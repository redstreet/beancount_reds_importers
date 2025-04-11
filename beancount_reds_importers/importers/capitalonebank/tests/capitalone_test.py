from os import path

from beancount_reds_importers.importers import capitalonebank
from beancount_reds_importers.util import regression_pytest as regtest


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
