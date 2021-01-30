""" Schwab Brokerage ofx importer."""

import ntpath
from beancount_reds_importers.libimport import investments, ofxreader


class Importer(investments.Importer, ofxreader.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.account_number_field = 'number'
        self.filename_identifier_substring = 'schwab.ofx'
        self.get_ticker_info = self.get_ticker_info_from_id

    def file_name(self, file):
        return ntpath.basename(file.name)
