""" Vanguard screenscrape importer. Unsettled trades are not available in Vanguard's qfx and need to be
screenscrapped into a tsv"""

from beancount_reds_importers.libreader import tsvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, tsvreader.Importer):
    IMPORTER_NAME = 'Vanguard screenscrape tsv'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*vanguardss.*'
        self.header_identifier = ''
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.header_map = {
            "date":        'date',
            "settledate":   'tradeDate',
            "symbol":      'security',
            "description": 'memo',
            "action":      'type',
            "quantity":    'units',
            "price":       'unit_price',
            "fees":        'fees',
            "amount":      'amount',
            "total":       'total',
            }
        self.transaction_type_map = {
            'Buy':                          'buystock',
            'Sell':                         'sellstock',
            }
        self.skip_transaction_types = ['']

    def prepare_table(self, rdr):
        def extract_numbers(x):
            replacements = {'– ': '-',
                            '$': '',
                            ',': '',
                            'Free': '0',
                            }
            for k, v in replacements.items():
                x = x.replace(k, v)
            return x

        header = ('date', 'settledate', 'symbol', 'description', 'quantity', 'price', 'fees', 'amount')
        rdr = rdr.pushheader(header)

        rdr = rdr.addfield('action', lambda x: x['description'].rsplit(' ', 2)[1].strip())

        for field in ["date", "settledate", "symbol", "description", "quantity", "price", "fees"]:
            rdr = rdr.convert(field, lambda x: x.strip())
        for field in ["quantity", "amount", "price", "fees"]:
            rdr = rdr.convert(field, extract_numbers)

        rdr = rdr.addfield('total', lambda x: x['amount'])

        return rdr
