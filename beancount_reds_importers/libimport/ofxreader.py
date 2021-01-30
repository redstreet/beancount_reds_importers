"""Ofx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

from beancount.ingest import importer
from ofxparse import OfxParser
from beancount_reds_importers.libimport import reader


class Importer(reader.Reader, importer.ImporterProtocol):
    FILE_EXT = 'fx'

    def initialize_reader(self, file):
        if not self.initialized_reader:
            self.ofx = OfxParser.parse(open(file.name))
            self.ofx_account = None
            for acc in self.ofx.accounts:
                # account identifying info fieldname varies across institutions
                if self.match_account_number(getattr(acc, self.account_number_field),
                                             self.config['account_number']):
                    self.ofx_account = acc
                    self.reader_ready = True
            if self.reader_ready:
                self.currency = self.ofx_account.statement.currency.upper()
                self.includes_balances = True
            self.initialized_reader = True

    def match_account_number(self, file_account, config_account):
        """We don't want to store entire credit card numbers in our config, so just use the last 4"""
        return file_account == config_account

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
