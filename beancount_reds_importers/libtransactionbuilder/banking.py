"""Generic banking importer for beancount."""

import itertools
from collections import namedtuple
from beancount.core import data
from beancount.core import amount
from beancount.ingest import importer
from beancount_reds_importers.libtransactionbuilder import common, transactionbuilder


Balance = namedtuple('Balance', ['date', 'amount', 'currency'])


class Importer(importer.ImporterProtocol, transactionbuilder.TransactionBuilder):
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

    @staticmethod
    def fields_contain_data(ot, fields):
        return all(hasattr(ot, f) and getattr(ot, f) for f in fields)

    def get_main_account(self, ot):
        """Can be overridden by importer"""
        return self.config['main_account']

    def get_target_account(self, ot):
        """Can be overridden by importer"""
        return self.config.get('target_account')

    # --------------------------------------------------------------------------------

    def extract_balance(self, file, counter):
        entries = []

        for bal in self.get_balance_statement(file=file):
            if bal:
                metadata = data.new_metadata(file.name, next(counter))
                metadata.update(self.build_metadata(file, metatype='balance'))
                balance_entry = data.Balance(metadata, bal.date, self.config['main_account'],
                                             amount.Amount(bal.amount, self.get_currency(bal)),
                                             None, None)
                entries.append(balance_entry)
        return entries

    def extract_custom_entries(self, file, counter):
        """For custom importers to override"""
        return []

    def get_currency(self, ot):
        try:
            return ot.currency
        except AttributeError:
            return self.currency

    def extract(self, file, existing_entries=None):
        self.initialize(file)
        counter = itertools.count()
        new_entries = []

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
            # Banking transactions might include foreign currency transactions. TODO: figure out
            # how ofx handles this and use the same interface for csv and other files
            entry = data.Transaction(
                    meta=metadata,
                    date=ot.date.date(),
                    flag=self.FLAG,
                    # payee and narration are switched. See the preceding note
                    payee=self.get_narration(ot),
                    narration=self.get_payee(ot),
                    tags=self.get_tags(ot),
                    links=data.EMPTY_SET,
                    postings=[])

            main_account = self.get_main_account(ot)

            if self.fields_contain_data(ot, ['foreign_amount', 'foreign_currency']):
                common.create_simple_posting_with_price(entry, main_account,
                                                        ot.amount, self.get_currency(ot),
                                                        ot.foreign_amount, ot.foreign_currency)
            else:
                data.create_simple_posting(entry, main_account, ot.amount, self.get_currency(ot))

            # smart_importer can fill this in if the importer doesn't override self.get_target_acct()
            target_acct = self.get_target_account(ot)
            if target_acct:
                data.create_simple_posting(entry, target_acct, None, None)

            new_entries.append(entry)

        new_entries += self.extract_balance(file, counter)
        new_entries += self.extract_custom_entries(file, counter)

        return new_entries
