from os import path
from beancount.ingest import regression_pytest as regtest
from beancount_reds_importers.importers.vanguard import vanguard_529


@regtest.with_importer(
    vanguard_529.Importer(
        {
            "account_number": "535672845-01",
            "main_account": "Assets:Vanguard:529:{ticker}",
            "cash_account": "Assets:Vanguard:529:Cash",
            "dividends": "Income:Dividends:Vanguard:529:{ticker}",
            "interest": "Income:Interest:Vanguard:529:{ticker}",
            "cg": "Income:CapitalGains:529:{ticker}",
            "capgainsd_lt": "Income:CapitalGains:Long:Vanguard:529:{ticker}",
            "capgainsd_st": "Income:CapitalGains:Short:Vanguard:529:{ticker}",
            "fees": "Expenses:Fees:Vanguard:529",
            "invexpense": "Expenses:Expenses:Vanguard:529",
            "rounding_error": "Equity:Rounding-Errors:Imports",
            "fund_info": {
                "fund_data": [
                     ('VTE2040', '00000000', 'Vanguard Target Enrollment 2040/2041 Portfolio'),
                ],
                "money_market": [],
            },
            "currency" : 'USD',
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestVanguard529(regtest.ImporterTestBase):
    pass
