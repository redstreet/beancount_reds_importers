"""Reader module base class for beancount_reds_importers. ofx, csv, etc. readers inherit this."""

import ntpath
import re
from os import path

from loguru import logger


class Reader:
    FILE_EXTS = [""]
    IMPORTER_NAME = "NOT SET"

    def identify(self, file):
        try:
            # quick check to filter out files that are not the right format
            # print()
            # print('------------------', self.IMPORTER_NAME, '(' + self.FILE_EXT + ')')
            # print(file.lower())
            if not any(file.lower().endswith(ext) for ext in self.FILE_EXTS):
                # print("No match on extension")
                return False
            self.custom_init()
            self.filename_pattern = self.config.get("filename_pattern", self.filename_pattern_def)
            if not re.match(self.filename_pattern, path.basename(file)):
                # print("No match on filename_pattern", self.filename_pattern, path.basename(file))
                return False
            self.currency = self.config.get("currency", "CURRENCY_NOT_CONFIGURED")
            self.initialize_reader(file)
        except Exception as e:
            logger.error(e)

        # print("reader_ready:", self.reader_ready, self.IMPORTER_NAME)
        return self.reader_ready

    def set_currency(self):
        """For overriding"""
        self.currency = self.config.get("currency", "CURRENCY_NOT_CONFIGURED")

    def file_name(self, file):
        return "{}".format(ntpath.basename(file))

    def file_account(self, file):
        # Ugly hack to handle an interaction with smart_importer. See:
        # https://github.com/redstreet/beancount_reds_importers/issues/41
        # https://github.com/beancount/smart_importer/issues/122
        # https://github.com/beancount/smart_importer/issues/30
        import inspect

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        if any("predictor" in i.filename for i in calframe):
            if "smart_importer_hack" in self.config:
                return self.config["smart_importer_hack"]

        # Otherwise handle a typical bean-file call
        self.initialize(file)
        if "filing_account" in self.config:
            return self.config["filing_account"]
        return self.config["main_account"]

    def get_balance_statement(self, file=None):
        return []

    def get_balance_positions(self):
        return []

    def get_balance_assertion_date(self):
        return None

    def get_available_cash(self, settlement_fund_balance=0):
        return None

    def get_transactions(self):
        raise NotImplementedError(
            "get_transactions() must be implemented by a subclass (usually the reader, but sometimes the importer)."
        )
