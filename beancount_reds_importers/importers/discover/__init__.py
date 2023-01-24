""" Discover credit card .csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = """ Discover credit card .csv importer."""

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = 'Discover.*'
        self.header_identifier = 'Trans. Date,Post Date,Description,Amount,Category'
        self.date_format = '%m/%d/%Y'
        self.header_map = {
            "Category":    'payee',
            "Description": 'memo',
            "Trans. Date": 'date',
            "Post Date":   'postDate',
            "Amount":      'amount',
            }

    def skip_transaction(self, ot):
        return False

    def prepare_processed_table(self, rdr):
        # Need to invert numbers supplied by Discover
        rdr = rdr.convert('amount', lambda x: -1 * x)
        return rdr
