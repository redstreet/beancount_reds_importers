""" TD Ameritrade .csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(csvreader.Importer, investments.Importer):
    IMPORTER_NAME = 'TD Ameritrade CSV'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'transactions'
        self.header_identifier = 'DATE,TRANSACTION ID,DESCRIPTION.*'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.skip_head_rows = 0
        self.skip_tail_rows = 1
        self.header_map = {
            "DATE":        'date',
            "TRANSACTION ID": 'txid',
            "DESCRIPTION": 'memo',
            "SYMBOL":      'security',
            "QUANTITY":    'units',
            "PRICE":       'unit_price',
            "AMOUNT":      'amount',
            "SHORT-TERM RDM FEE": 'short_term_fee',
            "FUND REDEMPTION FEE": 'fund_redmpt_fee',
            " DEFERRED SALES CHARGE": 'deferred_sales_charge',
            "REG FEE": 'fees',
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []

    def prepare_raw_columns(self, rdr):
        def f(desc):
            if desc.startswith('Bought'):
                return 'buystock'
            if desc.startswith('Sold'):
                return 'sellstock'
            if desc.startswith('QUALIFIED DIVIDEND'):
                return 'dividends'
            if desc.startswith('ADR FEE'):
                return 'debit'
            if desc.startswith('CLIENT REQUESTED ELECTRONIC FUNDING RECEIPT'):
                return 'credit'
            return 'Unknown type'

        rdr = rdr.addfield('type', lambda x: f(x['DESCRIPTION']))
        rdr = rdr.addfield('total', lambda x: x['AMOUNT'])
        rdr = rdr.addfield('tradeDate', lambda x: x['DATE'])

        return rdr

    def get_balance_positions(self):
        return []

    def build_metadata(self, file, metatype=None, data={}):
        """This method is for importers to override. The overridden method can
        look at the metatype ('transaction', 'balance', 'account', 'commodity', etc.)
        and the data dictionary to return additional metadata"""
        return {'txid': data['transaction'].txid}
