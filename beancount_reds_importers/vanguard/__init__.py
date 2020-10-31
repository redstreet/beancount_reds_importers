""" Vanguard Brokerage ofx importer."""

import sys
import ntpath
import beancount_reds_importers.libimport.investments


class Importer(beancount_reds_importers.libimport.investments.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.account_number_field = 'number'
        self.filename_identifier_substring = 'OfxDownload.qfx'
        self.get_ticker_info = self.get_ticker_info_from_id

    def file_name(self, file):
        return 'vanguard-all-{}'.format(ntpath.basename(file.name))
