"""csv importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import datetime
import re
import traceback
from beancount.ingest import importer
from beancount.core.number import D
import petl as etl
from beancount_reds_importers.libreader import reader
import sys

# This csv reader uses petl to read a .csv into a table for maniupulation. The output of this reader is a list
# of namedtuples corresponding roughly to ofx transactions. The following steps achieve this. When writing
# your own importer, you only should need to:
# - override prepare_table()
#   - provide the following mappings, which correspond to the input file format of a given institution:
#       - header_map
#       - transaction_type_map
#       - skip_transaction_types
# See the schwab_csv importer for an example
#
# The steps this importer follow are:
# - read csv into petl table
# - skip header and footer rows (configurable)
# - prepare_table: an overridable method to help get the raw table in shape. As an example, the schwab
#   importer does the following
#      - rdr.cutout('') # remove the last column, which is empty
#      - for rows with interest, the date column contains text such as: '11/16/2018 as of 11/15/2018'. We
#        convert these into a regular parseable date: '11/16/2018'
#      - add a 'tradeDate' column, which is a copy of the 'Date' column, to correspond to the importer API
#      - add a a 'total' column, which is a copy of the 'Amount' column, to correspond to the importer API
# - rename columns: columns headers are renamed to standardize them to the importer API, using a supplied
#   dictionary. For the included schwab importer, that looks like:
#             "Action":      'type',
#             "Date":        'date',
#             "tradeDate":   'tradeDate',
#             "Description": 'memo',
#             "Symbol":      'security',
#             etc.
#
# - convert_columns: this fixes up the actual data in each column. The base class does the following:
#   - map types to standard types. The standard types that the importer-API uses are loosely based on ofx
#     standards. For example, the schwab importer needs this mapping:
#
#         self.transaction_type_map = {
#             'Bank Interest':      'income',
#             'Buy':                'buystock',
#             'Cash Dividend':      'dividends',
#             'MoneyLink Transfer': 'transfer',
#             'Reinvest Dividend':  'dividends',
#             'Reinvest Shares':    'buystock',
#             'Sell':               'sellstock',
#             }
#
#   - numbers are parsed from string and convered into Decimal type. Non-numeric characters like '$' are removed.
#   - dates are parsed and converted into datetime type.
# - The table is now ready for use by the importer. petl makes each row available via namedtuples


class Importer(reader.Reader, importer.ImporterProtocol):
    FILE_EXTS = ['csv']

    def initialize_reader(self, file):
        if getattr(self, 'file', None) != file:
            self.file = file
            self.reader_ready = self.deep_identify(file)
            if self.reader_ready:
                self.file_read_done = False
            # else:
            #     print("header_identifier failed---------------:")
            #     print(self.header_identifier, file.head())

    def deep_identify(self, file):
        return re.match(self.header_identifier, file.head())

    def file_date(self, file):
        "Get the maximum date from the file."
        self.initialize(file)  # self.date_format gets set via this
        self.read_file(file)
        return max(ot.date for ot in self.get_transactions()).date()

    def prepare_table(self, rdr):
        return rdr

    def prepare_raw_file(self, rdr):
        return rdr

    def fix_column_names(self, rdr):
        header_map = {k: re.sub("[-/ ]", "_", k) for k in rdr.header()}
        rdr = rdr.rename(header_map)
        return rdr

    def prepare_processed_table(self, rdr):
        return rdr

    def convert_columns(self, rdr):
        # convert data in transaction types column
        if 'type' in rdr.header():
            rdr = rdr.convert('type', self.transaction_type_map)

        # fixup decimals
        decimals = ['units']
        for i in decimals:
            if i in rdr.header():
                rdr = rdr.convert(i, D)

        # fixup currencies
        def remove_non_numeric(x):
            return re.sub(r'[^0-9\.-]', "", str(x).strip())  # noqa: W605
        currencies = getattr(self, 'currency_fields', []) + ['unit_price', 'fees', 'total', 'amount', 'balance']
        for i in currencies:
            if i in rdr.header():
                rdr = rdr.convert(i, remove_non_numeric)
                rdr = rdr.convert(i, D)

        # fixup dates
        def convert_date(d):
            return datetime.datetime.strptime(d, self.date_format)
        dates = getattr(self, 'date_fields', []) + ['date', 'tradeDate', 'settleDate']
        for i in dates:
            if i in rdr.header():
                rdr = rdr.convert(i, convert_date)

        return rdr

    def read_raw(self, file):
        return etl.fromcsv(file.name)

    def skip_until_main_table(self, rdr, col_labels=None):
        """Skip csv lines until the header line is found."""
        # TODO: convert this into an 'extract_table()' method that handles the tail as well
        if not col_labels:
            if hasattr(self, 'column_labels_line'):
                col_labels = self.column_labels_line.replace('"', '').split(',')
            else:
                return rdr
        skip = None
        for n, r in enumerate(rdr):
            # We only check if each element in col_labels shows up in the line in the file, and not
            # the other way around. This allows additional fields to show up anywhere, case the csv
            # format changes
            if all(i in list(r) for i in col_labels):
                skip = n
        if skip is None:
            print("Error: expected columns not found:")
            print(col_labels)
            sys.exit(1)
        return rdr.skip(skip)

    def extract_table_with_header(self, rdr, col_labels=None):
        rdr = self.skip_until_main_table(rdr, col_labels)
        nrows = len(rdr)
        for (n, r) in enumerate(rdr):
            if not r or all(i == '' for i in r):
                # blank line, terminate
                nrows = n - 1
                break
        rdr = rdr.head(nrows)
        return rdr

    def skip_until_row_contains(self, rdr, value):
        start = None
        for n, r in enumerate(rdr):
            if value in r[0]:
                start = n
        if start is None:
            print(f'Error: table is not as expected. "{value}" row not found.')
            sys.exit(1)
        return rdr.rowslice(start, len(rdr))

    def read_file(self, file):
        if not self.file_read_done:

            # read file
            rdr = self.read_raw(file)
            rdr = self.prepare_raw_file(rdr)

            # extract main table
            rdr = rdr.skip(getattr(self, 'skip_head_rows', 0))                 # chop unwanted header rows
            rdr = rdr.head(len(rdr) - getattr(self, 'skip_tail_rows', 0) - 1)  # chop unwanted footer rows
            rdr = self.extract_table_with_header(rdr)
            if hasattr(self, 'skip_comments'):
                rdr = rdr.skipcomments(self.skip_comments)
            rdr = rdr.rowslice(getattr(self, 'skip_data_rows', 0), None)
            rdr = self.prepare_table(rdr)

            # process table
            rdr = rdr.rename(self.header_map)
            rdr = self.convert_columns(rdr)
            rdr = self.fix_column_names(rdr)
            rdr = self.prepare_processed_table(rdr)
            self.rdr = rdr
            self.ifile = file
            self.file_read_done = True

    def get_transactions(self):
        for ot in self.rdr.namedtuples():
            if self.skip_transaction(ot):
                continue
            yield ot

    def get_available_cash(self, settlement_fund_balance=0):
        return None

    # TOOD: custom, overridable
    def skip_transaction(self, row):
        return getattr(row, 'type', 'NO_TYPE') in self.skip_transaction_types

    def get_balance_assertion_date(self):
        """
        We add an additional day to get_max_transaction_date(), since Beancount balance
        assertions are defined to occur on the beginning of the assertion date.
        """
        return self.get_max_transaction_date() + datetime.timedelta(days=1)

    def get_max_transaction_date(self):
        try:
            # date = self.ofx_account.statement.end_date.date() # this is the date of ofx download
            # we find the last transaction's date. If we use the ofx download date (if our source is ofx), we
            # could end up with a gap in time between the last transaction's date and balance assertion.
            # Pending (but not yet downloaded) transactions in this gap will get downloaded the next time we
            # do a download in the future, and cause the balance assertions to be invalid.

            # TODO: clean this up. this probably suffices:
            # return max(ot.date for ot in self.get_transactions()).date()
            date = max(ot.tradeDate if hasattr(ot, 'tradeDate') else ot.date
                       for ot in self.get_transactions()).date()
        except Exception as err:
            print("ERROR: no end_date. SKIPPING input.")
            traceback.print_tb(err.__traceback__)
            return None

        return date

    def get_row_by_label(self, file, label):
        """Return a row from file where the first cell (column) matches label. This is a common
        operation in csv files, and is thus provided here as a utility. Eg:
           "Account Statement:,123456,EUR"
        """
        # Read from scratch, as we don't want to throw away headers or footers, which is where our
        # label is likely to be found
        rdr = self.read_raw(file)
        rdr = self.prepare_raw_file(rdr)
        return rdr.select(lambda r: r[0] == label)[1]
