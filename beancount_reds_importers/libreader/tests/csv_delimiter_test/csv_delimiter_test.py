#!/usr/bin/env python3

from os import path

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking
from beancount_reds_importers.util import regression_pytest as regtest


class Importer(banking.Importer, csvreader.Importer):
    IMPORTER_NAME = "CSVSemicolon"

    def custom_init(self):
        if not self.custom_init_run:
            self.csv_delimiter = ";"
            self.filename_pattern_def = ".*csv"
            self.header_identifier = "Semicolon Delimited CSV"
            self.column_labels_line = "date;description;payee;amount;memo"
            self.date_format = "%Y/%m/%d"
            self.header_map = {}
            self.transaction_type_map = {}
            self.skip_transaction_types = []
            self.custom_init_run = True


@regtest.with_importer(
    Importer(
        {
            "account_number": "acctid",
            "main_account": "Assets:Bank",
            "currency": "$",
            "emit_filing_account_metadata": False,
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestSmart(regtest.ImporterTestBase):
    pass
