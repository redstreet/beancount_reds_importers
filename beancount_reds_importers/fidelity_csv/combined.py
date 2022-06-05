""" Fidelity Brokerage international csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments

# TODO: put this and its variation with 'Account' into self.header_identifier
# Run Date,Account,Action,Symbol,Security Description,Security Type,Exchange Quantity,Exchange Currency,Quantity,Currency,Price,Exchange Rate,Commission,Fees,Accrued Interest,Amount,Settlement Date

# TODO:
# - header differs:
# - includes currency
# - skip_head_rows and skip_tail_rows are different
# - different enough to warrant a separate importer?

# - filter by account:
#    petl.transform.selects.select(table, *args, **kwargs)[source]
#    https://petl.readthedocs.io/en/stable/transform.html#selecting-rows


class Importer(investments.Importer, csvreader.Importer):
    IMPORTER_NAME = 'Fidelity Brokerage CSV'
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*History.*'
        self.header_identifier = '.*Run Date,Account,Action,Symbol,Security Description,Security Type,Exchange Quantity,Exchange Currency,Quantity,Currency,Price,Exchange Rate,Commission,Fees,Accrued Interest,Amount,Settlement Date'
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
                "Price":            'unit_price',
                "Fees":             'fees',
                "Amount":           'amount',
                "tradeDate":            'tradeDate',
                "Settlement Date":      "settleDate",
                "total":                'total',
                "type":                 'type',

                "Security Description": "security_description",
                "Security Type":        "security_type",
                "Commission":       "commission",
                "Accrued Interest": "accrued_interest",

                "Exchange Quantity": "exchange_quantity",
                "Exchange Currency": "exchange_currency",
                "Exchange Rate": "exchange_rate",
                "Settlement Date": "settlement_date",

                # TODO:
                # "Commission ($)": '',
                # "Accrued Interest ($)": '',
            }

        self.transaction_type_map = { #TODO this list is incomplete
                'CHECK RECEIVED':                     'dep',
                'Check Paid':                         'transfer',
                'DIRECT DEPOSIT':                     'dep',
                'DIVIDEND RECEIVED':                  'dividends',
                'Electronic Funds Transfer Received': 'credit',
                'LONG-TERM CAP GAIN':                 'capgainsd_lt',
                'REINVESTMENT':                       'buystock',
                'SHORT-TERM CAP GAIN':                'capgainsd_st',
                'TRANSFERRED FROM':                   'debit',
                'YOU BOUGHT':                         'buystock',
                'MERGER MER FROM':                    'transfer',
                'MERGER MER PAYOUT':                  'transfer',
                'REDEMPTION':                  'sellmf',
                'PURCHASE INTO':                  'buymf',
                'DIRECT DEBIT':                  'transfer',
                'INTEREST EARNED':                  'income',
            }

        # TODO
        self.skip_transaction_types = [ 'MERGER MER FROM', 'MERGER MER PAYOUT']

    def skip_transaction(self, row):
        if row.type in self.skip_transaction_types:
            return True
        if 'Account' in self.rdr.header():
            return row.Account != self.config['account_number']
        return False

    def prepare_raw_columns(self, rdr):
        def description_to_action(d):
            for i in self.transaction_type_map:
                if d.startswith(i):
                    return i
            print("Unknown transaction type: ", d)
            return d

        for field in ['Run Date', 'Settlement Date', 'Action', 'Symbol']:
            rdr = rdr.convert(field, lambda x: x.lstrip())

        rdr = rdr.addfield('tradeDate', lambda x: x['Run Date'])
        rdr = rdr.addfield('total', lambda x: x['Amount'])
        rdr = rdr.addfield('type', lambda x: x['Action'])
        rdr = rdr.convert('type', description_to_action)
        return rdr
