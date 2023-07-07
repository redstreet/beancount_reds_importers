""" Schwab Brokerage .csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(csvreader.Importer, investments.Importer):
    IMPORTER_NAME = 'Schwab Brokerage CSV'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*_Transactions_'
        self.header_identifier = '"Transactions  for account.*'
        self.column_labels_line = '"Date","Action","Symbol","Description","Quantity","Price","Fees & Comm","Amount"'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.get_payee = lambda ot: ot.Action
        self.header_map = {
            "Date":        'date',
            "Description": 'memo',
            "Symbol":      'security',
            "Quantity":    'units',
            "Price":       'unit_price',
            "Amount":      'amount',
            # "tradeDate":   'tradeDate',
            # "total":       'total',
            "Fees & Comm": 'fees',
            }
        self.transaction_type_map = {
            'Bank Interest':                'income',
            'Bank Transfer':                'cash',
            'Buy':                          'buystock',
            'Reinvestment Adj':             'buystock',
            'Div Adjustment':               'dividends',
            'Long Term Cap Gain Reinvest':  'capgainsd_lt',
            'Misc Credits':                 'cash',
            'MoneyLink Deposit':            'cash',
            'MoneyLink Transfer':           'cash',
            'Pr Yr Div Reinvest':           'dividends',
            'Reinvest Dividend':            'dividends',
            'Qualified Dividend':           'dividends',
            'Cash Dividend':                'dividends',
            'Reinvest Shares':              'buystock',
            'Sell':                         'sellstock',
            'Short Term Cap Gain Reinvest': 'capgainsd_st',
            'Wire Funds Received':          'cash',
            'Wire Received':                'cash',
            'Funds Received':               'cash',
            'Stock Split':                  'cash',
            'Cash In Lieu':                 'cash',
            }

    def skip_transaction(self, ot):
        return ot.type in ['', 'Journal']

    def prepare_table(self, rdr):
        if '' in rdr.fieldnames():
            rdr = rdr.cutout('')  # clean up last column

        def cleanup_date(d):
            """'11/16/2018 as of 11/15/2018' --> '11/16/2018'"""
            return d.split(' ', 1)[0]

        rdr = rdr.convert('Date', cleanup_date)
        rdr = rdr.addfield('tradeDate', lambda x: x['Date'])
        rdr = rdr.addfield('total', lambda x: x['Amount'])
        rdr = rdr.addfield('type', lambda x: x['Action'])
        return rdr
