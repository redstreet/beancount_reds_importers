"""xlsx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import petl as etl
from beancount_reds_importers.libreader import csvreader


class Importer(csvreader.Importer):
    FILE_EXTS = ['xls']

    def initialize_reader(self, file):
        if getattr(self, 'file', None) != file:
            self.file = file
            self.file_read_done = False
            self.reader_ready = True

            self.currency = self.config.get('currency', 'CURRENCY_NOT_CONFIGURED')

    def read_raw(self, file):
        return etl.fromxls(file.name)
