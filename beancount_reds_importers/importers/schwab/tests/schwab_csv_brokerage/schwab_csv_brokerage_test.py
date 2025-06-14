# flake8: noqa

from os import path

from beancount_reds_importers.importers.schwab import schwab_csv_brokerage
from beancount_reds_importers.util import regression_pytest as regtest

fund_data = [
    ("SWVXX", "123", "SCHWAB VALUE ADVANTAGE MONEY INV"),
    ("GIS", "456", "GENERAL MILLS INC"),
    ("BND", "789", "Vanguard Total Bond Market Index Fund"),
]

# list of money_market accounts. These will not be held at cost, and instead will use price conversions
money_market = ["VMFXX"]

fund_info = {
    "fund_data": fund_data,
    "money_market": money_market,
}


def build_config():
    acct = "Assets:Investments:Schwab"
    root = "Investments"
    taxability = "Taxable"
    leaf = "Schwab"
    currency = "USD"
    config = {
        "account_number": "9876",
        "main_account": acct + ":{ticker}",
        "cash_account": f"{acct}:{currency}",
        "transfer": "Assets:Zero-Sum-Accounts:Transfers:Bank-Account",
        "dividends": f"Income:{root}:{taxability}:Dividends:{leaf}:{{ticker}}",
        "interest": f"Income:{root}:{taxability}:Interest:{leaf}:{{ticker}}",
        "cg": f"Income:{root}:{taxability}:Capital-Gains:{leaf}:{{ticker}}",
        "capgainsd_lt": f"Income:{root}:{taxability}:Capital-Gains-Distributions:Long:{leaf}:{{ticker}}",
        "capgainsd_st": f"Income:{root}:{taxability}:Capital-Gains-Distributions:Short:{leaf}:{{ticker}}",
        "fees": f"Expenses:Fees-and-Charges:Brokerage-Fees:{taxability}:{leaf}",
        "invexpense": f"Expenses:Expenses:Investment-Expenses:{taxability}:{leaf}",
        "rounding_error": "Equity:Rounding-Errors:Imports",
        "fund_info": fund_info,
        "currency": currency,
        "emit_filing_account_metadata": False,
    }
    return config


@regtest.with_importer(schwab_csv_brokerage.Importer(build_config()))
@regtest.with_testdir(path.dirname(__file__))
class TestSchwabBrokerage(regtest.ImporterTestBase):
    pass
