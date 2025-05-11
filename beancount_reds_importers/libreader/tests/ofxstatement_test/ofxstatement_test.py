#!/usr/bin/env python3

"""N26 Bank (Checking, Savings accounts) ofx importer for beancount."""

from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(banking.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'N26'

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_pattern_def = '.*n26'
            self.custom_init_run = True

from os import path

from beancount.ingest import regression_pytest as regtest


@regtest.with_importer(
    Importer(
        {
        'account_number'  : 'acctid',
        'main_account'    : 'Assets:Banks:Checking:N26',
        "emit_filing_account_metadata": False,
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestSmart(regtest.ImporterTestBase):
    pass
