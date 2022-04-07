""" Fidelity Brokerage csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments

# Run Date,Action,Symbol,Security Description,Security Type,Quantity,Price ($),Commission ($),Fees ($),Accrued Interest ($),Amount ($),Settlement Date

class Importer(investments.Importer, csvreader.Importer):
    IMPORTER_NAME = 'Fidelity Brokerage CSV'
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'History'
        self.header_identifier = ''
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.skip_head_rows = 5
        self.skip_tail_rows = 14


        self.header_map = {

                "Run Date":             'date',
                "Action":               'memo',
                "Symbol":               'security',
                "Quantity":             'units',
                "Price ($)":            'unit_price',
                "Fees ($)":             'fees',
                "Amount ($)":           'amount',
                "tradeDate":            'tradeDate',
                "Settlement Date":      "settleDate",
                "total":                'total',
                "type":                 'type',

                "Security Description": "security_description",
                "Security Type": "security_type",
                "Commission ($)": "commission",
                "Accrued Interest ($)": "accrued_interest",

                # TODO:
                # "Commission ($)": '',
                # "Accrued Interest ($)": '',
            }

        self.transaction_type_map = {
                ' CHECK RECEIVED': 'transfer',
                ' DIRECT DEPOSIT': 'transfer',
                ' DIVIDEND RECEIVED': 'dividends',
                ' Electronic Funds Transfer Received': 'transfer',
                ' LONG-TERM CAP GAIN': 'capgains_lt',
                ' REINVESTMENT': 'buystock',
                ' SHORT-TERM CAP GAIN': 'capgains_st',
                ' TRANSFERRED FROM': 'transfer',
                ' YOU BOUGHT': 'buystock',
                ' MERGER MER FROM': 'transfer',
                ' MERGER MER PAYOUT': 'transfer',
            }

        # TODO
        self.skip_transaction_types = [ 'MERGER MER FROM', 'MERGER MER PAYOUT']

    def prepare_raw_columns(self, rdr):
        def cleanup_date(d):
            """' 11/16/2018 as' --> '11/16/2018'"""
            return d[1:]

        def description_to_action(d):
            for i in self.transaction_type_map:
                if d.startswith(i):
                    return i
            print("Unknown type: ", d)
            return d

        rdr = rdr.convert('Run Date', cleanup_date)
        rdr = rdr.convert('Settlement Date', cleanup_date)
        rdr = rdr.addfield('tradeDate', lambda x: x['Run Date'])
        rdr = rdr.addfield('total', lambda x: x['Amount ($)'])
        rdr = rdr.addfield('type', lambda x: x['Action'])
        rdr = rdr.convert('type', description_to_action)
        rdr = rdr.convert('Symbol', lambda x: x[1:])
        return rdr
