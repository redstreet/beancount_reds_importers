"""Generic banking ofx importer for beancount."""

import datetime
import itertools
import ntpath
from ofxparse import OfxParser
from beancount.core import data
from beancount.core import amount
from beancount.ingest import importer


class Importer(importer.ImporterProtocol):
    def __init__(self, config):
        self.config = config
        self.initialized = False
        self.custom_init_run = False
        # REQUIRED_CONFIG = {
        #     'account_number'   : 'account number',
        #     'main_account'     : 'destination of import',
        # }

    def initialize(self, file):
        if not self.initialized:
            self.custom_init()
            self.ofx = OfxParser.parse(open(file.name))
            self.ofx_account = None
            for acc in self.ofx.accounts:
                # account identifying info fieldname varies across institutions
                if getattr(acc, self.account_number_field).endswith(self.config['account_number']):
                    self.ofx_account = acc
            if self.ofx_account is not None:
                self.currency = self.ofx_account.statement.currency.upper()
                self.build_account_map()
            self.initialized = True

    def build_account_map(self):
        # Not needed for accounts using smart_importer
        # transaction types: {}
        # self.target_account_map = {
        #         "directdep": 'TODO',
        #         "credit":    'TODO',
        #         "debit":     'TODO',
        # }
        pass

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.account_number_field = 'account_id'
            self.filename_identifier_substring = ''
            self.custom_init_run = True

    def identify(self, file):
        if not file.name.endswith('fx'):
            return False
        self.custom_init()
        if self.filename_identifier_substring not in file.name:
            return False
        self.initialize(file)
        return self.ofx_account is not None

    def file_name(self, file):
        return '{}'.format(ntpath.basename(file.name))

    def file_account(self, _):
        return self.config['main_account']

    def file_date(self, file):
        "Get the maximum date from the file."
        self.ofx_account.statement.end_date

    def get_target_acct(self, transaction):
        # Not needed for accounts using smart_importer
        return self.target_account_map.get(transaction.type, None)

    # --------------------------------------------------------------------------------

    def extract(self, file, existing_entries=None):
        config = self.config

        new_entries = []
        self.initialize(file)
        counter = itertools.count()
        for ot in self.ofx_account.statement.transactions:
            # Build metadata
            metadata = data.new_metadata(file.name, next(counter))
            # metadata['type'] = ot.type # Optional metadata, useful for debugging #TODO

            # Build transaction entry
            entry = data.Transaction(metadata, ot.date.date(), self.FLAG,
                                     None, ot.payee, data.EMPTY_SET, data.EMPTY_SET, [])
            data.create_simple_posting(entry, config['main_account'], ot.amount, self.currency)

            # Commented out so smart_importer can fill this in
            # target_acct = self.get_target_acct(ot)
            # data.create_simple_posting(entry, target_acct, None, None)

            new_entries.append(entry)

        # balance assertion
        # The Balance assertion occurs at the beginning of the date, so move
        # it to the following day.
        date = self.ofx_account.statement.balance_date
        date += datetime.timedelta(days=1)
        meta = data.new_metadata(file.name, next(counter))
        balance_entry = data.Balance(meta, date.date(), self.config['main_account'],
                                     amount.Amount(self.ofx_account.statement.balance, self.currency),
                                     None, None)
        new_entries.append(balance_entry)

        return(new_entries)
