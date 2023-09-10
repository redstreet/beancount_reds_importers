""" ETrade Brokerage ofx importer."""

from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'ETrade Brokerage OFX'

    def custom_init(self):
        self.max_rounding_error = 0.11
        self.filename_pattern_def = '.*etrade'
        self.get_ticker_info = self.get_ticker_info_from_id

    def skip_transaction(self, ot):
        if 'JNL' in ot.memo:
            return True
        return False
