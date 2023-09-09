""" Schwab Checking .csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = 'Schwab Checking account CSV'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*_Checking_Transactions_'
        self.header_identifier = '"Transactions  for Checking account.*'
        self.column_labels_line = '"Date","Type","Check #","Description","Withdrawal (-)","Deposit (+)","RunningBalance"'
        self.date_format = '%m/%d/%Y'
        self.skip_comments = '# '
        self.header_map = {
            "Date":           "date",
            "Type":           "type",
            "Check #":        "checknum",
            "Description":    "payee",
            "Withdrawal (-)": "withdrawal",
            "Deposit (+)":    "deposit",
            "RunningBalance": "balance"
        }
        self.transaction_type_map = {
            "INTADJUST": 'income',
            "TRANSFER": 'transfer',
            "ACH": 'transfer'
        }
        self.skip_transaction_types = ['Journal']

    def prepare_table(self, rdr):
        if self.config.get('include_pending', False):
            rows_to_remove = ['Pending Transactions', 'Posted Transactions', 'Total Pending Check']
            rdr = rdr.select(lambda x: not any(x[0].startswith(i) for i in rows_to_remove))
            # TODO: this doesn't work with generating balance assertions: pending transactions
            # don't include balance assertion data. So what we need to do is generate a balance
            # assertion at the end of posted transactions. This has not yet been done.
        else:
            # There are two sub-tables: pending and posted transactions. Skip pending transactions
            rdr = self.skip_until_row_contains(rdr, "Posted Transactions")

        rdr = rdr.addfield('amount',
                           lambda x: "-" + x['Withdrawal (-)'] if x['Withdrawal (-)'] != '' else x['Deposit (+)'])
        rdr = rdr.addfield('memo', lambda x: '')
        return rdr

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""

        date = self.get_balance_assertion_date()
        if date:
            yield banking.Balance(date, self.rdr.namedtuples()[0].balance, self.currency)
