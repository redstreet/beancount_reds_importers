from os import path
from beancount.ingest import regression_pytest as regtest
from beancount_reds_importers.importers import ally


@regtest.with_importer(
    ally.Importer({
        "account_number": "23456",
        "main_account": "Assets:Banks:Checking",
        "balance_assertion_date_type": "ofx_date",
    })
)
@regtest.with_testdir(path.dirname(__file__))
class TestSmart(regtest.ImporterTestBase):
    pass
