"""Fidelity Net Benefits and Fidelity Investments OFX importer."""

import ntpath
from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'Fidelity Net Benefits / Fidelity Investments OFX'

    def custom_init(self):
        self.max_rounding_error = 0.18
        self.filename_pattern_def = '.*fidelity'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.get_payee = lambda ot: ot.memo.split(";", 1)[0] if ';' in ot.memo else ot.memo

    def security_narration(self, ot):
        ticker, ticker_long_name = self.get_ticker_info(ot.security)
        return f"[{ticker}]"

    def file_name(self, file):
        return 'fidelity-{}-{}'.format(self.config['account_number'], ntpath.basename(file.name))

    def get_target_acct_custom(self, transaction, ticker=None):
        if transaction.memo.startswith("CONTRIBUTION"):
            return self.config['transfer']
        if transaction.memo.startswith("FEES"):
            return self.config['fees']
        return None

    def get_available_cash(self, settlement_fund_balance=0):
        return getattr(self.ofx_account.statement, 'available_cash', None)
