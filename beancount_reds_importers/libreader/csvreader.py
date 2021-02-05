"""csv importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import datetime
import re
import traceback
from beancount.ingest import importer
from beancount.core.number import D
import petl as etl
from beancount_reds_importers.libreader import reader

# This csv reader uses petl to read a .csv into a table for maniupulation. The output of this reader is a list
# of namedtuples corresponding roughly to ofx transactions. The following steps achieve this. When writing
# your own importer, you only should need to:
# - override prepare_raw_columns()
#   - provide the following mappings, which correspond to the input file format of a given institution:
#       - header_map
#       - transaction_type_map
#       - skip_transaction_types
# See the schwab_csv importer for an example
#
# The steps this importer follow are:
# - read csv into petl table
# - skip header and footer rows (configurable)
# - prepare_raw_columns: an overridable method to help get the raw table in shape. As an example, the schwab
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
    FILE_EXT = 'csv'

    def initialize_reader(self, file):
        if not self.initialized_reader:
            self.reader_ready = re.match(self.header_identifier, file.head())
            if self.reader_ready:
                # TODO: move out elsewhere?
                # self.currency = self.ofx_account.statement.currency.upper()
                self.currency = 'USD'  # TODO
                self.includes_balances = False
            self.initialized_reader = True
            self.file_read_done = False

    def file_date(self, file):
        "Get the maximum date from the file."
        self.read_file(file)
        return max(ot.date for ot in self.get_transactions()).date()

    def prepare_raw_columns(self, rdr):
        return rdr

    def convert_columns(self, rdr):
        # convert data in transaction types column
        rdr = rdr.convert('type', self.transaction_type_map)

        # fixup decimals
        decimals = ['units']
        for i in decimals:
            rdr = rdr.convert(i, D)

        # fixup currencies
        def remove_non_numeric(x):
            return re.sub("[^0-9\.]", "", x)  # noqa: W605
        currencies = ['unit_price', 'fees', 'total', 'amount']
        for i in currencies:
            rdr = rdr.convert(i, remove_non_numeric)
            rdr = rdr.convert(i, D)

        # fixup dates
        def convert_date(d):
            return datetime.datetime.strptime(d, '%m/%d/%Y')
        dates = ['date', 'tradeDate']
        for i in dates:
            rdr = rdr.convert(i, convert_date)

        return rdr

    def read_file(self, file):
        if not self.file_read_done:
            rdr = etl.fromcsv(file.name)
            rdr = rdr.skip(getattr(self, 'skip_head_rows', 0))                 # chop unwanted header rows
            rdr = rdr.head(len(rdr) - getattr(self, 'skip_tail_rows', 0) - 1)  # chop unwanted footer rows
            rdr = self.prepare_raw_columns(rdr)
            rdr = rdr.rename(self.header_map)
            rdr = self.convert_columns(rdr)
            self.rdr = rdr
            self.file_read_done = True

    def get_transactions(self):
        for ot in self.rdr.namedtuples():
            if self.skip_transaction(ot):
                continue
            yield ot

    def get_balance_positions(self):
        raise "Not supported"

    def get_available_cash(self):
        raise "Not supported"

    # TOOD: custom, overridable
    def skip_transaction(self, row):
        return row.type in self.skip_transaction_types

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
            return False

        return date
