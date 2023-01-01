"""Reader module base class for beancount_reds_importers. ofx, csv, etc. readers inherit this."""

import ntpath
from os import path
import re


class Reader():
    FILE_EXT = ''
    IMPORTER_NAME = 'NOT SET'

    def identify(self, file):
        # quick check to filter out files that are not the right format
        # print()
        # print('------------------', self.IMPORTER_NAME, '(' + self.FILE_EXT + ')')
        # print(file.name.lower())
        if not file.name.lower().endswith(self.FILE_EXT):
            # print("No match on extension")
            return False
        self.custom_init()
        self.filename_pattern = self.config.get('filename_pattern', self.filename_pattern_def)
        if not re.match(self.filename_pattern, path.basename(file.name)):
            # print("No match on filename_pattern", self.filename_pattern, path.basename(file.name))
            return False
        self.initialize_reader(file)
        # print("reader_ready:", self.reader_ready)
        return self.reader_ready

    def file_name(self, file):
        return '{}'.format(ntpath.basename(file.name))

    def file_account(self, _):
        return self.config['main_account'].replace(':{ticker}', '').replace(':{currency}', '')

    def get_balance_statement(self):
        return []

    def get_balance_positions(self):
        return []

    def get_available_cash(self):
        return None
