""" Schwab csv importer."""

import datetime
import re
from beancount.core.number import D
from beancount_reds_importers.libreader import csv_multitable_reader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, csv_multitable_reader.Importer):
    IMPORTER_NAME = 'Schwab Brokerage Balances CSV'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*_Balances_'
        self.header_identifier = 'Balances  for account'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.header_map = {
            "Description": 'memo',
            "Symbol":      'security',
            "Quantity":    'units',
            "Price":       'unit_price',
            }

    def prepare_table(self, rdr):
        return rdr

    def convert_columns(self, rdr):
        # fixup decimals
        decimals = ['units']
        for i in decimals:
            rdr = rdr.convert(i, D)

        # fixup currencies
        def remove_non_numeric(x):
            return re.sub(r'[^0-9\.]', "", x)  # noqa: W605
        currencies = ['unit_price']
        for i in currencies:
            rdr = rdr.convert(i, remove_non_numeric)
            rdr = rdr.convert(i, D)

        return rdr

    def file_date(self, file):
        return self.date.date()

    def get_max_transaction_date(self):
        return self.date.date()

    def prepare_tables(self):
        # first row has date
        d = self.raw_rdr[0][0].rsplit(' ', 1)[1]
        self.date = datetime.datetime.strptime(d, self.date_format)

        for section, table in self.alltables.items():
            if section in self.config['section_headers']:
                table = table.rename(self.header_map)
                table = self.convert_columns(table)
                table = table.cut('memo', 'security', 'units', 'unit_price')
                table = table.selectne('memo', '--')  # we don't need total rows
                table = table.addfield('date', self.date)
                self.alltables[section] = table

    def get_balance_positions(self):
        for section in self.config['section_headers']:
            yield from self.alltables[section].namedtuples()
