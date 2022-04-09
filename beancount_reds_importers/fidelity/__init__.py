""" Fidelity Net Benefits ofx importer."""

import ntpath
from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'Fidelity Net Benefits OFX'

    def custom_init(self):
        self.max_rounding_error = 0.14
        self.filename_pattern_def = '.*fidelity'
        self.get_ticker_info = self.get_ticker_info_from_id

    def file_name(self, file):
        return 'fidelity-{}-{}'.format(self.config['account_number'], ntpath.basename(file.name))

    def get_target_acct_custom(self, transaction, ticker=None):
        if transaction.memo.startswith("CONTRIBUTION"):
            return self.config['transfer']
        if transaction.memo.startswith("FEES"):
            return self.config['fees']
        return None
