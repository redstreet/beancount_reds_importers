from os import path

from beangulp import regression_pytest as regtest

from beancount_reds_importers.importers import ally


@regtest.with_importer(
    ally.Importer(
        {
            "account_number": "23456",
            "main_account": "Assets:Banks:Checking",
            "emit_filing_account_metadata": False,
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestAlly(regtest.ImporterTestBase):
    pass
