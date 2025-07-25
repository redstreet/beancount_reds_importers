"""Fidelity Brokerage csv importer for beancount."""

import re

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, csvreader.Importer):
    IMPORTER_NAME = "Fidelity Cash Management Account"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = ".*History"
        self.date_format = "%m/%d/%Y"
        self.header_identifier = ""
        self.column_labels_line = "Run Date,Action,Symbol,Description,Type,Quantity,Price ($),Commission ($),Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date"
        self.header_map = {
            "Run Date": "date",
            "Action": "memo",
            "Symbol": "security",
            "Amount ($)": "amount",
            "Settlement Date": "settleDate",
            "Quantity": "units",
            "Accrued Interest ($)": "accrued_interest",
            "Fees ($)": "fees",
            "Commission ($)": "commission",
            "Cash Balance ($)": "balance",
            "Price ($)": "unit_price",
        }
        self.transaction_type_map = {
            "DIVIDEND RECEIVED": "dividends",
            "TRANSFERRED FROM": "cash",
            "YOU BOUGHT": "buystock",
            "YOU SOLD": "sellstock",
        }
        self.skip_transaction_types = []
        # fmt: on

    def deep_identify(self, file):
        last_four = self.config.get("account_number", "")[-4:]
        header = ""
        with open(file, "r", encoding="utf-8") as f:
            header = f.read(200)
        return re.match(self.header_identifier, header, flags=re.DOTALL) and f"{last_four}" in file

    def prepare_table(self, rdr):
        for field in ["Action", "Symbol", "Description"]:
            rdr = rdr.convert(field, lambda x: x.lstrip())

        rdr = rdr.addfield("total", lambda x: x["Amount ($)"])
        rdr = rdr.addfield("tradeDate", lambda x: x["Run Date"])
        rdr = rdr.cutout("Type")
        rdr = rdr.capture("Action", "(\\S+(?:\\s+\\S+)?)", ["type"], include_original=True)

        # for field in ["memo"]:
        #     rdr = rdr.convert(field, lambda x: x.lstrip())

        return rdr
