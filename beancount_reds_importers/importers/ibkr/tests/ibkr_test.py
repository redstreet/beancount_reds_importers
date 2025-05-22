"""
Tests for the IBKR importer.
"""

from os import path

from beancount_reds_importers.importers import ibkr
from beancount_reds_importers.util import regression_pytest as regtest

DIR = path.dirname(__file__)

fund_info = {
    "fund_data": [
        ("OPI", "US67623C1099", "Office Properties Income Trust"),
    ],
    "money_market": [],
}


@regtest.with_importer(
    ibkr.Importer(
        {
            "filename_pattern": "*.xml",
            "emit_filing_account_metadata": False,

            "account_number": "U1110000",
            "main_account": "Assets:Investments:IB:Stocks-{currency}:{ticker}",
            "fund_info": fund_info,
            "dividends": "Income:Investment:Dividends:IB:{ticker}",
            "cash_account": "Assets:Investments:IB:Cash-{currency}",
            "capgainsd_lt": "Account to book long term capital gains distributions to",
            "capgainsd_st": "Account to book short term capital gains distributions to",
            "interest": "Income:Investment:Interest:IB:{ticker}",
            "fees": "Account to book fees to",
            "whtax": "Expenses:Tax:WithholdingTax:{currency}",
        }
    )
)
@regtest.with_testdir(DIR)
class TestIbkr(regtest.ImporterTestBase):
    """
    Tests for the IBKR importer.
    """

    # assert False
