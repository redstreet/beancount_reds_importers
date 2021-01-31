"""csv importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import petl as etl
from beancount_reds_importers.libimport import csvreader


class NotImplementedError(Exception):
    pass

# This csv reader uses petl to read a .csv with multiple tables into a dictionary of petl tables. The section
# title is the key. See csvreader for more.


class Importer(csvreader.Importer):
    def initialize_reader(self, file):
        csvreader.Importer.initialize_reader(self, file)

        # TODO: should be in importer, not here
        self.includes_balances = True

    def file_date(self, file):
        "Get the maximum date from the file."
        self.read_file(file)
        raise "Not yet implemented"
        pass

    def convert_columns(self, rdr):
        pass

    def read_raw(self, file):
        return etl.fromcsv(file.name)

    def is_section_title(self, row):
        return len(row) == 1

    def read_file(self, file):
        # read csv
        # identify and separate out tables
        # clean up each table
        # output is in self.alltables

        if self.file_read_done:
            return

        self.raw_rdr = rdr = self.read_raw(file)

        #     [0, 2, 10] <-- starts
        # [-1, 1, 9]     <-- ends
        table_starts = [i for (i, row) in enumerate(rdr) if self.is_section_title(row)] + [len(rdr)]
        table_ends = [r-1 for r in table_starts][1:]
        table_indexes = zip(table_starts, table_ends)

        # build the dictionary of tables
        self.alltables = {}
        for (s, e) in table_indexes:
            if s == e:
                continue
            table = rdr.skip(s+1)
            table = table.head(e-s-1)
            self.alltables[rdr[s][0]] = table

        for section, table in self.alltables.items():
            table = table.rowlenselect(0, complement=True)  # clean up empty rows
            table = table.cut(*[h for h in table.header() if h])  # clean up empty columns
            self.alltables[section] = table

        self.prepare_tables()  # to be overridden by importer
        self.file_read_done = True

    def get_transactions(self):
        # TODO, remove
        for i in []:
            yield i

    def get_balance_positions(self):
        # TODO
        raise "Not supported"

    def get_available_cash(self):
        return False
