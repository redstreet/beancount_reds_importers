from os import path

from beancount_reds_importers.importers import multiplexer, questrade
from beancount_reds_importers.util import regression_pytest as regtest

fund_info = {
    "fund_data": [
        ("VBAL", "VBAL", "Vanguard Balanced ETF"),
        ("XBAL", "XBAL", "IShares Balanced ETF"),
        ("XEQT", "XEQT", "IShares Equity ETF"),
        ("VTI", "VTI", "Vanguard Total Stock Market"),
        ("VXUS", "VXUS", "Vanguard Total Stock Market Ex-US"),
        ("CASH", "CASH", "Global X High Interest Savings ETF"),
        ("DLR", "DLR", "GLOBAL X US DLR CURRENCY"),
        ("DLR.U", "G036247", "GLOBAL X US DLR CURRENCY"),
    ],
    "money_market": [],
}


@regtest.with_importer(
    multiplexer.Importer(
        {
            "importers": [
                questrade.Importer(
                    {
                        "account_number": "54637281",
                        "main_account": "Assets:Questrade:RRSP:{ticker}",
                        "cash_account": "Assets:Questrade:RRSP:Cash",
                        "transfer": "Assets:Zero-Sum-Accounts:Transfers-Questrade-RRSP",
                        "dividends": "Income:Dividends:Questrade:RRSP:{ticker}",
                        "interest": "Income:Interest:Questrade:RRSP:{ticker}",
                        "cg": "Income:CapitalGains:Questrade:RRSP:{ticker}",
                        "capgainsd_lt": "Income:CapitalGains:Long:Questrade:RRSP:{ticker}",
                        "capgainsd_st": "Income:CapitalGains:Short:Questrade:RRSP:{ticker}",
                        "fees": "Expenses:Fees:Questrade:RRSP",
                        "rounding_error": "Equity:Rounding-Errors:Imports",
                        "fund_info": fund_info,
                    }
                ),
                questrade.Importer(
                    {
                        "account_number": "12345678",
                        "main_account": "Assets:Questrade:FHSA:{ticker}",
                        "cash_account": "Assets:Questrade:FHSA:Cash",
                        "transfer": "Assets:Zero-Sum-Accounts:Transfers-Questrade-FHSA",
                        "dividends": "Income:Dividends:Questrade:FHSA:{ticker}",
                        "interest": "Income:Interest:Questrade:FHSA:{ticker}",
                        "cg": "Income:CapitalGains:Questrade:FHSA:{ticker}",
                        "capgainsd_lt": "Income:CapitalGains:Long:Questrade:FHSA:{ticker}",
                        "capgainsd_st": "Income:CapitalGains:Short:Questrade:FHSA:{ticker}",
                        "fees": "Expenses:Fees:Questrade:FHSA",
                        "rounding_error": "Equity:Rounding-Errors:Imports",
                        "fund_info": fund_info,
                    }
                ),
                questrade.Importer(
                    {
                        "account_number": "98765432",
                        "main_account": "Assets:Questrade:Taxable:{ticker}",
                        "cash_account": "Assets:Questrade:Taxable:Cash",
                        "transfer": "Assets:Zero-Sum-Accounts:Transfers-Questrade-Taxable",
                        "dividends": "Income:Dividends:Questrade:Taxable:{ticker}",
                        "interest": "Income:Interest:Questrade:Taxable:{ticker}",
                        "cg": "Income:CapitalGains:Questrade:Taxable:{ticker}",
                        "capgainsd_lt": "Income:CapitalGains:Long:Questrade:Taxable:{ticker}",
                        "capgainsd_st": "Income:CapitalGains:Short:Questrade:Taxable:{ticker}",
                        "fees": "Expenses:Fees:Questrade:Taxable",
                        "rounding_error": "Equity:Rounding-Errors:Imports",
                        "fund_info": fund_info,
                    }
                ),
            ],
        }
    ),
)
@regtest.with_testdir(path.dirname(__file__))
class TestQuestradeImporter(regtest.ImporterTestBase):
    pass
