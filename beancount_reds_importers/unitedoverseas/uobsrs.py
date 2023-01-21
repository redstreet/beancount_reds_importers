"""UOB SRS importer."""

from beancount_reds_importers.libreader import xlsreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(xlsreader.Importer, banking.Importer):
    IMPORTER_NAME = 'UOB SRS'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'SRS_TXN_History[0-9]*'
        self.header_identifier = 'United Overseas Bank Limited.*Account Type:SRS Account'
        self.column_labels_line = 'Transaction Date,Transaction Description,Withdrawal,Deposit'
        self.date_format = '%Y%m%d'
        self.header_map = {
            'Transaction Date': 'date',
            'Transaction Description': 'payee',
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []

    def prepare_raw_columns(self, rdr):
        # Remove carriage returns in description
        rdr = rdr.convert('Transaction Description', lambda x: x.replace('\n', ' '))

        rdr = rdr.addfield('amount',
                           lambda x: -1 * x['Withdrawal'] if x['Withdrawal'] != '0' else x['Deposit'])
        rdr = rdr.addfield('memo', lambda x: '')
        return rdr

    def prepare_raw_rows(self, rdr):
        # Strip tabs and spaces around each field in the entire file
        rdr = rdr.convertall(lambda x: x.strip(' \t') if isinstance(x, str) else x)

        # Delete empty rows
        rdr = rdr.select(lambda x: any([i != '' for i in x]))

        return rdr
