"""xlsx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import csv
import warnings
from io import StringIO

import openpyxl
import petl as etl

from beancount_reds_importers.libreader import csv_multitable_reader

# This xlsx reader uses petl to read a .csv with multiple tables into a dictionary of petl tables. The section
# title is the key. See csv_multitable_reader for more.


class Importer(csv_multitable_reader.Importer):
    FILE_EXTS = ["xlsx"]

    def initialize_reader(self, file):
        if getattr(self, "file", None) != file:
            self.file = file
            self.file_read_done = False
            self.reader_ready = True

    def read_raw(self, file):
        # return etl.fromcsv(file)

        in_memory_file = StringIO()
        csv_writer = csv.writer(in_memory_file)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wb = openpyxl.load_workbook(file)
            sh = wb.worksheets[0]

        for r in sh.rows:
            csv_writer.writerow([cell.value for cell in r])
        in_memory_file.seek(0)
        rawlines = in_memory_file.read().encode()
        raw = etl.MemorySource(rawlines)
        rdr = etl.fromcsv(raw)
        return rdr

    def is_section_title(self, row):
        if len(row) == 1:
            return True
        return all(i == "" or i is None for i in row[1:])
