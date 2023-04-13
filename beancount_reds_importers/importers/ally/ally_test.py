from os import path
from beancount.ingest import regression_pytest as regtest
from beancount_reds_importers.importers import ally


@regtest.with_importer(
    ally.Importer(
        {
            "account_number": "23456",
            "main_account": "Assets:Banks:Checking",
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestAlly(regtest.ImporterTestBase):
    pass
