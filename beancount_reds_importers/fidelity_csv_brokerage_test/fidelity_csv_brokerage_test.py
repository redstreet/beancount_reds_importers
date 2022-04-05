"""Fidelity CSV importer test for Brokerage account"""

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
        ("DNA", "37611X100", "Ginkgo Bioworks Holdings, Inc."),
        ("CUSIPG8354H126", "G8354H126", "Soaring Eagle Acq Corp"),
        ("FZIPX", "315911636", "Fidelity ZERO Extended Market Index Fund"),
    ],
    "money_market": ["FZFXX", "SPAXX"],
}

transfer_info = {
    "transfer_accounts": [
        (
            "C_SCHLAB DEPTRIALCREDT",
            "Income:Misc:BankValidation",
            fidelity_csv.Importer.TransferDedupeStyle.COMMENT_NO_TRANSACTIONS,
        ),
        (
            "Sphere Inc * Cashew App",
            "Assets:US:SphereCashewApp",
            fidelity_csv.Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS,
        ),
        (
            "X11111111",
            "Assets:US:Fidelity:Checking",
            fidelity_csv.Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS,
        ),
        (
            "SCHLAB BANK P2P  JANE DOE",
            "Assets:Schlab:Checking",
            fidelity_csv.Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS,
        ),
    ],
}

IMPORTER = fidelity_csv.Importer(
    {
        "currency": "USD",
        "account_number": "X99999999",
        "transfer": "Assets:TODOTransfer",
        "transfer_info": transfer_info,
        "fund_info": fund_info,
        "main_account": "Assets:Fidelity:Brokerage",
        "cash_account": "Assets:Fidelity:Brokerage:Cash",
        "dividends": "Income:Fidelity:Brokerage:Dividends",
        "capgains_lt": "Income:Fidelity:Brokerage:Capgainslt",
        "capgains_st": "Income:Fidelity:Brokerage:Capgainsst",
        "interest": "Income:Fidelity:Brokerage:Interest",
        "cusip_symbol_prepend": "CUSIP",
        "fees": "Expenses:Investing:TradeCommissions",
        "rounding_error": "Equity:Fidelity:Brokerage:RoundingError",
        # "income_elan_fidelityrewards_cashback": 'Income:Misc:CreditCard:CashBackReward',
    }
)


@regtest.with_importer(IMPORTER)
@regtest.with_testdir(path.dirname(__file__))
class TestImporter(regtest.ImporterTestBase):
    pass


if __name__ == "__main__":
    unittest.main()
