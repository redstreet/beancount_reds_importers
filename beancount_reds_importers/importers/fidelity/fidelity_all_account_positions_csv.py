"""Fidelity positions csv importer."""

import datetime
import math
import re
from decimal import Decimal

from beancount.core.number import D

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, csvreader.Importer):
    IMPORTER_NAME = "Fidelity Positions CSV"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.file_encoding = "utf-8-sig"
        self.filename_pattern_def = "Portfolio_Positions_.*.csv"
        self.header_identifier = (
            "^Account Number,Account Name,Symbol,Description,Quantity.*"
        )
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = "%b-%d-%Y"
        self.funds_db_txt = "funds_by_ticker"
        self.fix_muni_shares = True  # see prepare_raw_file, fidelity reports 100x share values for muni bonds
        self.column_labels_line = "Account Number,Account Name,Symbol,Description,Quantity,Last Price,Last Price Change,Current Value,Today's Gain/Loss Dollar,Today's Gain/Loss Percent,Total Gain/Loss Dollar,Total Gain/Loss Percent,Percent Of Account,Cost Basis Total,Average Cost Basis,Type"
        # fmt: off
        self.header_map = {
            "Description": "memo",
            "Symbol": "security",
            "date": "date",
            "Quantity": "units",
            "Last Price": "unit_price",
            "Account Number": "account_number",
            "Current Value": "balance",
        }
        # fmt: on
        self.skip_transaction_types = []
        self.security_symbol_map = {
            # if you have securities where you use a custom symbol
            # instead of the one to be found in the CSV, example would
            # be singhle letter symbols which cannot be a bc commodity name
            "M": "M-M",
            "V": "V-V",
            "T": "T-T",
            "C": "C-C",
            "F": "F-F",
            "G": "G-G",
            "K": "K-K",
            "A": "A-A",
        }

    def convert_columns(self, rdr):
        # fixup decimals
        decimals = ["units"]
        for i in decimals:
            rdr = rdr.convert(i, D)

        # fixup currencies
        def remove_non_numeric(x):
            return re.sub(r"[^0-9\.]", "", x)  # noqa: W605

        currencies = ["unit_price", "balance"]
        for i in currencies:
            rdr = rdr.convert(i, remove_non_numeric)
            rdr = rdr.convert(i, D)

        return rdr

    def file_date(self, file):
        self.read_file(file)
        return self.date.date()

    def get_max_transaction_date(self):
        return self.date.date()

    def prepare_raw_file(self, rdr):
        for r in rdr.data():
            # looking for row with date
            # Date downloaded Dec-05-2025 at 1:02 p.m ET
            if len(r) >= 1:
                pattern = re.compile(
                    r"Date downloaded ((?i:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}-\d{4})"
                )
                match = pattern.search(r[0])
                if match:
                    self.date = datetime.datetime.strptime(
                        match.group(1), self.date_format
                    )

        # add date to each record
        rdr = rdr.addfields([("date", self.date)])

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
            if None in [quantity, row["Last Price"], row["Current Value"]] or "" in [
                quantity,
                row["Last Price"],
                row["Current Value"],
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
                    numeric_value = re.sub(r"[^0-9\.]", "", row["Current Value"])
                    numeric_price = re.sub(r"[^0-9\.]", "", row["Last Price"])
                    inferred_price = round(
                        abs(float(numeric_value)) / abs(float(quantity)), 4
                    )

                    if float(numeric_price) / inferred_price > 90:
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
            if '.' not in value:
                return value + ".00"

            return value

        rdr = rdr.convert("Symbol", cusip_to_symbols)
        rdr = rdr.convert("Symbol", map_symbols)
        if getattr(self, "fix_muni_shares", False):
            rdr = rdr.convert("Quantity", adjust_muni_share_count, pass_row=True)

        for f in ["Last Price", "Quantity"]:
            rdr = rdr.convert(f, add_precision)

        return rdr

    def get_transactions(self):
        """No transactions, this is a file with positions and prices only"""
        return []

    def prepare_table(self, rdr):
        # Delete uninteresting columns
        rdr = rdr.cut(list(self.header_map.keys()))
        return rdr

    def get_balance_positions(self):
        for pos in self.rdr.namedtuples():
            if pos.account_number == self.config["account_number"]:
                if pos.security not in ["Pending activity"]:  # unsettled transactions
                    if not pos.security.endswith(
                        "**"
                    ):  # these are core (cash) accounts
                        yield pos

    def get_available_cash(self, settlement_fund_balance):
        core_acct_balance = Decimal()
        for pos in self.rdr.namedtuples():
            if pos.account_number == self.config["account_number"]:
                if pos.security.endswith("**"):  # these are core (cash) accounts
                    core_acct_balance = pos.balance

        return core_acct_balance
