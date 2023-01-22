"""xlsx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import petl as etl
from beancount_reds_importers.libreader import xlsreader


class Importer(xlsreader.Importer):
    FILE_EXTS = ['xlsx']

    def read_raw(self, file):
        rdr = etl.fromxlsx(file.name)
        # openpyxl gives us typed columns from the xlsx files (e.g. `float` for numeric
        # values, `datetime.datetime` for dates). Since xlsxreader currently inherits from csvreader,
        # converting these to be plain strings. Consider building a new xlsxreader that doesn't have to
        return rdr.convertall(str)
