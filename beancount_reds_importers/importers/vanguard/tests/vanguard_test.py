from os import path
from beancount.ingest import regression_pytest as regtest
from beancount_reds_importers.importers import vanguard


@regtest.with_importer(
    vanguard.Importer(
        {
            "account_number": "444555",
            "main_account": "Assets:Vanguard:401k:{source401k}:{ticker}",
            "cash_account": "Assets:Vanguard:401k:Cash",
            "dividends": "Income:Dividends:Vanguard:401k:{source401k}:{ticker}",
            "interest": "Income:Interest:Vanguard:401k:{source401k}:{ticker}",
            "cg": "Income:CapitalGains:401k:{source401k}:{ticker}",
            "capgainsd_lt": "Income:CapitalGains:Long:Vanguard:401k:{source401k}:{ticker}",
            "capgainsd_st": "Income:CapitalGains:Short:Vanguard:401k:{source401k}:{ticker}",
            "fees": "Expenses:Fees:Vanguard:401k",
            "invexpense": "Expenses:Expenses:Vanguard:401k",
            "rounding_error": "Equity:Rounding-Errors:Imports",
            "fund_info": {
                "fund_data": [
                    # https://investor.vanguard.com/mutual-funds/profile/pe/overview/7743
                    ("V7743", "VGI007743", "Vanguard Target Retirement 2050 Trust"),
                ],
                "money_market": ["VMFXX"],
            },
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestVanguard401k(regtest.ImporterTestBase):
    pass
