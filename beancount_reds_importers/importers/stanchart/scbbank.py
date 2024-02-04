"""SCB Banking .csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking
import re
from beancount.core.number import D


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = 'SCB Banking Account CSV'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'AccountTransactions[0-9]*'
        self.header_identifier = self.config.get('custom_header', 'Account transactions shown:')
        self.column_labels_line = 'Date,Transaction,Currency,Deposit,Withdrawal,Running Balance,SGD Equivalent Balance'
        self.balance_column_labels_line = 'Account Name,Account Number,Currency,Current Balance,Available Balance'
        self.date_format = '%d/%m/%Y'
        self.skip_tail_rows = 0
        self.skip_comments = '# '
        self.header_map = {
            "Date":            "date",
            "Transaction":     "payee",
            "Currency":        "currency",
            "Withdrawal":      "withdrawal",
            "Deposit":         "deposit",
            "Running Balance": "balance_running",
            "SGD Equivalent Balance": "balance",
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []

    def deep_identify(self, file):
        account_number = self.config.get('account_number', '')
        return re.match(self.header_identifier, file.head()) and \
            account_number in file.head()

    # TODO: move into utils, since this is probably a common operation
    def prepare_table(self, rdr):
        rdr = rdr.addfield('amount',
                           lambda x: "-" + x['Withdrawal'] if x['Withdrawal'] != '' else x['Deposit'])
        rdr = rdr.addfield('memo', lambda x: '')
        return rdr

    def prepare_raw_file(self, rdr):
        # Strip tabs and spaces around each field in the entire file
        rdr = rdr.convertall(lambda x: x.strip(' \t') if isinstance(x, str) else x)

        return rdr

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""
        date = self.get_balance_assertion_date()
        if date:
            rdr = self.read_raw(file)
            rdr = self.prepare_raw_file(rdr)
            col_labels = self.balance_column_labels_line.split(',')
            rdr = self.extract_table_with_header(rdr, col_labels)

            header_map = {k: k.replace(' ', '_') for k in col_labels}
            rdr = rdr.rename(header_map)

            while '' in rdr.header():
                rdr = rdr.cutout('')

            row = rdr.namedtuples()[0]
            amount = row.Current_Balance
            units, debitcredit = amount.split()
            if debitcredit != 'CR':
                units = '-' + units
            yield banking.Balance(date, D(units), row.Currency)
