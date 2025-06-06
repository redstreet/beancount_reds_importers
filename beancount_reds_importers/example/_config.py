#!/usr/bin/env python3
"""Import configuration."""

import sys
from os import path

import beangulp

sys.path.insert(0, path.join(path.dirname(__file__)))

from fund_info import fund_info

from beancount_reds_importers.importers import vanguard
from beancount_reds_importers.importers.schwab import schwab_csv_brokerage

# For a better solution for fund_info, see: https://reds-rants.netlify.app/personal-finance/tickers-and-identifiers/

# Setting this variable provides a list of importer instances.
CONFIG = [
    # Investments
    # --------------------------------------------------------------------------------------
    vanguard.Importer(
        {
            "account_number": "1234567",
            "main_account": "Assets:Investments:TradIRA:{ticker}",
            "cash_account": "Assets:Investments:TradIRA:{currency}",
            "transfer": "Assets:Zero-Sum-Accounts:Transfers:Bank-Account",
            "dividends": "Income:Dividends:TradIRA:{ticker}",
            "interest": "Income:Interest:TradIRA:{ticker}",
            "cg": "Income:Capital-Gains:TradIRA:{ticker}",
            "capgainsd_lt": "Income:Capital-Gains-Distributions:Long:TradIRA:{ticker}",
            "capgainsd_st": "Income:Capital-Gains-Distributions:Short:TradIRA:{ticker}",
            "fees": "Expenses:Brokerage-Fees:TradIRA",
            "invexpense": "Expenses:Brokerage-Expenses:TradIRA",
            "rounding_error": "Equity:Rounding-Errors:Imports",
            "fund_info": fund_info,
            # Not necessary as this is the default, but here for demo/documentation. 'filename_pattern'
            # is useful when your downloads have custom filenames to differentiate amongst accounts and
            # such
            "filename_pattern": "OfxDownload",
        }
    ),
    vanguard.Importer(
        {
            "main_account": "Assets:Investments:RothIRA:{ticker}",
            "cash_account": "Assets:Investments:RothIRA:{currency}",
            "account_number": "654321",
            "transfer": "Assets:Zero-Sum-Accounts:Transfers:Bank-Account",
            "dividends": "Income:Dividends:RothIRA:{ticker}",
            "interest": "Income:Interest:TradIRA:{ticker}",
            "cg": "Income:Capital-Gains:RothIRA:{ticker}",
            "capgainsd_lt": "Income:Capital-Gains-Distributions:Long:RothIRA:{ticker}",
            "capgainsd_st": "Income:Capital-Gains-Distributions:Short:RothIRA:{ticker}",
            "fees": "Expenses:Brokerage-Fees:RothIRA",
            "invexpense": "Expenses:Brokerage-Expenses:TradIRA",
            "rounding_error": "Equity:Rounding-Errors:Imports",
            "fund_info": fund_info,
        }
    ),
    schwab_csv_brokerage.Importer(
        {
            "main_account": "Assets:Investments:Schwab:{ticker}",
            # "main_account": "Assets:Investments:Schwab:{currency}",
            "account_number": "18181",
            "transfer": "Assets:Zero-Sum-Accounts:Transfers:Bank-Account",
            "dividends": "Income:Dividends:Schwab:{ticker}",
            "income": "Income:Interest:Schwab:{ticker}",
            "cg": "Income:Capital-Gains:Schwab:{ticker}",
            "capgainsd_lt": "Income:Capital-Gains-Distributions:Long:Schwab:{ticker}",
            "capgainsd_st": "Income:Capital-Gains-Distributions:Short:Schwab:{ticker}",
            "fees": "Expenses:Brokerage-Fees:Schwab",
            "invexpense": "Expenses:Brokerage-Expenses:TradIRA",
            "rounding_error": "Equity:Rounding-Errors:Imports",
            "fund_info": fund_info,
        }
    ),
]

if __name__ == "__main__":
    ingest = beangulp.Ingest(CONFIG)
    ingest()
