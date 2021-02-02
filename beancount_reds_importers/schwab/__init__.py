""" Schwab Brokerage ofx importer."""

from beancount_reds_importers.libimport import investments, ofxreader


class Importer(investments.Importer, ofxreader.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.account_number_field = 'number'
        self.filename_identifier_substring = 'schwab'
        self.get_ticker_info = self.get_ticker_info_from_id

    # def get_ticker_info(self, security):
    #     ticker = self.cusip_map[security]
    #     ticker_long_name = self.inv_ticker_map[ticker]
    #     return ticker, ticker_long_name
