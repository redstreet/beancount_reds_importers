""" Schwab CSV Positions importer.

Note: Schwab "Positions" CSV is not the same as Schwab "Balances" CSV."""

import datetime
import re
from beancount.core.number import D
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, csvreader.Importer):
    IMPORTER_NAME = "Schwab Brokerage Positions CSV"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*-Positions-'
        self.header_identifier = '["]+Positions for account'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%Y/%m/%d'
        self.funds_db_txt = 'funds_by_ticker'
        self.column_labels_line = '"Symbol","Description","Quantity","Price","Price Change %","Price Change $","Market Value","Day Change %","Day Change $","Cost Basis","Gain/Loss %","Gain/Loss $","Ratings","Reinvest Dividends?","Capital Gains?","% Of Account","Security Type"'  # noqa: #501
        self.header_map = {
            "Description": 'memo',
            "Symbol":      'security',
            "Quantity":    'units',
            "Price":       'unit_price',
            }
        self.skip_transaction_types = []

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
        self.read_file(file)
        return self.date.date()

    def get_max_transaction_date(self):
        return self.date.date()

    def prepare_raw_file(self, rdr):
        # first row has date
        d = rdr[0][0].rsplit(' ', 1)[1]
        self.date = datetime.datetime.strptime(d, self.date_format)
        return rdr

    def get_transactions(self):
        """No transactions, this is a file with positions only (balance positions)"""
        return []

    def prepare_table(self, rdr):
        # Delete uninteresting columns
        rdr = rdr.cut(list(self.header_map.keys()))
        return rdr

    def get_balance_positions(self):
        for pos in self.rdr.namedtuples():
            if pos.memo != '--':
                yield pos
