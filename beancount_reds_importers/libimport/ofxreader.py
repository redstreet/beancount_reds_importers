"""Ofx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import ntpath
from beancount.ingest import importer
from ofxparse import OfxParser


class Importer(importer.ImporterProtocol):
    def initialize_reader(self, file):
        if not self.initialized_reader:
            self.ofx = OfxParser.parse(open(file.name))
            self.ofx_account = None
            for acc in self.ofx.accounts:
                # account identifying info fieldname varies across institutions
                if getattr(acc, self.account_number_field) == self.config['account_number']:
                    self.ofx_account = acc
                    self.reader_ready = True
            if self.reader_ready:
                self.currency = self.ofx_account.statement.currency.upper()
                self.includes_balances = True
            self.initialized_reader = True

    def identify(self, file):
        # quick check to filter out files that are not qfx/ofx
        if not file.name.lower().endswith('fx'):
            return False
        self.custom_init()
        if self.filename_identifier_substring not in file.name:
            return False
        self.initialize_reader(file)
        return self.reader_ready

    def file_name(self, file):
        return 'account-{}'.format(ntpath.basename(file.name))

    def file_account(self, _):
        return self.config['main_account']

    def file_date(self, file):
        "Get the maximum date from the file."
        self.ofx_account.statement.end_date

    def read_file(self, file):
        pass

    def get_transactions(self):
        for ot in self.ofx_account.statement.transactions:
            yield ot

    def get_balance_positions(self):
        for pos in self.ofx_account.statement.positions:
            yield pos

    def get_available_cash(self):
        return self.ofx_account.statement.available_cash
