"""Small real-institution configuration used by installed-package checks."""

import beangulp

from beancount_reds_importers.importers.schwab import (
    schwab_csv_brokerage,
    schwab_csv_checking,
)

CONFIG = [
    schwab_csv_checking.Importer(
        {
            "account_number": "1234",
            "main_account": "Assets:Bank",
            "target_account": "Income:Interest",
            "currency": "USD",
            "emit_filing_account_metadata": False,
        }
    ),
    schwab_csv_brokerage.Importer(
        {
            "account_number": "5678",
            "main_account": "Assets:Broker:{ticker}",
            "cash_account": "Assets:Broker:{currency}",
            "currency": "USD",
            "transfer": "Assets:Transfers",
            "dividends": "Income:Dividends:{ticker}",
            "interest": "Income:Interest",
            "cg": "Income:Gains:{ticker}",
            "capgainsd_lt": "Income:Long:{ticker}",
            "capgainsd_st": "Income:Short:{ticker}",
            "fees": "Expenses:Fees",
            "rounding_error": "Equity:Rounding",
            "emit_filing_account_metadata": False,
            "fund_info": {"money_market": [], "fund_data": [("ABC", "US123", "Example Fund")]},
        }
    ),
]

if __name__ == "__main__":
    beangulp.Ingest(CONFIG)()
