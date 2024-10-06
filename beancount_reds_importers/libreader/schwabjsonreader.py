"""JSON importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers.

------------------------------
This is WIP and incomplete.
------------------------------

JSON schemas vary widely. This one is based on Charles Schwab's json format. In the future, the
goal is to make this reader automatically "understand" the schema of any json given to it.

Until that happens, perhaps this file should be renamed to schwabjsonreader.py.
"""

import json

# import re
import warnings

# import datetime
# import ofxparse
# from collections import namedtuple
from beancount.ingest import importer
from bs4.builder import XMLParsedAsHTMLWarning

from beancount_reds_importers.libreader import reader

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class Importer(reader.Reader, importer.ImporterProtocol):
    FILE_EXTS = ["json"]

    def initialize_reader(self, file):
        if getattr(self, "file", None) != file:
            self.file = file
            self.reader_ready = self.deep_identify(file)
            if self.reader_ready:
                self.file_read_done = False

    def deep_identify(self, file):
        # identify based on filename
        return True

    def file_date(self, file):
        "Get the maximum date from the file."
        self.initialize(file)  # self.date_format gets set via this
        self.read_file(file)
        return max(ot.date for ot in self.get_transactions()).date()

    def read_file(self, file):
        with open(file.name) as fh:
            self.rdr = json.load(fh)

            # transactions = []
            # for transaction in self.rdr['BrokerageTransactions']:
            #     raw_ot = Transaction(
            #         date       = transaction['Date'],
            #         type       = transaction['Action'],
            #         security   = transaction['Symbol'],
            #         memo       = transaction['Description'],
            #         unit_price = transaction['Price'],
            #         units      = transaction['Quantity'],
            #         fees       = transaction['Fees & Comm'],
            #         total      = transaction['Amount']
            #     )

    # def get_transactions(self):
    #     Transaction = namedtuple('Transaction', ['date', 'type', 'security', 'memo', 'unit_price',
    #                                              'units', 'fees', 'total'])
    #     for transaction in self.rdr['BrokerageTransactions']:
    #         raw_ot = Transaction(
    #             date       = transaction['Date'],
    #             type       = transaction['Action'],
    #             security   = transaction['Symbol'],
    #             memo       = transaction['Description'],
    #             unit_price = transaction['Price'],
    #             units      = transaction['Quantity'],
    #             fees       = transaction['Fees & Comm'],
    #             total      = transaction['Amount']
    #         )
    #         ot = self.fixup(ot)
    #         import pdb; pdb.set_trace()
    #         yield ot

    def fixup(self, ot):
        ot.date = self.convert_date(ot.date)

    # def convert_date(d):
    #     return datetime.datetime.strptime(d, self.date_format)

    def get_balance_assertion_date(self):
        return None
