""" Vanguard Brokerage ofx importer."""

import sys
import ntpath
import beancount_reds_importers.libimport.investments


class Importer(beancount_reds_importers.libimport.investments.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.account_number_field = 'number'
        self.filename_identifier_substring = 'OfxDownload.qfx'
        self.cusip_map = self.config['fund_info']['cusip_map']

    def get_ticker_info(self, security):
        try:
            ticker = self.cusip_map[security]
            ticker_long_name = self.inv_ticker_map[ticker]
        except KeyError:
            tickers = [t for t in self.get_ticker_list()
                       if (t not in self.cusip_map or t not in self.inv_ticker_map)]
            print(f"Error: cusip_map and ticker_map not found for: {tickers}", file=sys.stderr)
            sys.exit(1)
        return ticker, ticker_long_name

    def file_name(self, file):
        return 'vanguard-all-{}'.format(ntpath.basename(file.name))
