from os import path

from beangulp import regression_pytest as regtest

from beancount_reds_importers.importers import capitalonebank


@regtest.with_importer(
    capitalonebank.Importer(
        {
            "account_number": "9876",
            "main_account": "Assets:Banks:CapitalOne",
            "emit_filing_account_metadata": False,
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestCapitalOne(regtest.ImporterTestBase):
    pass
