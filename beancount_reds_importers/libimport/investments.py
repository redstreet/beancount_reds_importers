"""Generic investment ofx importer for beancount."""

import datetime
import itertools
import ntpath
import traceback
from ofxparse import OfxParser
from beancount.core import data
from beancount.core import amount
from beancount.ingest import importer
from beancount.core.position import CostSpec

from beancount_reds_importers.libimport import common


class Importer(importer.ImporterProtocol):
    def __init__(self, config):
        self.config = config
        self.initialized = False
        self.custom_init_run = False
        # REQUIRED_CONFIG = {
        #     'account_number'   : 'account number',
        #     'main_account'     : 'Destination account of import',
        #     'transfer'         : 'Account to which contributions and outgoing is transferred',
        #     'dividends'        : 'Account to book dividends',
        #     'cg'               : 'Account to book capital gains/losses',
        #     'fees'             : 'Account to book fees to',
        #     'rounding_error'   : 'Account to book rounding errors to',
        #     'fund_info '       : 'dictionary of fund info (ticker_map, money_market, etc.)'
        # }

    def initialize(self, file):
        if not self.initialized:
            self.custom_init()
            self.ofx = OfxParser.parse(open(file.name))
            self.ofx_account = None
            for acc in self.ofx.accounts:
                # account identifying info fieldname varies across institutions
                if getattr(acc, self.account_number_field) == self.config['account_number']:
                    self.ofx_account = acc
            if self.ofx_account is not None:
                self.money_market_funds = self.config['fund_info']['money_market']
                self.currency = self.ofx_account.statement.currency.upper()
                self.inv_ticker_map = {v: k for k, v in self.config['fund_info']['ticker_map'].items()}
                self.build_account_map()
            self.initialized = True

    def build_account_map(self):
        # transaction types: {'buymf', 'sellmf', 'buystock', 'sellstock', 'other', 'reinvest', 'income'}
        self.target_account_map = {
            "buymf":     self.config['main_account'],
            "sellmf":    self.config['main_account'],
            "buystock":  self.config['main_account'],
            "sellstock": self.config['main_account'],
            "reinvest":  self.config['dividends'],
            "income":    self.config['dividends'],
            "other":     self.config['transfer'],
            "credit":    self.config['transfer'],
            "debit":    self.config['transfer'],
            "transfer":     self.config['transfer'],
        }

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.account_number_field = 'number'
            self.filename_identifier_substring = 'bank_specific_filename.qfx'
            self.custom_init_run = True

    def identify(self, file):
        self.custom_init()
        if self.filename_identifier_substring not in file.name:
            return False
        self.initialize(file)
        return self.ofx_account is not None

    def file_name(self, file):
        return 'account-{}'.format(ntpath.basename(file.name))

    def file_account(self, _):
        return self.config['main_account']

    def file_date(self, file):
        "Get the maximum date from the file."
        self.ofx_account.statement.end_date

    def get_ticker_info(self, security):
        return security, 'UNKNOWN'

    def get_target_acct(self, transaction):
        return self.target_account_map.get(transaction.type, None)

    def get_ticker_list(self):
        tickers = []
        for ot in self.ofx_account.statement.transactions:
            if ot.type in ['buymf', 'sellmf', 'buystock', 'sellstock', 'reinvest', 'income']:
                tickers.append(ot.security)
        return tickers

    # --------------------------------------------------------------------------------

    def extract(self, file):
        config = self.config
        # Example:
        # {'type': 'buymf',
        # 'tradeDate': datetime.datetime(2018, 6, 25, 19, 0),
        # 'settleDate': datetime.datetime(2018, 6, 25, 19, 0),
        # 'memo': 'MONEY FUND PURCHASE',
        # 'security': 'XXYYYZZ',
        # 'income_type': '', ('', None, DIV)
        # 'units': Decimal('2345.67'),
        # 'unit_price': Decimal('1.0'),
        # 'commission': Decimal('0'),
        # 'fees': Decimal('0'),
        # 'total': Decimal('-2345.67'),
        # 'tferaction': None, 'id': '10293842'}

        new_entries = []
        self.initialize(file)
        counter = itertools.count()
        for ot in self.ofx_account.statement.transactions:
            if ot.type in ['buymf', 'sellmf', 'buystock', 'sellstock', 'reinvest', 'income']:
                # Build metadata
                ticker, ticker_long_name = self.get_ticker_info(ot.security)
                is_money_market = ticker in self.money_market_funds
                metadata = data.new_metadata(file.name, next(counter))
                if ot.settleDate is not None:
                    metadata['settlement_date'] = str(ot.settleDate.date())
                # Optional metadata, useful for debugging
                # metadata['type'] = ot.type

                if 'sell' in ot.type and not is_money_market:
                    metadata['todo'] = 'TODO: this entry is incomplete until lots are selected (bean-doctor context <filename> <lineno>)'
                if 'sell' in ot.type:
                    ot.units = -1 * abs(ot.units)
                if ot.type in ['reinvest', 'dividends']:
                    ot.total = -1 * abs(ot.total)
                description = '[' + ticker + '] ' + ticker_long_name
                target_acct = self.get_target_acct(ot)

                # Build transaction entry
                entry = data.Transaction(metadata, ot.tradeDate.date(), self.FLAG,
                                         ot.memo, description, data.EMPTY_SET, data.EMPTY_SET, [])

                # Build postings
                if ot.type == 'income':  # cash
                    data.create_simple_posting(entry, config['main_account'], ot.total, self.currency)
                    data.create_simple_posting(entry, target_acct, -1 * ot.total, self.currency)
                else:  # stock/fund
                    if is_money_market:
                        common.create_simple_posting_with_price(entry, config['main_account'],
                                                                ot.units, ticker, ot.unit_price, self.currency)
                    elif 'sell' in ot.type:
                        common.create_simple_posting_with_cost_or_price(entry, config['main_account'],
                                                                        ot.units, ticker, price_number=ot.unit_price,
                                                                        price_currency=self.currency,
                                                                        costspec=CostSpec(None, None, None, None, None, None))
                        data.create_simple_posting(
                            entry, self.config['cg'], None, None)
                    else:  # buy stock/fund
                        common.create_simple_posting_with_cost(entry, config['main_account'],
                                                               ot.units, ticker, ot.unit_price, self.currency)
                    data.create_simple_posting(
                        entry, target_acct, ot.total, self.currency)

                    # Rounding errors
                    rounding_error = ot.total + (ot.unit_price * ot.units)
                    if 0.0005 <= abs(rounding_error) <= self.max_rounding_error:
                        data.create_simple_posting(
                            entry, config['rounding_error'], -1 * rounding_error, 'USD')
                    # if abs(rounding_error) > self.max_rounding_error:
                    #     print("Transactions legs do not sum up! Difference: {}. Entry: {}, ot: {}".format(
                    #         rounding_error, entry, ot))

            # cash or in-kind transfers
            elif ot.type in ['other', 'credit', 'debit', 'transfer']:
                # Build metadata
                metadata = data.new_metadata(file.name, next(counter))
                target_acct = self.get_target_acct(ot)

                if ot.type == 'transfer':  # in-kind transfer
                    ticker, ticker_long_name = self.get_ticker_info(
                        ot.security)
                    description = '[' + ticker + '] ' + ticker_long_name
                    date = ot.tradeDate.date()
                    units = ot.units
                else:  # cash transfer
                    description = 'TRANSFER'
                    date = ot.date.date()
                    units = ot.amount
                    ticker = self.currency

                # Build transaction entry
                entry = data.Transaction(metadata, date, self.FLAG,
                                         ot.memo, description, data.EMPTY_SET, data.EMPTY_SET, [])

                # Build postings
                data.create_simple_posting(
                    entry, config['main_account'], units, ticker)
                data.create_simple_posting(
                    entry, target_acct, -1*units, ticker)

            else:
                print("ERROR: unknown entry type:", ot.type)
                raise Exception('Unknown entry type')

            if hasattr(ot, 'fees') or hasattr(ot, 'commission'):
                if ot.fees != 0:
                    data.create_simple_posting(
                        entry, config['fees'], ot.fees, self.currency)
                if ot.commission != 0:
                    data.create_simple_posting(
                        entry, config['fees'], ot.commission, self.currency)
            new_entries.append(entry)

        # balance assertions
        # The Balance assertion occurs at the beginning of the date, so move
        # it to the following day.
        try:
            # date = self.ofx_account.statement.end_date.date() # this is the date of ofx download

            # we find the last transaction's date. If we use the ofx download date, we could end up with a gap
            # in time between the last transaction's date and balance assertion. Pending (but not yet
            # downloaded) transactions in this gap will get downloaded the next time we do a download in the
            # future, and cause the balance assertions to be invalid.
            date = max(ot.tradeDate if hasattr(ot, 'tradeDate') else ot.date
                       for ot in self.ofx_account.statement.transactions).date()
        except Exception as err:
            print("ERROR: no end_date. SKIPPING input.")
            traceback.print_tb(err.__traceback__)
            return []
        date += datetime.timedelta(days=1)
        settlement_fund_balance = 0
        for pos in self.ofx_account.statement.positions:
            ticker, ticker_long_name = self.get_ticker_info(pos.security)
            meta = data.new_metadata(file.name, next(counter))
            balance_entry = data.Balance(meta, date, self.config['main_account'],
                                         amount.Amount(pos.units, ticker),
                                         None, None)
            new_entries.append(balance_entry)
            if ticker in self.money_market_funds:
                settlement_fund_balance = pos.units

            # extract price info if available
            if hasattr(pos, 'unit_price') and hasattr(pos, 'date'):
                meta = data.new_metadata(file.name, next(counter))
                price_entry = data.Price(meta, pos.date.date(), ticker,
                                         amount.Amount(pos.unit_price, self.currency))
                new_entries.append(price_entry)

        # we want trade date balance, which is reflected as USD
        #
        # trade date balance: The net dollar amount in your account that has not swept to or from your
        # settlement fund.
        #
        # available cash combines settlement fund and trade date balance
        balance = self.ofx_account.statement.available_cash - settlement_fund_balance
        meta = data.new_metadata(file.name, next(counter))
        balance_entry = data.Balance(meta, date, self.config['main_account'],
                                     amount.Amount(balance, self.currency),
                                     None, None)
        new_entries.append(balance_entry)

        return(new_entries)

# TODO
# -----------------------------------------------------------------------------------------------------------
# Feature improvements:
# - CG: book gains and losses to separate accounts, and short-term/long-term to separate accounts
