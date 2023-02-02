
from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'TDAmeritrade'

    def custom_init(self):
        super(Importer, self).custom_init()
        self.max_rounding_error = 0.07
        self.filename_pattern_def = '.*tdameritrade'
        self.get_ticker_info = self.get_ticker_info_from_id

    def get_ticker_info(self, security):
        ticker = self.config['fund_info']['cusip_map'][security]
        return ticker, ''
