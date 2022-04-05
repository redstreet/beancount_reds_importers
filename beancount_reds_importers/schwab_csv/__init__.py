""" Schwab csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, csvreader.Importer):
    IMPORTER_NAME = 'Schwab Brokerage CSV'
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_identifier_substring = self.config.get('filename_identifier_substring', '_Transactions_')
        self.header_identifier = self.config.get('header_identifier', '"Transactions  for account.*')
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.skip_head_rows = 1
        self.skip_tail_rows = 1
        self.header_map = {
            "Action":      'type',
            "Date":        'date',
            "tradeDate":   'tradeDate',
            "Description": 'memo',
            "Symbol":      'security',
            "Quantity":    'units',
            "Price":       'unit_price',
            "Amount":      'amount',
            "total":       'total',
            "Fees & Comm": 'fees',
            }
        self.transaction_type_map = {
            'Bank Interest':                'income',
            'Bank Transfer':                'transfer',
            'Buy':                          'buystock',
            'Reinvestment Adj':             'buystock',
            'Cash Dividend':                'dividends',
            'Div Adjustment':               'dividends',
            'Long Term Cap Gain Reinvest':  'capgains_lt',
            'Misc Credits':                 'transfer',
            'MoneyLink Deposit':            'transfer',
            'MoneyLink Transfer':           'transfer',
            'Pr Yr Div Reinvest':           'dividends',
            'Reinvest Dividend':            'dividends',
            'Reinvest Shares':              'buystock',
            'Sell':                         'sellstock',
            'Short Term Cap Gain Reinvest': 'capgains_st',
            'Wire Funds Received':          'transfer',
            'Funds Received':               'transfer',
            }
        self.skip_transaction_types = ['Journal']

    def prepare_raw_columns(self, rdr):
        rdr = rdr.cutout('')  # clean up last column

        def cleanup_date(d):
            """'11/16/2018 as of 11/15/2018' --> '11/16/2018'"""
            return d.split(' ', 1)[0]
        rdr = rdr.convert('Date', cleanup_date)
        rdr = rdr.addfield('tradeDate', lambda x: x['Date'])
        rdr = rdr.addfield('total', lambda x: x['Amount'])
        return rdr
