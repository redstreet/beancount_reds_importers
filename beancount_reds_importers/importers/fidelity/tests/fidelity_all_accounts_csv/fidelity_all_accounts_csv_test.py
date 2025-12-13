# flake8: noqa

from os import path
import sys

# hack to use testing code
sys.path.insert(0, path.normpath(path.join(path.dirname(__file__), "../../../../..")))

try:
    from beancount.ingest import regression_pytest as regtest
except ModuleNotFoundError:
    from beancount_reds_importers.util import regression_pytest as regtest

from beancount_reds_importers.importers.fidelity import fidelity_all_accounts_csv

fund_data = [
    ('BND', '921937835', 'VANGUARD BD INDEX FDS TOTAL BND MRKT'),
    ('VTEB', '922907746', 'VANGUARD MUN BD FDS TAX EXEMPT BD'),
    ('CUSIP96255NBE8', '96255NBE8', '96255NBE8 WHEAT RIDGE COLO SALES & USE TAX REV 05.00000% 12/01/2041 REF IMPT BDS SER. 2024'),
    ("OSK", "688239201", "OSHKOSH CORP"),
    ("WM", "94106L109", "WASTE MANAGEMENT INC"),
    ('JEPI', '46641Q332', 'J P MORGAN EXCHANGE TRADED FD EQUITY PREMIUM'),
    ('VVV', '92047W101', 'VALVOLINE INC COM'),
    ("ZTS", "98978V103", "ZOETIS INC"),
    ("CUSIP44244CCF2", "44244CCF2", "44244CCF2 HOUSTON TEX UTIL SYS REV REF BDS SER. 05.00000% 11/15/2025 2015D"),
    ('TSM', '874039100', 'TAIWAN SEMICONDUCTOR MANUFACTURING SPON ADS EACH REP 5 ORD TWD10'),
    ('COR', '03073E105', 'AMERISOURCEBERGEN CORPORATION COM USD0.01'),
    ('VGK', '922042874', 'VANGUARD INTL EQUITY INDEX FDS FTSE EUROPE ETF'),
    # test a bond where chosen symbol fails on substring match
    ('CUSIP412003AD7', '412003AD7', 'HARDIN CNTY OHIO ECONOMIC DEV FACS 05.50000% 05/01/2050 REV REF IMPT BDS OHIO NORTHERN UNIV SER. 2020'),
    # test mapping a security to different symbol
    # ("V-V", "92826C839", "VISA INC"),
    # test a security with a symbol as a substring
    ("G", "G3922B107", "GENPACT LIMITED COM STK USD0.01"),
]

# list of money_market accounts. These will not be held at cost, and instead will use price conversions
money_market = ["VMFXX"]

fund_info = {
    "fund_data": fund_data,
    "money_market": money_market,
}


config = {
    "currency": "USD",
    "account_number": "333333333",
    'add_precision': True,
    'use_inferred_price': True,
    'fix_muni_shares': True,
    'security_symbol_map': {
        "M": "M-M",
        "V": "V-V",
        "T": "T-T",
        "C": "C-C",
        "F": "F-F",
        "G": "G-G",
        "K": "K-K",
        "A": "A-A",
    },
    'actions_to_treat_as_cash_reinvestment': [
        "REINVESTMENT CIBC INSTITUTIONAL DEPOSIT SWEEP PROGRAM (QCIBQ) (Cash)",
    ],
    'actions_to_treat_as_cash': (
        "INTEREST EARNED FDIC INSURED DEPOSIT AT",
        "INTEREST EARNED CIBC INSTITUTIONAL DEPOSIT SWEEP PROGRAM (QCIBQ)",
    ),
    "main_account": "Assets:Investments:Fidelity" + ":{ticker}",
    "cash_account": "Assets:Investments:Fidelity:{currency}",
    "transfer": "Assets:Zero-Sum-Accounts:Transfers:Bank-Account",
    "dividends": "Income:Investments:Taxable:Dividends:Fidelity:{{ticker}}",
    "interest": "Income:Investments:Taxable:Interest:Fidelity:{{ticker}}",
    "cg": "Income:Investments:Taxable:Capital-Gains:Fidelity:{{ticker}}",
    "capgainsd_lt": "Income:Investments:Taxable:Capital-Gains-Distributions:Long:Fidelity:{{ticker}}",
    "capgainsd_st": "Income:Investments:Taxable:Capital-Gains-Distributions:Short:Fidelity:{{ticker}}",
    "fees": "Expenses:Fees-and-Charges:Brokerage-Fees:Taxable:Fidelity",
    "invexpense": "Expenses:Expenses:Investment-Expenses:Taxable:Fidelity",
    "rounding_error": "Equity:Rounding-Errors:Imports",
    "fund_info": fund_info,
    "emit_filing_account_metadata": False,
    "filename_pattern": 'fidelity_csv_all_accounts_transactions_.*.csv',
}
# print(config)
@regtest.with_importer(fidelity_all_accounts_csv.Importer(config))
@regtest.with_testdir(path.dirname(__file__))
class TestFidelityAllAccountsCsv(regtest.ImporterTestBase):
    pass
