"""Questrade Brokerage xlsx importer."""

import re
from decimal import Decimal

from beancount_reds_importers.libreader import xlsxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, xlsxreader.Importer):
    IMPORTER_NAME = "Questrade Brokerage XLSX"
    FILE_EXT = "xlsx"

    def custom_init(self):
        self.max_rounding_error = 0.009
        self.filename_pattern_def = "Activities.*"
        self.header_identifier = "Transaction Date"
        self.date_format = "%Y-%m-%d %I:%M:%S %p"
        self.get_ticker_info = self.get_ticker_info_from_id
        self.funds_db_txt = "funds_by_id"
        self.header_map = {
            "Transaction Date": "tradeDate",
            "Settlement Date": "settleDate",
            # Will look at self.transaction_type_map to find out
            # which actions it is.
            "Action": "type",
            "Symbol": "security",
            "Description": "memo",
            "Quantity": "units",
            "Price": "unit_price",
            "Gross Amount": "amount",
            "Commission": "commission",
            "Net Amount": "total",
            "Currency": "currency",
        }
        self.transaction_type_map = {
            "Deposits": "cash",
            "Transfer": "xfer",
            # Contributions to registered account
            "CON": "cash",
            # Deposits to non-registered accoun
            "DEP": "cash",
            "Buy": "buystock",
            "Sell": "sellstock",
            # BRW seems quite generic, I've seen it when transferring in from
            # another broker or when journaling shares
            "BRW": "transfer",
            "TFI": "transfer",
            "Dividends": "dividends",
        }
        self.skip_transaction_types = []

    def file_date(self, file):
        self.initialize(file)
        self.read_file(file)
        return max(ot.tradeDate for ot in self.get_transactions()).date()

    def convert_activity_type(self, value, row):
        """
        Convert a row to an activity type. Most of actions are described in the
        "Action" column by an explicit keyword like "Buy", "Sell", etc. But the
        column might be empty and in that case, the action is described in the
        "Activity Type" column, like for "Dividends". Here is a table with a
        few transactions that can be found in the report.

        Transaction Type | Action Column Value | Activity Type
        -----------------+---------------------+--------------
        dividends        | "None"              | "Dividends"
        buy stock        | "Buy"               | "Trades"
        sell stock       | "Sell"              | "Trades"
        generic brw      | "BRW"               | "Others"

        BRW is generic and looking into the "Description" field will probably
        be needed to support all types of transactions.
        """
        if not (row["Action"] == "None" or row["Action"] == ""):
            if row["Action"] == "CON":
                # CON is quite generically a cash movement on an account
                # If the description is like "CON 123456789 TO 987654321", then
                # its a transfer between account.
                # Else, check Activity Type to check if it's an actual deposit
                # or a withdrawal.
                if re.search(r"CON \d+ TO \d+", row["Description"]):
                    return "Transfer"
                elif row["Activity Type"] == "Deposits":
                    return "CON"
                elif row["Activity Type"] == "Withdrawals":
                    raise Exception("'Withdrawals' not supported yet")

            return row["Action"]
        elif row["Activity Type"] != "None":
            return row["Activity Type"]
        else:
            raise Exception(f"Both 'Action' and 'Activity Type' are empty in row {row}")

    def convert_symbol(self, ticker):
        """
        Convert a ticker to a more canonical name. Tickers' symbols don't seem
        very consistent, sometimes they are reported as XEQT or XEQT.TO. When
        journaling DRL.U.TO to DLR.TO, both transactions showed as "DLR"
        symbol. CASH sometimes appears as .CASH, CASH, or CASH.TO. This is best
        effort to try to have consistent naming.
        """
        if ticker is not None:
            if ticker.startswith("."):
                # Sometimes, ETF is called ".CASH", normalize to "CASH"
                ticker = ticker[1:]

            if "." in ticker:
                # normalize "CASH.TO" to "CASH"
                ticker = ticker.split(".")[0]

        return ticker

    def adjust_gross_amount(self, value, row):
        """
        For Deposits and Contributions, "Gross Amount" is 0, "Net Amount" is
        the amount contributed/deposited to the account.
        For other transactions, like buying and selling stock, both "Gross
        Amount" and "Net Amount" fields are populated.
        """
        if row["Action"] in ["CON", "DEP"]:
            return row["Net Amount"]
        return value

    def convert_commission(self, value):
        """
        Commission are posted as negative values, but they need to be positive
        values to make sense in beancount's world, so discard the minus sign
        and convert them to Decimal.
        """
        if value.startswith("-"):
            return Decimal(value[1:])
        return Decimal(value)

    def prepare_table(self, rdr):
        rdr = rdr.convert("Symbol", self.convert_symbol)

        rdr = rdr.convert("Gross Amount", self.adjust_gross_amount, pass_row=True)

        rdr = rdr.convert("Action", self.convert_activity_type, pass_row=True)

        rdr = rdr.convert("Commission", self.convert_commission)

        # Make this importer Multiplexer compatible by filtering by relevant account number
        rdr = rdr.select(lambda rec: rec["Account #"] == self.config["account_number"])

        rdr = rdr.cutout("Account #")
        rdr = rdr.cutout("Account Type")

        return rdr
