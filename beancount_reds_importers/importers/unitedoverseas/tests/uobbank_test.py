from os import path

from beancount_reds_importers.importers.unitedoverseas import uobbank
from beancount_reds_importers.util import regression_pytest as regtest


@regtest.with_importer(
    uobbank.Importer(
        {
            "main_account": "Assets:Banks:UOB:UNIPLUS",
            "account_number": "1234567890",
            "currency": "SGD",
            "rounding_error": "Equity:Rounding-Errors:Imports",
            "emit_filing_account_metadata": False,
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestUOB(regtest.ImporterTestBase):
    pass
