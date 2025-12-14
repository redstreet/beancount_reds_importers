"""Fidelity All Accounts .csv importer."""

import math
import re
from datetime import datetime

from beangulp import cache

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments

# from beangulp import cache


class Importer(csvreader.Importer, investments.Importer):
    IMPORTER_NAME = "Fidelity All Accounts CSV"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.file_encoding = "utf-8-sig"
        self.filename_pattern_def = "Accounts_History.*"
        self.header_identifier = "^Run Date,Account,Account Number,Action,Symbol.*"
        self.column_labels_line = "Run Date,Account,Account Number,Action,Symbol,Description,Type,Exchange Quantity,Exchange Currency,Currency,Price,Quantity,Exchange Rate,Commission,Fees,Accrued Interest,Amount,Settlement Date"
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = "%m/%d/%Y"
        self.funds_db_txt = "funds_by_ticker"
        self.currency = self.config.get("currency", None)
        self.use_inferred_price = self.config.get(
            # calculate price to 4 decimal places rather than using csv price
            "use_inferred_price",
            False,
        )
        self.fix_muni_shares = self.config.get(
            # see prepare_table, fidelity reports 100x share values for muni bonds
            "fix_muni_shares",
            False,
        )
        self.actions_to_treat_as_cash = self.config.get(
            # these are deposit sweep funds, just treat them as cash...will have
            # a huge variety of symbols, some with impossible to find CUSIP
            "actions_to_treat_as_cash",
            tuple(),
        )
        self.actions_to_treat_as_cash_reinvestment = self.config.get(
            # similar to actions_to_treat_as_cash, some of these deposit sweep funds
            # will reinvest interest payments...the above treats the earned interest
            # as cash, will ignore the reinvestment transaction
            "actions_to_treat_as_cash_reinvestment",
            [],
        )
        self.security_symbol_map = self.config.get(
            # if you have securities where you use a custom symbol
            # instead of the one to be found in the CSV, example would
            # be singhle letter symbols which cannot be a bc commodity name
            "security_symbol_map",
            dict(),
        )
        self.add_precision = self.config.get("add_precision", False)  # add some decimal precision to quantity and value fields if none is present
        # fmt: off
        self.header_map = {
            "Account Number": "account_number",
            "Run Date": "date",
            "Action": "memo",
            "Symbol": "security",
            "Quantity": "units",
            "Accrued Interest": "accrued_interest",
            "Amount": "amount",
            "Settlement Date": "settleDate",
            "Fees": "fees",
            "Commission": "commission",
        }
        if self.use_inferred_price:
            self.header_map["inferred_price"] = "unit_price"
        else:
            self.header_map["Price"] = "unit_price"
        self.transaction_type_map = {
            "REINVESTMENT": "buymf",
            "REDEMPTION FROM": "sellmf",
            "DIVIDEND RECEIVED": "dividends",
            "DIVIDENDS": "dividends",
            "TRANSFERRED FROM": "cash",
            "YOU BOUGHT": "buystock",
            "YOU SOLD": "sellstock",
            "REDEMPTION PAYOUT": "sellother",
            "DIRECT DEPOSIT": "dep",
            "TRANSFERRED TO": "xfer",
            "MUNI EXEMPT": "income",
            "INTEREST EARNED": "income",
            "FEE CHARGED": "fee",
            "ADVISOR FEE": "fee",
            "FOREIGN TAX": "fee",
            "ADJ FOREIGN": "fee",
            "BUY CANCEL": "fee",  # longer text here is BUY CANCEL TAX PAID as of May-05-2025...
            "DIVIDEND ADJUSTMENT": "fee",  # longer text here is FOREIGN TAX PAID as of May-05-2025...
            "BILL PAYMENT": "payment",
            "DEBIT CARD": "payment",
            "Check Paid": "payment",
            "DIRECT DEBIT": "payment",
            "Electronic Funds": "payment",
            "CHECK RECEIVED": "dep",
            "CASH ADVANCE": "debit",
            "SHORT-TERM CAP": "capgainsd_st",
            "LONG-TERM CAP": "capgainsd_lt",
            "PARTIC CONTR": "dep",
            "WIRE TRANSFER": "dep",
            "CONTRIBUTED TO": "sellstock",
            "IN LIEU": "dep",
            "CASH CONTRIBUTION": "dep",
            "ROLLOVER CASH": "dep",
            "TRANSFER OF": "dep",
            "PART CONTRIB": "dep",
            "ROLLOVER SHARES": "buystock",  # rollover from closed account...almost certainly needs to be edited manually
            "CONVERSION as": "buymf",  # conversion of mutual fund class...almost certainly needs to be edited manually
            "EXCHANGE OUT": "sellmf",
            "EXCHANGE IN": "buymf",
            "CHANGE ON": "capgainsd_lt",
            "WITHDRAWAL": "sellmf",
        }
        self.skip_transaction_types = []
        # fmt: on

    def get_max_transaction_date(self):
        try:
            # NOTE: this is the same as the code in csvreader.py, but the exception does not
            # generate an error...for the fidelity csv transaction file there are no balance
            # assertions, so not being able to generate them is not an error.  This will occur for any
            # account in the import file that has no transactions

            date = max(
                ot.tradeDate if hasattr(ot, "tradeDate") else ot.date
                for ot in self.get_transactions()
            ).date()
        except Exception as err:
            date = datetime.today().date()

        return date

    def deep_identify(self, file):
        return re.search(self.header_identifier, cache.get_file(file).head(), flags=re.MULTILINE)

    def skip_transaction(self, ot):
        if ot.account_number != self.config["account_number"]:
            return True
        if ot.type in ["MERGER MER", "ADJUST FEE", "DISTRIBUTION", "JOURNALED JNL"]:
            # this sort of transaction must be handled manually
            # ADJUST FEE sounds like a fee, but has been used for a 1:1 reorg
            # DISTRIBUTION is for splits
            return True

        return False

    def prepare_table(self, rdr):
        if "" in rdr.fieldnames():
            rdr = rdr.cutout("")  # clean up last column

        def cusip_to_symbols(s):
            """
            Stocks and mutual funds are represented by their
            symbol, but bonds and core account funds (some?) use
            their cusip, try to convert these to symbol if they
            are present in fund_data
            """
            return self.funds_by_id.get(s, (s,))[0]

        def map_symbols(s):
            """
            Stocks and mutual funds are represented by their
            symbol, but bonds and core account funds (some?) use
            their cusip, try to convert these to symbol if they
            are present in fund_data
            """
            return self.security_symbol_map.get(s, s)

        def adjust_muni_share_count(quantity, row):
            """
            Fidelity reports muni shares as 100x the actual value
            By their own numbers shares * price = 100 x cost
            try to identify this and adjust by dividing by 100
            """

            # if quantity is None or row["Price"] is None or row["Amount"] is None:
            if None in [quantity, row["Price"], row["Amount"]] or "" in [
                quantity,
                row["Price"],
                row["Amount"],
            ]:
                # if quantity or price is not set there is nothing to fix here
                return quantity
            else:
                # see if price seems to be 100x an inferred price which indicates
                # the muni share problem
                if not math.isclose(
                    float(quantity),
                    0,
                    rel_tol=1e-09,
                    abs_tol=1e-09,
                ):
                    inferred_price = (
                        round(
                            (abs(float(row["Amount"])) - float(row["Accrued Interest"]))
                            / abs(float(quantity)),
                            4,
                        )
                        if row["Accrued Interest"]
                        else round(abs(float(row["Amount"])) / abs(float(quantity)), 4)
                    )

                    if float(row["Price"]) / inferred_price > 90:
                        # the provided prices is ~100x the calculated price
                        # This happens when muni bond shares are reported 100x too high
                        return str(round(float(quantity) / 100))
                    else:
                        # calculated price is about equal to provided one, no muni bond problem
                        return quantity
                else:
                    return quantity

        def add_precision(value):
            # add decimal places if none are present because
            # beancount treats values with no decimal places
            # as infinitely precise
            if "." not in value:
                return value + ".00"

            return value

        rdr = rdr.convert("Symbol", cusip_to_symbols)
        rdr = rdr.convert("Symbol", map_symbols)
        if self.fix_muni_shares:
            rdr = rdr.convert("Quantity", adjust_muni_share_count, pass_row=True)

        # add an inferred price column b/c csv prices are only to two decimals
        rdr = rdr.addfield(
            "inferred_price",
            lambda row: str(
                round(
                    (abs(float(row["Amount"])) - float(row["Accrued Interest"]))
                    / abs(float(row["Quantity"])),
                    4,
                )
                if row["Accrued Interest"]
                else round(abs(float(row["Amount"])) / abs(float(row["Quantity"])), 4)
            )
            if not math.isclose(
                float(row["Quantity"]),
                0,
                rel_tol=1e-09,
                abs_tol=1e-09,
            )
            else "",
        )

        rdr = rdr.convert(
            "Symbol",
            "",
            where=lambda r: r.Action.startswith(self.actions_to_treat_as_cash),
        )
        rdr = rdr.selectnotin("Action", self.actions_to_treat_as_cash_reinvestment)
        rdr = rdr.addfield("total", lambda x: x["Amount"])
        rdr = rdr.addfield("tradeDate", lambda x: x["Run Date"])
        if self.add_precision:
            for f in ["Amount", "Quantity", "total"]:
                rdr = rdr.convert(f, add_precision)
        # the REINVESTMENT action will include a fund symbol as the 2nd word,
        # so only use the first word for mapping
        # DISTRIBUTION which is used for splits will also include a symbol as
        # 2nd word
        rdr = rdr.capture(
            "Action",
            "(DISTRIBUTION|REINVESTMENT|\\S+(?:\\s+\\S+)?)",
            ["type"],
            include_original=True,
        )

        return rdr
