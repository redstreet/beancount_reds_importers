"""Generic investment importer module for beancount. Needs a reader module (eg: ofx, csv, etc.) from
beancount_reads_importers to work."""

import datetime
import itertools
import sys
from beancount.core import data
from beancount.core import amount
from beancount.ingest import importer
from beancount.core.position import CostSpec
from beancount_reds_importers.libtransactionbuilder import common


class Importer(importer.ImporterProtocol):
    def __init__(self, config):
        self.config = config
        self.initialized = False
        self.reader_ready = False
        self.custom_init_run = False
        self.price_cost_both_zero_handler = None

        # For overriding in custom_init()
        self.get_payee = lambda ot: ot.memo

        # REQUIRED_CONFIG = {
        #     #                  : # The string "{ticker}" will be replaced with the ticker symbol. Use this
        #                            to obtain account names that end with the commodity (commodity leaf
        #                            accounts). The string "{currency}" will be replaced with the operating
        #                            currency of the account in question (which is in turn obtained from the
        #                            ofx or csv)
        #     'account_number'   : 'account number',
        #     'main_account'     : 'Destination account of import',
        #     'cash_account'     : 'Cash account (usually same as the main account + a :{currency} appended)',
        #     'transfer'         : 'Account to which contributions and outgoing is transferred',
        #     #                     transfer account is optional. If left off no target posting will be created.
        #     #                     This allows for additional tools to handle this like smart importer.
        #     'dividends'        : 'Account to book dividends',
        #     'cg'               : 'Account to book capital gains/losses',
        #     'capgainsd_lt'     : 'Account to book long term capital gains distributions to'
        #     'capgainsd_st'     : 'Account to book short term capital gains distributions to'
        #     'fees'             : 'Account to book fees to',
        #     'rounding_error'   : 'Account to book rounding errors to',
        #     'fund_info '       : 'dictionary of fund info (by_id, money_market)',
        # }
        #
        # Example:
        # { 'account_number' : '1234567',
        #     'main_account'   : 'Assets:Investments:XTrade:{ticker}',
        #     'cash_account'   : 'Assets:Investments:XTrade:{currency}',
        #     'transfer'       : 'Assets:Zero-Sum-Accounts:Transfers:Bank-Account',
        #     'dividends'      : 'Income:Dividends:XTrade:{ticker}',
        #     'interest'       : 'Income:Interest:XTrade:{ticker}',
        #     'cg'             : 'Income:Capital-Gains:XTrade:{ticker}',
        #     'capgainsd_lt'   : 'Income:Capital-Gains-Distributions:Long:XTrade:{ticker}',
        #     'capgainsd_st'   : 'Income:Capital-Gains-Distributions:Short:XTrade:{ticker}',
        #     'fees'           : 'Expenses:Brokerage-Fees:XTrade',
        #     'rounding_error' : 'Equity:Rounding-Errors:Imports',
        #     'fund_info'       : fund_info, }

    def initialize(self, file):
        if not self.initialized:
            self.custom_init()
            self.initialize_reader(file)
            if self.reader_ready:
                # self.currency is defined by the reader (ofx, csv, etc.)
                d = {'currency': self.currency, 'ticker': '{ticker}'}
                self.config = {k: v.format(**d) if isinstance(v, str) else v for k, v in self.config.items()}
                self.money_market_funds = self.config['fund_info']['money_market']
                self.fund_data = self.config['fund_info']['fund_data']  # [(ticker, id, long_name), ...]
                self.funds_by_id = {i: (ticker, desc) for ticker, i, desc in self.fund_data}
                self.funds_by_ticker = {ticker: (ticker, desc) for ticker, _, desc in self.fund_data}

                # Most ofx/csv files refer to funds by id (cusip/isin etc.) Some use tickers instead
                self.funds_db = getattr(self, getattr(self, 'funds_db_txt', 'funds_by_id'))
                self.build_account_map()  # TODO: avoid for identify()
            self.initialized = True

    def build_account_map(self):
        # map transaction types to target posting accounts
        self.target_account_map = {
            "buymf":        self.config['cash_account'],
            "sellmf":       self.config['cash_account'],
            "buystock":     self.config['cash_account'],
            "sellstock":    self.config['cash_account'],
            "buyother":     self.config['cash_account'],
            "sellother":    self.config['cash_account'],
            "reinvest":     self.config['dividends'],
            "dividends":    self.config['dividends'],
            "capgainsd_lt": self.config['capgainsd_lt'],
            "capgainsd_st": self.config['capgainsd_st'],
            "income":       self.config['interest'],
        }

        if 'transfer' in self.config:
            self.target_account_map.update({
                "other":    self.config['transfer'],
                "credit":   self.config['transfer'],
                "debit":    self.config['transfer'],
                "transfer": self.config['transfer'],
                "cash":     self.config['transfer'],
                "dep":      self.config['transfer'],
            })

    def build_metadata(self, file, metatype=None, data={}):
        """This method is for importers to override. The overridden method can
        look at the metatype ('transaction', 'balance', 'account', 'commodity', etc.)
        and the data dictionary to return additional metadata"""
        return {}

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_pattern_def = '.*bank_specific_filename.*'
            self.custom_init_run = True

    def get_ticker_info(self, security_id):
        return security_id, 'UNKNOWN'

    def get_ticker_info_from_id(self, security_id):
        try:
            # isin might look like "US293409829" while the ofx use only a substring like "29340982"
            # first try a full match, fall back to substring
            ticker = None
            ticker, ticker_long_name = [v for k, v in self.funds_db.items() if security_id == k][0]
            if ticker is None:
                ticker, ticker_long_name = [v for k, v in self.funds_db.items() if security_id in k][0]
        except IndexError:
            print(f"Error: fund info not found for {security_id}", file=sys.stderr)
            securities = self.get_security_list()
            securities_missing = [s for s in securities]
            for s in securities:
                for k in self.funds_db:
                    if s in k:
                        securities_missing.remove(s)
            # securities_missing = [s for s in securities if s not in self.funds_db]

            # try to extract security info from ofx
            ofx_securities = dict()
            try:
                for o in self.ofx.security_list:
                    # It seems that because of the way investment transactions are reported
                    # in ofx the securities returned by self.get_security_list() are a list
                    # of cusip codes.  In the section of the ofx that lists all securities
                    # and is found in self.ofx.security_list these codes are generally
                    # referred to as UNIQUEID (though the presence of another key called
                    # UNIQUEIDTYPE suggests that UNIQUEID is not always a cusip).
                    # because of this the key for the ofx_securities dict is uniqueid which
                    # corresponds to the items in the securities_missing list.  The values
                    # of this dict are the best guess at what an entry for fund_info.py should
                    # be: a tuple of (ticker, cusip, name).  Note in the case of bonds the
                    # ticker will match the cusip (at least in examples I have) and not be
                    # literally usable as a beancount symbol
                    ofx_securities[o.uniqueid] = (o.ticker, o.uniqueid, o.name)
            except AttributeError:
                # ofx doesn't have a security list
                pass

            print("List of securities without fund info:", file=sys.stderr)
            for m in securities_missing:
                print("%s: %s" % (m, ofx_securities.get(m, "???")), file=sys.stderr)
            # print(f"List of securities without fund info: {securities_missing}", file=sys.stderr)
            # import pdb; pdb.set_trace()
            sys.exit(1)
        return ticker, ticker_long_name

    def get_target_acct_custom(self, transaction, ticker=None):
        """This method is for importers to override. The overridden method can return a target account for
        special cases, or return None, which will let get_target_acct() decide the target account"""
        return None

    def get_target_acct(self, transaction, ticker):
        target = self.get_target_acct_custom(transaction, ticker)
        if target:
            return target
        if transaction.type == 'income' and getattr(transaction, 'income_type', None) == 'DIV':
            return self.target_account_map.get('dividends', None)
        return self.target_account_map.get(transaction.type, None)

    def security_narration(self, ot):
        ticker, ticker_long_name = self.get_ticker_info(ot.security)
        return f"[{ticker}] {ticker_long_name}"

    def get_security_list(self):
        tickers = set()
        for ot in self.get_transactions():
            if hasattr(ot, 'security'):
                tickers.add(ot.security)
        return tickers

    def main_acct(self, ticker):
        return self.config['main_account'].format(ticker=ticker)

    # for custom importers to override
    def skip_transaction(self, ot):
        return False

    # extract() and supporting methods
    # --------------------------------------------------------------------------------

    def generate_trade_entry(self, ot, file, counter):
        """ Involves a commodity. One of: ['buymf', 'sellmf', 'buystock', 'sellstock', 'buyother',
        'sellother', 'reinvest']"""

        config = self.config
        ticker, ticker_long_name = self.get_ticker_info(ot.security)
        is_money_market = ticker in self.money_market_funds

        # Build metadata
        metadata = data.new_metadata(file.name, next(counter))
        metadata.update(self.build_metadata(file, metatype='transaction_trade', data={'transaction': ot}))
        if getattr(ot, 'settleDate', None) is not None and ot.settleDate != ot.tradeDate:
            metadata['settlement_date'] = str(ot.settleDate.date())

        narration = self.security_narration(ot)
        target_acct = self.get_target_acct(ot, ticker)
        units = ot.units
        total = ot.total

        # special cases
        if 'sell' in ot.type:
            units = -1 * abs(ot.units)
            if not is_money_market:
                metadata['todo'] = 'TODO: this entry is incomplete until lots are selected (bean-doctor context <filename> <lineno>)'  # noqa: E501
        if ot.type in ['reinvest']:  # dividends are booked to commodity_leaf. Eg: Income:Dividends:HOOLI
            target_acct = target_acct.format(ticker=ticker)
        else:
            target_acct = target_acct.format(ticker=self.currency)

        # Build transaction entry
        entry = data.Transaction(metadata, ot.tradeDate.date(), self.FLAG,
                                 self.get_payee(ot), narration,
                                 data.EMPTY_SET, data.EMPTY_SET, [])

        # Main posting(s):
        main_acct = self.main_acct(ticker)

        if is_money_market:  # Use price conversions instead of holding these at cost
            common.create_simple_posting_with_price(entry, main_acct,
                                                    units, ticker, ot.unit_price, self.currency)
        elif 'sell' in ot.type:
            common.create_simple_posting_with_cost_or_price(entry, main_acct,
                                                            units, ticker, price_number=ot.unit_price,
                                                            price_currency=self.currency,
                                                            costspec=CostSpec(None, None, None, None, None, None))
            data.create_simple_posting(entry, self.config['cg'].format(ticker=ticker), None, None)
        else:  # buy stock/fund
            # annoyingly, vanguard reinvests have unit_price set to zero. so manually compute it
            if (hasattr(ot, 'security') and ot.security) and ot.units and not ot.unit_price:
                ot.unit_price = round(abs(ot.total) / ot.units, 4)
            common.create_simple_posting_with_cost(entry, main_acct, units, ticker, ot.unit_price,
                                                   self.currency, self.price_cost_both_zero_handler)

        # "Other" account posting
        reverser = 1
        if units > 0 and total > 0:  # (ugly) hack for some brokerages with incorrect signs (TODO: remove)
            reverser = -1
        data.create_simple_posting(entry, target_acct, reverser * total, self.currency)

        # Rounding errors posting
        rounding_error = (reverser * total) + (ot.unit_price * units)
        if 0.0005 <= abs(rounding_error) <= self.max_rounding_error:
            data.create_simple_posting(
                entry, config['rounding_error'], -1 * rounding_error, 'USD')
        # if abs(rounding_error) > self.max_rounding_error:
        #     print("Transactions legs do not sum up! Difference: {}. Entry: {}, ot: {}".format(
        #         rounding_error, entry, ot))

        return entry

    def generate_transfer_entry(self, ot, file, counter):
        """ Cash transactions, or in-kind transfers. One of:
            [credit, debit, dep, transfer, income, dividends, capgainsd_lt, capgainsd_st, other]"""
        config = self.config
        metadata = data.new_metadata(file.name, next(counter))
        metadata.update(self.build_metadata(file, metatype='transaction_transfer', data={'transaction': ot}))
        ticker = None
        date = getattr(ot, 'tradeDate', None)
        if not date:
            date = ot.date
        date = date.date()

        try:
            if ot.type in ['transfer']:
                units = ot.units
            elif ot.type in ['other', 'credit', 'debit', 'dep', 'cash', 'payment', 'check']:
                units = ot.amount
            else:
                units = ot.total
        except AttributeError:
            print("Could not determine field for transaction amount")
            # import pdb; pdb.set_trace()

        main_acct = None
        if ot.type in ['income', 'dividends', 'capgainsd_lt',
                       'capgainsd_st', 'transfer'] and (hasattr(ot, 'security') and ot.security):
            ticker, ticker_long_name = self.get_ticker_info(ot.security)
            narration = self.security_narration(ot)
            main_acct = self.main_acct(ticker)
        else:  # cash transaction
            narration = ot.type
            ticker = self.currency
            main_acct = config['cash_account']

        # Build transaction entry
        entry = data.Transaction(metadata, date, self.FLAG,
                                 self.get_payee(ot), narration,
                                 data.EMPTY_SET, data.EMPTY_SET, [])
        target_acct = self.get_target_acct(ot, ticker)
        if target_acct:
            target_acct = target_acct.format(ticker=ticker)

        # Build postings
        if ot.type in ['income', 'dividends', 'capgainsd_st', 'capgainsd_lt']:  # cash
            data.create_simple_posting(entry, config['cash_account'], ot.total, self.currency)
            data.create_simple_posting(entry, target_acct, -1 * ot.total, self.currency)
        else:
            data.create_simple_posting(entry, main_acct, units, ticker)
            if target_acct:
                data.create_simple_posting(entry, target_acct, -1 * units, ticker)
        return entry

    def extract_transactions(self, file, counter):
        # Required transaction fields: ({ofx, csv, ...}reader.py need to provide these fields)
        # 'type': 'buymf',
        # 'tradeDate': datetime.datetime(2018, 6, 25, 19, 0),
        # 'date': datetime.datetime(2018, 6, 25, 19, 0),
        # 'memo': 'MONEY FUND PURCHASE',
        # 'security': 'XXYYYZZ',
        # 'units': Decimal('2345.67'),
        # 'unit_price': Decimal('1.0'),
        # 'total': Decimal('-2345.67')

        # Optional transaction fields:
        # 'settleDate': datetime.datetime(2018, 6, 25, 19, 0),
        # 'commission': Decimal('0'),
        # 'fees': Decimal('0'),

        new_entries = []
        self.read_file(file)
        for ot in self.get_transactions():
            if self.skip_transaction(ot):
                continue
            if ot.type in ['buymf', 'sellmf', 'buystock', 'sellstock', 'buyother', 'sellother', 'reinvest']:
                entry = self.generate_trade_entry(ot, file, counter)
            elif ot.type in ['other', 'credit', 'debit', 'transfer', 'dep', 'income',
                             'dividends', 'capgainsd_st', 'capgainsd_lt', 'cash', 'payment', 'check']:
                entry = self.generate_transfer_entry(ot, file, counter)
            else:
                print("ERROR: unknown entry type:", ot.type)
                raise Exception('Unknown entry type')
            self.add_fee_postings(entry, ot)
            new_entries.append(entry)
        return new_entries

    def extract_balances_and_prices(self, file, counter):
        new_entries = []
        date = self.get_max_transaction_date()
        if date:
            # balance assertions are evaluated at the beginning of the date, so move it to the following day
            date += datetime.timedelta(days=1)
        else:
            print("Warning: no transactions, using statement date for balance assertions.")

        settlement_fund_balance = 0
        for pos in self.get_balance_positions():
            ticker, ticker_long_name = self.get_ticker_info(pos.security)
            metadata = data.new_metadata(file.name, next(counter))
            metadata.update(self.build_metadata(file, metatype='balance', data={'pos': pos}))

            # if there are no transactions, use the date in the source file for the balance. This gives us the
            # bonus of an updated, recent balance assertion
            bal_date = date if date else pos.date.date()
            balance_entry = data.Balance(metadata, bal_date, self.main_acct(ticker),
                                         amount.Amount(pos.units, ticker),
                                         None, None)
            new_entries.append(balance_entry)
            if ticker in self.money_market_funds:
                settlement_fund_balance = pos.units

            # extract price info if available
            if hasattr(pos, 'unit_price') and hasattr(pos, 'date'):
                metadata = data.new_metadata(file.name, next(counter))
                metadata.update(self.build_metadata(file, metatype='price', data={'pos': pos}))
                price_entry = data.Price(metadata, pos.date.date(), ticker,
                                         amount.Amount(pos.unit_price, self.currency))
                new_entries.append(price_entry)

        # ----------------- available cash
        available_cash = self.get_available_cash()
        if available_cash is not None:
            balance = available_cash - settlement_fund_balance
            metadata = data.new_metadata(file.name, next(counter))
            metadata.update(self.build_metadata(file, metatype='balance_cash'))
            try:
                bal_date = date if date else self.file_date(file).date()  # unavailable file_date raises AttributeError
                balance_entry = data.Balance(metadata, bal_date, self.config['cash_account'],
                                             amount.Amount(balance, self.currency),
                                             None, None)
                new_entries.append(balance_entry)
            except AttributeError:
                pass

        return new_entries

    def add_fee_postings(self, entry, ot):
        config = self.config
        if hasattr(ot, 'fees') or hasattr(ot, 'commission'):
            if getattr(ot, 'fees', 0) != 0:
                data.create_simple_posting(entry, config['fees'], ot.fees, self.currency)
            if getattr(ot, 'commission', 0) != 0:
                data.create_simple_posting(entry, config['fees'], ot.commission, self.currency)

    def extract_custom_entries(self, file, counter):
        """For custom importers to override"""
        return []

    def extract(self, file, existing_entries=None):
        self.initialize(file)
        counter = itertools.count()
        new_entries = []

        new_entries += self.extract_transactions(file, counter)
        new_entries += self.extract_balances_and_prices(file, counter)

        new_entries += self.extract_custom_entries(file, counter)

        return new_entries
