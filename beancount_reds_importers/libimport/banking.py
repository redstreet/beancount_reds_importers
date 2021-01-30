"""Generic banking ofx importer for beancount."""

import datetime
import itertools
from beancount.core import data
from beancount.core import amount
from beancount.ingest import importer


class Importer(importer.ImporterProtocol):
    def __init__(self, config):
        self.config = config
        self.initialized = False
        self.initialized_reader = False
        self.reader_ready = False
        self.custom_init_run = False
        # REQUIRED_CONFIG = {
        #     'account_number'   : 'account number',
        #     'main_account'     : 'destination of import',
        # }

    def initialize(self, file):
        if not self.initialized:
            self.custom_init()
            self.initialize_reader(file)
            self.initialized = True

    def build_account_map(self):
        # TODO: Not needed for accounts using smart_importer; make tihs configurable
        # transaction types: {}
        # self.target_account_map = {
        #         "directdep": 'TODO',
        #         "credit":    'TODO',
        #         "debit":     'TODO',
        # }
        pass

    def match_account_number(self, file_account, config_account):
        return file_account.endswith(config_account)

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.account_number_field = 'account_id'
            self.filename_identifier_substring = ''
            self.custom_init_run = True

    # def get_target_acct(self, transaction):
    #     # Not needed for accounts using smart_importer
    #     return self.target_account_map.get(transaction.type, None)

    # --------------------------------------------------------------------------------

    def extract_balance(self, file, counter):
        # date = self.ofx_account.statement.balance_date
        date = max(ot.tradeDate if hasattr(ot, 'tradeDate') else ot.date
                   for ot in self.get_transactions()).date()
        # balance assertions are evaluated at the beginning of the date, so move it to the following day
        date += datetime.timedelta(days=1)
        meta = data.new_metadata(file.name, next(counter))
        balance_entry = data.Balance(meta, date, self.config['main_account'],
                amount.Amount(self.ofx_account.statement.balance, self.currency),
                None, None)
        return [balance_entry]

    def extract(self, file, existing_entries=None):
        self.initialize(file)
        counter = itertools.count()
        new_entries = []
        config = self.config

        self.read_file(file)
        for ot in self.get_transactions():
            metadata = data.new_metadata(file.name, next(counter))
            # metadata['type'] = ot.type # Optional metadata, useful for debugging #TODO

            # Build transaction entry
            entry = data.Transaction(metadata, ot.date.date(), self.FLAG,
                                     None, ot.payee, data.EMPTY_SET, data.EMPTY_SET, [])
                                     # ot.payee, ot.type, data.EMPTY_SET, data.EMPTY_SET, [])
            data.create_simple_posting(entry, config['main_account'], ot.amount, self.currency)

            # TODO: Commented out so smart_importer can fill this in
            # target_acct = self.get_target_acct(ot)
            # data.create_simple_posting(entry, target_acct, None, None)

            new_entries.append(entry)

        if self.includes_balances:
            new_entries += self.extract_balance(file, counter)

        return(new_entries)
