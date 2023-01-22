"""SCB Credit .csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking
from collections import namedtuple
import datetime
import petl as etl
from beancount.core.number import D


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = 'SCB Card CSV'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'CardTransactions[0-9]*'
        self.header_identifier = 'PRIORITY BANKING VISA INFINITE CARD'
        self.column_labels_line = 'Date,DESCRIPTION,Foreign Currency Amount,SGD Amount'
        self.date_format = '%d/%m/%Y'
        self.skip_tail_rows = 6
        self.skip_comments = '# '
        self.header_map = {
            "Date":           "date",
            "DESCRIPTION":    "payee",
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []

    # TODO: internationalize the string to number conversion
    # TODO: move into utils, since this is probably a common operation
    def prepare_table(self, rdr):
        # split Foreign Currency Amount into two columns
        def safesplit(a, minlength=2):
            retval = a.split(' ')
            if len(retval) >= minlength:
                return retval
            return ['', '']

        # Uncomment after enabling total price conversions in banking.py
        # rdr = etl.addfield(rdr, 'foreign_amount',
        #                    lambda row: D(safesplit(row['Foreign Currency Amount'])[1]))
        # rdr = etl.addfield(rdr, 'foreign_currency',
        #                    lambda row: safesplit(row['Foreign Currency Amount'])[0])
        rdr = rdr.cutout('Foreign Currency Amount')

        # parse SGD Amount, change DR into -ve, remove SGD, change to amount
        def parse_sgd_amount(s):
            currency, amount, drcr = s.split()
            if drcr == 'DR':
                amount = '-' + amount
            return amount, currency
        rdr = etl.addfield(rdr, 'amount', lambda row: parse_sgd_amount(row['SGD Amount'])[0])
        rdr = etl.addfield(rdr, 'currency', lambda row: parse_sgd_amount(row['SGD Amount'])[1])
        rdr = rdr.cutout('SGD Amount')

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
        max_date = self.get_max_transaction_date()
        if max_date:
            rdr = self.read_raw(file)
            rdr = self.prepare_raw_file(rdr)
            _, currency, amount, _ = rdr.select(lambda r: r[0] == 'Current Balance')[1]
            units, debitcredit = amount.split()
            if debitcredit != 'CR':
                units = '-' + units

            date = max_date + datetime.timedelta(days=1)
            Balance = namedtuple('Balance', ['date', 'amount', 'currency'])

            yield Balance(date, D(units), currency)
