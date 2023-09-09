"""United Overseas Bank, Bank account .csv importer."""

from beancount_reds_importers.libreader import xlsreader
from beancount_reds_importers.libtransactionbuilder import banking
import re
from beancount.core.number import D


class Importer(xlsreader.Importer, banking.Importer):
    IMPORTER_NAME = __doc__

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'ACC_TXN_History[0-9]*'
        self.header_identifier = self.config.get('custom_header', 'United Overseas Bank Limited.*Account Type:Uniplus Account')
        self.column_labels_line = 'Transaction Date,Transaction Description,Withdrawal,Deposit,Available Balance'
        self.date_format = '%d %b %Y'
        self.header_map = {
            'Transaction Date': 'date',
            'Transaction Description': 'payee',
            'Available Balance': 'balance'
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []

    def deep_identify(self, file):
        account_number = self.config.get('account_number', '')
        return re.match(self.header_identifier, file.head()) and \
            account_number in file.head()

    # TODO: move these into utils, since this is probably a common operation
    def prepare_table(self, rdr):
        # Remove carriage returns in description
        rdr = rdr.convert('Transaction Description', lambda x: x.replace('\n', ' '))

        def Ds(x):
            return D(str(x))
        rdr = rdr.addfield('amount',
                           lambda x: -1 * Ds(x['Withdrawal']) if x['Withdrawal'] != 0 else Ds(x['Deposit']))
        rdr = rdr.addfield('memo', lambda x: '')
        return rdr

    def prepare_raw_file(self, rdr):
        # Strip tabs and spaces around each field in the entire file
        rdr = rdr.convertall(lambda x: x.strip(' \t') if isinstance(x, str) else x)

        # Delete empty rows
        rdr = rdr.select(lambda x: any([i != '' for i in x]))

        return rdr

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""
        date = self.get_balance_assertion_date()
        if date:
            row = self.rdr.namedtuples()[0]
            # Get currency from input file
            currency = self.get_row_by_label(file, 'Account Number:')[2]

            yield banking.Balance(date, D(str(row.balance)), currency)
