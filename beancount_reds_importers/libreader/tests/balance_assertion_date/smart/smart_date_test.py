from os import path

from beancount_reds_importers.importers import ally
from beancount_reds_importers.util import regression_pytest as regtest


# default balance_assertion_date_type is "smart"
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
class TestSmart(regtest.ImporterTestBase):
    pass
