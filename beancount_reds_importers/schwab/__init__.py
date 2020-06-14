""" Schwab Brokerage ofx importer."""

import ntpath
import beancount_reds_importers.libimport.investments


class Importer(beancount_reds_importers.libimport.investments.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.account_number_field = 'number'
        self.filename_identifier_substring = 'schwab.ofx'
        self.cusip_map = self.config['fund_info']['cusip_map']
        self.get_ticker_info = self.get_ticker_info_cusip

    def file_name(self, file):
        return ntpath.basename(file.name)
