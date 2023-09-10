# flake8: noqa

from os import path
from beancount.ingest import regression_pytest as regtest
from beancount_reds_importers.importers import etrade


fund_data = [
 ('TSM', '874039100', 'Taiwan Semiconductor Mfg LTD'),
 ('VISA', '92826C839', 'Visa Inc'),
]

# list of money_market accounts. These will not be held at cost, and instead will use price conversions
money_market = ['VMFXX']

fund_info = {
        'fund_data': fund_data,
        'money_market': money_market,
        }


def build_config():
    acct = "Assets:Investments:Etrade"
    root = 'Investments'
    taxability = 'Taxable'
    leaf = 'Etrade'
    currency = 'USD'
    config = {
        'account_number' : '555555555',
        'main_account'   : acct + ':{ticker}',
        'cash_account'   : f'{acct}:{{currency}}',
        'transfer'       : 'Assets:Zero-Sum-Accounts:Transfers:Bank-Account',
        'dividends'      : f'Income:{root}:{taxability}:Dividends:{leaf}:{{ticker}}',
        'interest'       : f'Income:{root}:{taxability}:Interest:{leaf}:{{ticker}}',
        'cg'             : f'Income:{root}:{taxability}:Capital-Gains:{leaf}:{{ticker}}',
        'capgainsd_lt'   : f'Income:{root}:{taxability}:Capital-Gains-Distributions:Long:{leaf}:{{ticker}}',
        'capgainsd_st'   : f'Income:{root}:{taxability}:Capital-Gains-Distributions:Short:{leaf}:{{ticker}}',
        'fees'           : f'Expenses:Fees-and-Charges:Brokerage-Fees:{taxability}:{leaf}',
        'invexpense'     : f'Expenses:Expenses:Investment-Expenses:{taxability}:{leaf}',
        'rounding_error' : 'Equity:Rounding-Errors:Imports',
        'fund_info'      : fund_info,
        'currency'       : currency,
    }
    return config


@regtest.with_importer(
    etrade.Importer(
        build_config()
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestEtradeQFX(regtest.ImporterTestBase):
    pass
