"""xlsx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import petl as etl
from beancount_reds_importers.libreader import csvreader


class Importer(csvreader.Importer):
    FILE_EXT = 'xlsx'

    def initialize_reader(self, file):
        if getattr(self, 'file', None) != file:
            self.file = file
            self.file_read_done = False
            self.reader_ready = True

            self.currency = self.config.get('currency', 'USD')

    def read_raw(self, file):
        rdr = etl.fromxlsx(file.name, read_only=True)
        # openpyxl gives us typed columns from the xlsx files (e.g. `float` for numeric
        # values, `datetime.datetime` for dates). Since xlsxreader currently inherits from csvreader,
        # converting these to be plain strings. Consider building a new xlsxreader that doesn't have to
        return rdr.convertall(str)
