"""BambooHR paycheck importer"""

import re

from dateparser.search import search_dates

from beancount_reds_importers.libreader import pdfreader
from beancount_reds_importers.libtransactionbuilder import paycheck

# BambooHR exports paycheck stubs to pdf, with multiple tables across multiple pages.
# Call this importer with a config that looks like:
#
#    bamboohr.Importer({"desc":"Paycheck (My Company)",
#        "main_account":"Income:Employment",
#        "paycheck_template": {}, # See beancount_reds_importers/libtransactionbuilder/paycheck.py for sample template
#        "currency": "PENNIES",
#    }),
#


class Importer(paycheck.Importer, pdfreader.Importer):
    IMPORTER_NAME = "BambooHR Paycheck"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = r"PayStub.*\.pdf"
        self.pdf_table_extraction_settings = {"join_tolerance": 4, "snap_tolerance": 4}
        self.pdf_table_extraction_crop = (0, 40, 0, 0)
        self.debug = False

        self.header_map = {
            "Deduction Type": "description",
            "Pay Type": "description",
            "Paycheck Total": "amount",
            "Tax Type": "description",
        }

        self.currency_fields = ["ytd_total", "amount"]

    def paycheck_date(self, input_file):
        if not self.file_read_done:
            self.read_file(input_file)
        dates = [date for _, date in search_dates(self.meta_text)]
        return dates[2].date()

    def prepare_tables(self):
        def valid_header(label):
            if label in self.header_map:
                return self.header_map[header]

            label = label.lower().replace(" ", "_")
            return re.sub(r"20\d{2}", "ytd", label)

        for section, table in self.alltables.items():
            # rename columns
            for header in table.header():
                table = table.rename(header, valid_header(header))
            # convert columns
            table = self.convert_columns(table)

            self.alltables[section] = table

    def build_metadata(self, file, metatype=None, data={}):
        return {"filing_account": self.config["main_account"]}
