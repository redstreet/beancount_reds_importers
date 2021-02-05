""" Vanguard Brokerage ofx importer."""

import ntpath
from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.account_number_field = 'number'
        self.filename_identifier_substring = 'OfxDownload.qfx'
        self.get_ticker_info = self.get_ticker_info_from_id

    def file_name(self, file):
        return 'vanguard-all-{}'.format(ntpath.basename(file.name))

    def get_target_acct_custom(self, transaction):
        return self.target_account_map.get(transaction.type, None)
