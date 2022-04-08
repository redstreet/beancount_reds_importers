""" Morgan Stanley Investments ofx importer."""

from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'Morgan Stanley Investments'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*morganstanley'
        self.get_ticker_info = self.get_ticker_info_from_id
