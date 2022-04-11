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
            self.includes_balances = False

    def read_raw(self, file):
        rdr = etl.fromxlsx(file.name, read_only=True)
        # openpyxl gives us nicely typed columns from the xlsx files (e.g. `float` for numeric
        # values, `datetime.datetime` for dates). But the rest of beancount_reds_importers assumes
        # string values in all columns and will silently fail otherwise (e.g. in
        # `csvreader.convert_columns()`). Work around this by converting all of the nicely typed
        # data back to plain strings.
        return rdr.convertall(str)
