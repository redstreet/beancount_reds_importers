"""Fidelity CSV importer test for HSA account"""

import unittest
import sys
from os import path

sys.path.insert(0, path.join(path.dirname(path.dirname(path.realpath(__file__)))))

from beancount.ingest import regression_pytest as regtest
import fidelity_csv

fund_info = {
    "fund_data": [
        ("FZFXX", "316341304", "Fidelity Treasury Money Market Fund"),
        ("SPAXX", "31617H102", "Fidelity Government Money Market Fund"),
    ],
    "money_market": ["FZFXX", "SPAXX"],
}

transfer_info = {
    "transfer_accounts": [
        (
            "X11111111",
            "Assets:US:Fidelity:Checking",
            fidelity_csv.Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS,
        ),
    ],
}

IMPORTER = fidelity_csv.Importer(
    {
        "currency": "USD",
        "account_number": "222222222",
        "transfer": "Assets:TODOTransfer",
        "transfer_info": transfer_info,
        "fund_info": fund_info,
        "main_account": "Assets:Fidelity:HSA",
        "cash_account": "Assets:Fidelity:HSA:Cash",
        "dividends": "Income:Fidelity:HSA:Dividends",
        "capgains_lt": "Income:Fidelity:HSA:Capgainslt",
        "capgains_st": "Income:Fidelity:HSA:Capgainsst",
        "interest": "Income:Fidelity:HSA:Interest",
        "cusip_symbol_prepend": "CUSIP",
        "fees": "Expenses:Investing:TradeCommissions",
        "rounding_error": "Equity:Fidelity:HSA:RoundingError",
    }
)


@regtest.with_importer(IMPORTER)
@regtest.with_testdir(path.dirname(__file__))
class TestImporter(regtest.ImporterTestBase):
    pass


if __name__ == "__main__":
    unittest.main()
