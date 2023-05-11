# flake8: noqa

from os import path
from beancount.ingest import regression_pytest as regtest
from beancount_reds_importers.importers.schwab import schwab_csv_checking

@regtest.with_importer(
    schwab_csv_checking.Importer(
        {
            'account_number'  : '1234',
            'main_account'    : 'Assets:Banks:Schwab',
            'currency'        : 'USD',
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestSchwabCSV(regtest.ImporterTestBase):
    pass
