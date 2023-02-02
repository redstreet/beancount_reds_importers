""" TDAmeritrade Brokerage .csv importer."""


import datetime
import re
import traceback

from beancount.core.number import D
import petl

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


# header looks like: DATE,TRANSACTION ID,DESCRIPTION,QUANTITY,SYMBOL,PRICE,COMMISSION,AMOUNT,REG FEE,SHORT-TERM RDM FEE,FUND REDEMPTION FEE, DEFERRED SALES CHARGE
# note that space on the beginning of that last field...
#


class Importer(investments.Importer, csvreader.Importer):
    IMPORTER_NAME = 'TDAmeritrade Brokerage CSV'

    def custom_init(self):
        self.currency = 'USD'
        self.max_rounding_error = 0.07
        self.filename_pattern_def = 'test-trans.csv'
        self.header_identifier = 'DATE,TRANSACT.*'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.skip_tail_rows = 1
        self.include_balances = False
        self.get_payee = lambda ot: ot.type
        self.header_map = {
            "DATE":                  'date',
            "TRANSACTION ID":        'transid',
            "DESCRIPTION":           'type',
            "QUANTITY":              'units',
            "SYMBOL":                'security',
            "PRICE":                 'unit_price',
            "COMMISSION":            'fees',
            "AMOUNT":                'amount',
            "REG FEE":               'regfees',
            "SHORT-TERM RDM FEE":    'strdmfees',
            "FUND REDEMPTION FEE":   'fundrdmfees',
            " DEFERRED SALES CHARGE":'defslschrg',
            #^ note that space 
            #
            #  These are added later by prepare_raw_columns
            # "desc":                 'memo',
            # "tradeDate":            'tradeDate',
            # "total":                'total',
            }
        self.transaction_type_map = {
            'Billpay':                                               'transfer',
            'Bought':                                                'buystock',
            'CASH ALTERNATIVES DIVIDENDS (ticker)':                  'dividends',
            'CASH ALTERNATIVES DIVIDENDS':                           'dividends',
            'CASH ALTERNATIVES INTEREST (ticker)':                   'income',
            'CASH ALTERNATIVES INTEREST':                            'income',
            'CASH ALTERNATIVES PURCHASE (ticker)':                   'transfer',
            'CASH ALTERNATIVES PURCHASE':                            'transfer',
            'CASH ALTERNATIVES REDEMPTION (ticker)':                 'transfer',
            'CASH ALTERNATIVES REDEMPTION':                          'transfer',
            'CASH MOVEMENT OF INCOMING ACCOUNT TRANSFER':            'transfer',
            'Check Written'                             :            'transfer',
            'INTERNAL TRANSFER OF CASH':                             'transfer',
            'MANDATORY REORGANIZATION FEE (ticker)':                 'transfer',
            'NON-TAXABLE SPIN OFF/LIQUIDATION DISTRIBUTION (ticker)':'transfer',
            'ORDINARY DIVIDEND (ticker)':                            'dividends',
            'ORDINARY DIVIDEND':                                     'dividends',
            'PAPER STATEMENT FEE':                                   'transfer',
            'QUALIFIED DIVIDEND (ticker)':                           'dividends',
            'Sold':                                                  'sellstock',
            'TRANSFER OF SECURITY OR OPTION IN (ticker)':            'transfer',
            }
        self.skip_transaction_types = ['Journal']


    def read_file(self, file):
        if not self.file_read_done:
            rdr = self.read_raw(file)
            print ("Version 0.0.6\n\n After read_raw file : \n", rdr)
            rdr = rdr.skip(getattr(self, 'skip_head_rows', 0))                 # chop unwanted header rows
            rdr = rdr.head(len(rdr) - getattr(self, 'skip_tail_rows', 0) - 1)  # chop unwanted footer rows

            if hasattr(self, 'skip_comments'):
                rdr = rdr.skipcomments(self.skip_comments)
            rdr = rdr.rowslice(getattr(self, 'skip_data_rows', 0), None)
            rdr = self.prepare_raw_columns(rdr)
            print ("After prepare_raw_columns : \n", rdr)
            rdr = rdr.rename(self.header_map)
            print ("After rename : \n", rdr)
            rdr = self.convert_columns(rdr)
            print ("After convert columns : \n", rdr)
            rdr = self.prepare_processed_table(rdr)
            self.rdr = rdr
            self.ifile = file
            self.file_read_done = True

    def get_ticker_info(self, security):
        ticker = self.config['fund_info']['cusip_map'][security]
        return ticker, ''

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
            return re.sub("[^0-9\.-]", "", str(x).strip())  # noqa: W605
        currencies = ['unit_price', 'fees', 'total', 'amount', 'balance', 'regfees', 'strdmfees', 'fundrdmfees', 'defslschrg' ]
        for i in currencies:
            if i in rdr.header():
                rdr = rdr.convert(i, remove_non_numeric)
                rdr = rdr.convert(i, D)

        # fixup dates
        def convert_date(d):
            return datetime.datetime.strptime(d, self.date_format)
        dates = ['date', 'tradeDate', 'settleDate']
        for i in dates:
            if i in rdr.header():
                rdr = rdr.convert(i, convert_date)

        return rdr


    def prepare_raw_columns(self, rdr):
        rdr = rdr.addfield('desc', lambda x: x['DESCRIPTION'])
        rdr = rdr.addfield('tradeDate', lambda x: x['DATE'])
        rdr = rdr.addfield('total', lambda x: x['AMOUNT'])

        # some rows I just need to match the first part of the line
        rdr = rdr.sub('DESCRIPTION',
            '^(Billpay.*)|(BILL PAY.*)|(CLIENT REQUESTED ELECTRONIC FUNDING DISBURSEMENT \(.*)',
            'Billpay', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^Bought.*', 'Bought', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^CASH ALTERNATIVES DIVIDENDS \(.*',
            'CASH ALTERNATIVES DIVIDENDS (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^CASH ALTERNATIVES INTEREST \(.*',
            'CASH ALTERNATIVES INTEREST (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^CASH ALTERNATIVES PURCHASE \(.*',
            'CASH ALTERNATIVES PURCHASE (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^CASH ALTERNATIVES REDEMPTION \(.*',
            'CASH ALTERNATIVES REDEMPTION (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^(CHECK \(WRITTEN AGAINST BROKERAGE ACCOUNT\))|(Check #.*)',
            'Check Written', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^MANDATORY REORGANIZATION FEE \(.*',
            'MANDATORY REORGANIZATION FEE (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^NON-TAXABLE SPIN OFF/LIQUIDATION DISTRIBUTION \(.*',
            'NON-TAXABLE SPIN OFF/LIQUIDATION DISTRIBUTION (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^ORDINARY DIVIDEND \(.*',
            'ORDINARY DIVIDEND (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^QUALIFIED DIVIDEND \(.*',
            'QUALIFIED DIVIDEND (ticker)', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^Sold.*',
            'Sold', count=1)
        rdr = rdr.sub('DESCRIPTION',
            '^TRANSFER OF SECURITY OR OPTION IN \(.*',
            'TRANSFER OF SECURITY OR OPTION IN (ticker)', count=1)

        # some symbols I put lot notes on
        rdr = rdr.sub('SYMBOL', '^AMD[abc?]', 'AMD', count=1)
        rdr = rdr.sub('SYMBOL', '^INTCw[abc]', 'INTCW', count=1)
        rdr = rdr.sub('SYMBOL', '^INTC[abc?]', 'INTC', count=1)


        return rdr
