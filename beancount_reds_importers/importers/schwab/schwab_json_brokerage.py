"""Schwab Brokerage .csv importer."""

from beancount_reds_importers.libreader import jsonreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(jsonreader.Importer, investments.Importer):
    IMPORTER_NAME = "Schwab Brokerage JSON"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = ".*_Transactions_"
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = "%m/%d/%Y"
        self.funds_db_txt = "funds_by_ticker"

    def skip_transaction(self, ot):
        return ot.type in ["", "Journal", "Journaled Shares"]
