""" Vanguard Brokerage ofx importer."""

import ntpath
from beancount_reds_importers.libreader import ofxreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(investments.Importer, ofxreader.Importer):
    IMPORTER_NAME = 'Vanguard'

    # Any memo in the source OFX that's in this set is not carried forward.
    # Vanguard sets memos that aren't very useful and would create noise in the
    # generated ledger transactions.
    SKIP_MEMOS = {
        "Price as of date based on closing price",
    }

    def custom_init(self):
        self.max_rounding_error = 0.11
        self.filename_pattern_def = '.*OfxDownload'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.get_payee = self.cleanup_memo

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

    def cleanup_memo(self, ot):
        # some vanguard files have memos repeated like this:
        # 'DIVIDEND REINVESTMENTDIVIDEND REINVESTMENT'
        retval = ot.memo
        if ot.memo[:int(len(ot.memo)/2)] == ot.memo[int(len(ot.memo)/2):]:
            retval = ot.memo[:int(len(ot.memo)/2)]
        return retval

        # For users to comment out in their local file if they so prefer
        # parts = [ot.type]
        # if ot.memo not in self.SKIP_MEMOS:
        #     parts.append(ot.memo)
        # return ' - '.join(parts)

    def skip_transaction(self, ot):
        return ot.memo.startswith("JOURNAL SEC BETWEEN ACCT")
