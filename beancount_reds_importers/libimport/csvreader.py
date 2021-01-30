"""csv importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import datetime
import re
from beancount.ingest import importer
from beancount.core.number import D
import petl as etl


class Importer(importer.ImporterProtocol):
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
            return re.sub("[^0-9\.]", "", x)
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
            rdr = rdr.skip(self.skip_head_rows)
            rdr = rdr.head(len(rdr) - self.skip_tail_rows - 1)
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
