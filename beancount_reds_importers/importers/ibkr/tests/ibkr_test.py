"""
Tests for the IBKR importer.
"""

from os import path

import beangulp

from beancount_reds_importers.importers import ibkr
from beancount_reds_importers.util import regression_pytest as regtest

# Setup

fund_data = [
    ("OPI", "US67623C1099", ""),
]
money_market = ["VMFXX"]
fund_info = {
    "fund_data": fund_data,
    "money_market": money_market,
}

ibkr_importer = ibkr.Importer(
    {
        "filename_pattern": ".*.xml",
        "currency": "EUR",
        "emit_filing_account_metadata": False,
        "account_number": "A0001111",
        "main_account": "Assets:Investments:IB-{currency}:{ticker}",
        "cash_account": "Assets:Investments:IB-{currency}:Cash-{currency}",
        "transfer": "Assets:Transfers",
        # transfer account is optional. If left off no target posting will be created.
        # This allows for additional tools to handle this like smart importer.
        "dividends": "Income:Investment:Dividends:IB-{currency}:{ticker}",
        # "interest": "Income:Interest"
        "interest": "Income:Investment:Interest:IB-{currency}:{ticker}",
        # "cg": "Account to book capital gains/losses",
        "cg": "Income:Investment:Capital-Gains:IB-{currency}:{ticker}",
        "capgainsd_lt": "Equity:Capgains-Lt",
        "capgainsd_st": "Equity:Capgains-St",
        "fees": "Expenses:Fees",
        "invexpense": "Expenses:Investment-Expenses",
        "rounding_error": "Equity:Rounding-Errors",
        "whtax": "Expenses:Tax:WithholdingTax:IB-{currency}",
        "fund_info": fund_info,
    }
)

CONFIG = [
    ibkr_importer,
]

# Tests


@regtest.with_importer(ibkr_importer)
@regtest.with_testdir(path.dirname(__file__))
class TestIbkr(regtest.ImporterTestBase):
    """Tests for the IBKR importer."""


if __name__ == "__main__":
    ingest = beangulp.Ingest(CONFIG)
    ingest()
