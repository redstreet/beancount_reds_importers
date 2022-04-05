"""Fidelity CSV importer test for checking account"""

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
        ("QPCTQ", "", "CITIBANK NOT CO"),
        ("QHMBQ", "", "DISCOVER BANK N"),
        ("QPIFQ", "", "TRUIST BANK NOT"),
    ],
    "money_market": ["FZFXX", "SPAXX", "QPCTQ", "QHMBQ", "QPIFQ"],
}

transfer_info = {
    "transfer_accounts": [
        (
            "X99999999",
            "Assets:US:Fidelity:Brokerage",
            fidelity_csv.Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS,
        ),
        (
            "222222222",
            "Assets:US:Fidelity:HSA",
            fidelity_csv.Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS,
        ),
    ],
}

IMPORTER = fidelity_csv.Importer(
    {
        "currency": "USD",
        "account_number": "X11111111",
        "transfer": "Assets:TODOTransfer",
        "transfer_info": transfer_info,
        "fund_info": fund_info,
        "main_account": "Assets:Fidelity:Checking",
        "cash_account": "Assets:Fidelity:Checking",
        "dividends": "Income:Fidelity:Checking:Dividends",
        "capgains_lt": "Income:Fidelity:Checking:Capgainslt",
        "capgains_st": "Income:Fidelity:Checking:Capgainsst",
        "interest": "Income:Fidelity:Checking:Interest",
        # "cusip_symbol_prepend": "CUSIP",
        "fees": "Expenses:Investing:TradeCommissions",
        "rounding_error": "Equity:Fidelity:Checking:RoundingError",
        "income_elan_fidelityrewards_cashback": "Income:Misc:CreditCard:CashBackReward",
    }
)


@regtest.with_importer(IMPORTER)
@regtest.with_testdir(path.dirname(__file__))
class TestImporter(regtest.ImporterTestBase):
    pass


if __name__ == "__main__":
    unittest.main()
