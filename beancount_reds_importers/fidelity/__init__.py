""" Fidelity Net Benefits ofx importer."""

import ntpath
from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.14
        self.account_number_field = 'account_id'
        self.filename_identifier_substring = 'fidelity'
        self.get_ticker_info = self.get_ticker_info_from_id

    def file_name(self, file):
        return 'fidelity-{}-{}'.format(self.config['account_number'], ntpath.basename(file.name))

    def get_target_acct_custom(self, transaction):
        if transaction.memo.startswith("CONTRIBUTION"):
            return self.config['transfer']
        if transaction.memo.startswith("FEES"):
            return self.config['fees']
        return self.target_account_map.get(transaction.type, None)
