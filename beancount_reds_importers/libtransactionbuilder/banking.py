"""Generic banking importer for beancount."""

import itertools
from beancount.core import data
from beancount.core import amount
from beancount.ingest import importer


class Importer(importer.ImporterProtocol):
    def __init__(self, config):
        self.config = config
        self.initialized = False
        self.reader_ready = False
        self.custom_init_run = False

        # For overriding in custom_init()
        self.get_payee = lambda ot: ot.payee
        self.get_narration = lambda ot: ot.memo

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
        # TODO: Not needed for accounts using smart_importer; make this configurable
        # transaction types: {}
        # self.target_account_map = {
        #         "directdep": 'TODO',
        #         "credit":    'TODO',
        #         "debit":     'TODO',
        # }
        pass

    def build_metadata(self, file, metatype=None, data={}):
        """This method is for importers to override. The overridden method can
        look at the metatype ('transaction', 'balance', 'account', 'commodity', etc.)
        and the data dictionary to return additional metadata"""
        return {}

    def match_account_number(self, file_account, config_account):
        return file_account.endswith(config_account)

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_pattern_def = '.*bank_specific_filename.*'
            self.custom_init_run = True

    # def get_target_acct(self, transaction):
    #     # Not needed for accounts using smart_importer
    #     return self.target_account_map.get(transaction.type, None)

    # --------------------------------------------------------------------------------

    def extract_balance(self, file, counter):
        entries = []
        metadata = data.new_metadata(file.name, counter)
        metadata.update(self.build_metadata(file, metatype='balance'))

        for bal in self.get_balance_statement():
            if bal:
                balance_entry = data.Balance(metadata, bal.date, self.config['main_account'],
                                             amount.Amount(bal.amount, self.currency),
                                             None, None)
                entries.append(balance_entry)
        return entries

    def extract_custom_entries(self, file, counter):
        """For custom importers to override"""
        return []

    # for custom importers to override
    def skip_transaction(self, ot):
        return False

    def extract(self, file, existing_entries=None):
        self.initialize(file)
        counter = itertools.count()
        new_entries = []
        config = self.config

        self.read_file(file)
        for ot in self.get_transactions():
            if self.skip_transaction(ot):
                continue
            metadata = data.new_metadata(file.name, next(counter))
            # metadata['type'] = ot.type # Optional metadata, useful for debugging #TODO
            metadata.update(self.build_metadata(file,
                                                metatype='transaction',
                                                data={'transaction': ot}))

            # description fields: With OFX, ot.payee tends to be the "main" description field,
            # while ot.memo is optional
            #
            # With Beancount, the grammar is (payee, narration). payee is optional, narration is
            # mandatory. This is a bit unintuitive. In addition, smart_importer relies on
            # narration, so keeping the order unchanged in the call below is important.

            # Build transaction entry
            entry = data.Transaction(metadata, ot.date.date(), self.FLAG,
                                     self.get_narration(ot), self.get_payee(ot),
                                     data.EMPTY_SET, data.EMPTY_SET, [])
            data.create_simple_posting(entry, config['main_account'], ot.amount, self.currency)

            # TODO: Commented out so smart_importer can fill this in
            # target_acct = self.get_target_acct(ot)
            # data.create_simple_posting(entry, target_acct, None, None)

            new_entries.append(entry)

        new_entries += self.extract_balance(file, counter)
        new_entries += self.extract_custom_entries(file, counter)

        return new_entries
