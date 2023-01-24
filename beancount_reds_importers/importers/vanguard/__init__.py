""" Vanguard Brokerage ofx importer."""

import ntpath
from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'Vanguard'

    def custom_init(self):
        self.max_rounding_error = 0.11
        self.filename_pattern_def = '.*OfxDownload'
        self.get_ticker_info = self.get_ticker_info_from_id

        # See https://github.com/redstreet/beancount_reds_importers/issues/15: occasionally, Vanguard qfx
        # files contain a transaction with untiprice set to zero. Probably an internal bug at their end. We
        # set this handler to "do nothing", which will result in the below, which can be fixed manually:
        # 2021-01-01 * "DIVIDEND REINVEST" "[TICKER] Vanguard Ticker"
        #    Assets:Vanguard:TICKER  234.56 TICKER
        #    Income:Dividends:TICKER  -78 USD

        self.price_cost_both_zero_handler = lambda *args: None

    def file_name(self, file):
        return 'vanguard-all-{}'.format(ntpath.basename(file.name))

    def get_target_acct_custom(self, transaction, ticker=None):
        if 'LT CAP GAIN' in transaction.memo:
            return self.config['capgainsd_lt']
        elif 'ST CAP GAIN' in transaction.memo:
            return self.config['capgainsd_st']
        return None
