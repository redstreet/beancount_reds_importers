#!/usr/bin/env python3

from os import path

from beangulp import regression_pytest as regtest

from beancount_reds_importers.importers import dcu


@regtest.with_importer(
    dcu.Importer(
        {
            "main_account": "Assets:Banks:DCU:Checking",
            "currency": "USD",
            "emit_filing_account_metadata": False,
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestDCUCSV(regtest.ImporterTestBase):
    pass
