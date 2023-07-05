"""UOB SRS importer."""

import re
from beancount_reds_importers.libreader import xlsreader
from beancount_reds_importers.libtransactionbuilder import banking
from beancount.core.number import D


class Importer(xlsreader.Importer, banking.Importer):
    IMPORTER_NAME = 'UOB SRS'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'SRS_TXN_History[0-9]*'
        self.header_identifier = self.config.get('custom_header', 'United Overseas Bank Limited.*Account Type:SRS Account')
        self.column_labels_line = 'Transaction Date,Transaction Description,Withdrawal,Deposit'
        self.date_format = '%Y%m%d'
        self.header_map = {
            'Transaction Date': 'date',
            'Transaction Description': 'payee',
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []

    def deep_identify(self, file):
        account_number = self.config.get('account_number', '')
        return re.match(self.header_identifier, file.head()) and \
            account_number in file.head()

    def prepare_table(self, rdr):
        # Remove carriage returns in description
        rdr = rdr.convert('Transaction Description', lambda x: x.replace('\n', ' '))

        def Ds(x):
            return D(str(x))
        rdr = rdr.addfield('amount',
                           lambda x: -1 * Ds(x['Withdrawal']) if x['Withdrawal'] != '' else Ds(x['Deposit']))
        rdr = rdr.addfield('memo', lambda x: '')
        return rdr

    def prepare_raw_file(self, rdr):
        # Strip tabs and spaces around each field in the entire file
        rdr = rdr.convertall(lambda x: x.strip(' \t') if isinstance(x, str) else x)

        # Delete empty rows
        rdr = rdr.select(lambda x: any([i != '' for i in x]))

        return rdr
