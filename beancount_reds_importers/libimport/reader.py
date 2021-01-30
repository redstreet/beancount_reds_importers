"""Reader module base class for beancount_reds_importers. ofx, csv, etc. readers inherit this."""

import ntpath
from os import path


class Reader():
    FILE_EXT = ''

    def identify(self, file):
        # quick check to filter out files that are not the right format
        if not file.name.lower().endswith(self.FILE_EXT):
            return False
        self.custom_init()
        if self.filename_identifier_substring not in path.basename(file.name):
            return False
        self.initialize_reader(file)
        return self.reader_ready

    def file_name(self, file):
        return '{}'.format(ntpath.basename(file.name))

    def file_account(self, _):
        return self.config['main_account']
