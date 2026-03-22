"""Unit tests for SECLIST-based fund_info augmentation in investments.Importer.

The initialize() method in investments.Importer populates funds_by_id and
funds_by_ticker from two sources, with config taking precedence:
  1. fund_info['fund_data'] in the importer config  (highest precedence)
  2. The SECLIST section of the OFX file            (fills in the rest)

Static fixture files in this directory cover the key scenarios:
  with_ticker.qfx  - SECLIST entry has both UNIQUEID and TICKER
  no_ticker.qfx    - SECLIST entry has UNIQUEID but no TICKER
  no_seclist.qfx   - OFX file has no SECLISTMSGSRSV1 block at all
"""

from os import path

from beancount_reds_importers.importers import vanguard

TESTDIR = path.dirname(__file__)

WITH_TICKER = path.join(TESTDIR, "with_ticker.qfx")
NO_TICKER = path.join(TESTDIR, "no_ticker.qfx")
NO_SECLIST = path.join(TESTDIR, "no_seclist.qfx")

CUSIP = "92202E862"
TICKER = "VFIFX"
SECNAME = "VANGUARD TARGET RETIREMENT 2050 INVESTOR CL"


def make_importer(fund_data=None, money_market=None):
    return vanguard.Importer(
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
            "emit_filing_account_metadata": False,
            "fund_info": {
                "fund_data": fund_data or [],
                "money_market": money_market or [],
            },
        }
    )


# ---------------------------------------------------------------------------
# SECLIST populates fund_info when fund_data is empty
# ---------------------------------------------------------------------------


def test_seclist_populates_funds_by_id():
    importer = make_importer()
    importer.initialize(WITH_TICKER)
    assert importer.funds_by_id[CUSIP] == (TICKER, SECNAME)


def test_seclist_populates_funds_by_ticker():
    importer = make_importer()
    importer.initialize(WITH_TICKER)
    assert importer.funds_by_ticker[TICKER] == (TICKER, SECNAME)


# ---------------------------------------------------------------------------
# Config-provided entries take precedence over SECLIST
# ---------------------------------------------------------------------------


def test_config_entry_not_overwritten_by_seclist_in_funds_by_id():
    importer = make_importer(fund_data=[("MY_TICKER", CUSIP, "My Fund Name")])
    importer.initialize(WITH_TICKER)
    assert importer.funds_by_id[CUSIP] == ("MY_TICKER", "My Fund Name")


def test_config_entry_not_overwritten_by_seclist_in_funds_by_ticker():
    importer = make_importer(fund_data=[("MY_TICKER", CUSIP, "My Fund Name")])
    importer.initialize(WITH_TICKER)
    assert importer.funds_by_ticker["MY_TICKER"] == ("MY_TICKER", "My Fund Name")


# ---------------------------------------------------------------------------
# SECLIST entries without a <TICKER> tag are silently skipped
# ---------------------------------------------------------------------------


def test_seclist_entry_without_ticker_not_added_to_funds_by_id():
    importer = make_importer()
    importer.initialize(NO_TICKER)
    assert CUSIP not in importer.funds_by_id


def test_seclist_entry_without_ticker_not_added_to_funds_by_ticker():
    importer = make_importer()
    importer.initialize(NO_TICKER)
    assert TICKER not in importer.funds_by_ticker


# ---------------------------------------------------------------------------
# OFX files with no SECLIST block are handled without error
# ---------------------------------------------------------------------------


def test_no_seclist_does_not_raise():
    importer = make_importer(fund_data=[(TICKER, CUSIP, "Vanguard 2050")])
    importer.initialize(NO_SECLIST)  # must not raise


def test_no_seclist_config_entries_still_present():
    importer = make_importer(fund_data=[(TICKER, CUSIP, "Vanguard 2050")])
    importer.initialize(NO_SECLIST)
    assert importer.funds_by_id[CUSIP] == (TICKER, "Vanguard 2050")
