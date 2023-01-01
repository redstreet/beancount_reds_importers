"""Ofx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import datetime
import ofxparse
from collections import namedtuple
from beancount.ingest import importer
from beancount_reds_importers.libreader import reader


class Importer(reader.Reader, importer.ImporterProtocol):
    FILE_EXT = 'fx'

    def initialize_reader(self, file):
        if getattr(self, 'file', None) != file:
            self.file = file
            self.ofx_account = None
            self.reader_ready = False
            try:
                self.ofx = ofxparse.OfxParser.parse(open(file.name))
            except ofxparse.OfxParserException:
                return
            for acc in self.ofx.accounts:
                # account identifying info fieldname varies across institutions
                # self.acc_num_field can be overridden in self.custom_init() if needed
                acc_num_field = getattr(self, 'account_number_field', 'account_id')
                if self.match_account_number(getattr(acc, acc_num_field),
                                             self.config['account_number']):
                    self.ofx_account = acc
                    self.reader_ready = True
            if self.reader_ready:
                self.currency = self.ofx_account.statement.currency.upper()

    def match_account_number(self, file_account, config_account):
        """We many not want to store entire credit card numbers in our config. Or a given ofx may not contain
        the full account number. Override this method to handle these cases."""
        return file_account == config_account

    def file_date(self, file):
        "Get the maximum date from the file."
        return self.ofx_account.statement.end_date

    def read_file(self, file):
        pass

    def get_transactions(self):
        yield from self.ofx_account.statement.transactions

    def get_balance_statement(self):
        if not hasattr(self.ofx_account.statement, 'balance'):
            return []
        date = self.get_max_transaction_date()
        if date:
            date += datetime.timedelta(days=1)  # See comment in get_max_transaction_date() for explanation
            Balance = namedtuple('Balance', ['date', 'amount'])
            yield Balance(date, self.ofx_account.statement.balance)

    def get_balance_positions(self):
        if not hasattr(self.ofx_account.statement, 'positions'):
            return []
        yield from self.ofx_account.statement.positions

    def get_available_cash(self):
        return getattr(self.ofx_account.statement, 'available_cash', None)

    def get_max_transaction_date(self):
        try:
            # date = self.ofx_account.statement.end_date.date() # this is the date of ofx download
            # we find the last transaction's date. If we use the ofx download date (if our source is ofx), we
            # could end up with a gap in time between the last transaction's date and balance assertion.
            # Pending (but not yet downloaded) transactions in this gap will get downloaded the next time we
            # do a download in the future, and cause the balance assertions to be invalid.

            date = max(ot.tradeDate if hasattr(ot, 'tradeDate') else ot.date
                       for ot in self.get_transactions()).date()
        except TypeError:
            return False
        except ValueError:
            return False
        return date
