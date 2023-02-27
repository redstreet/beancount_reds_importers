"""csv importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

from beancount_reds_importers.libreader import csvreader

# This is a reader that converts:
# ---- examples.csv -----
# downloaded on: blah blah
# section1
# date,transactions,amount
# 2020-02-02,3,5.00
# 2020-02-02,3,5.00
# section2
# account_num,balance,date
# 123123,1000,2020-12-31
# 23048,2000,2020-12-31
# end_of_file
# -----------------------
#
# to this data structure:
# self.alltables =  {'section1': <petl table of section 1>
#                    'section2': <petl table of section 2>
#                   }
#
# where each value is a petl table.
#
# The reader assumes that any line with a single field marks the beginning of a new section, with that field
# as the title of the section. The next line is assumed to be the header for that new section.
#
# This file format is common enough to warrant this reader.
# The xlsx_multitable reader is built on top of this reader


class Importer(csvreader.Importer):
    def initialize_reader(self, file):
        csvreader.Importer.initialize_reader(self, file)

    def file_date(self, file):
        "Get the maximum date from the file."
        self.read_file(file)
        raise "Not yet implemented"
        pass

    def convert_columns(self, rdr):
        pass

    def is_section_title(self, row):
        # Match against rows that contain section titles. Eg: 'section1', 'section2', ...
        return len(row) == 1

    def read_file(self, file):
        # read csv
        # identify and separate out tables
        # clean up each table
        # output is in self.alltables

        if self.file_read_done:
            return

        self.raw_rdr = rdr = self.read_raw(file)

        rdr = rdr.skip(getattr(self, 'skip_head_rows', 0))                 # chop unwanted file header rows
        rdr = rdr.head(len(rdr) - getattr(self, 'skip_tail_rows', 0) - 1)  # chop unwanted file footer rows

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
            table = rdr.skip(s+1)      # skip past start index and header row
            table = table.head(e-s-1)  # chop lines after table section data
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

    def get_available_cash(self, settlement_fund_balance=0):
        return None
