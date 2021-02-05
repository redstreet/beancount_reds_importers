""" TDAmeritrade ofx importer."""

from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    def custom_init(self):
        super(Importer, self).custom_init()
        self.max_rounding_error = 0.07
        self.account_number_field = 'account_id'
        self.filename_identifier_substring = 'tdameritrade'
        self.get_ticker_info = self.get_ticker_info_from_id

    def get_ticker_info(self, security):
        ticker = self.config['fund_info']['cusip_map'][security]
        return ticker, ''

    def get_target_acct_custom(self, transaction):
        m = transaction.memo
        if m.startswith("CONTRIBUTION"):
            return self.config['transfer']
        if m.startswith("FEES"):
            return self.config['fees']
        return self.target_account_map.get(transaction.type, None)
