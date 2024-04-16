"""Generic pdf paycheck importer"""

import datetime

from beancount_reds_importers.libreader import pdfreader
from beancount_reds_importers.libtransactionbuilder import paycheck

# Generic pdf paystub importer. Use this to build your own pdf paystub importer.
# Call this importer with a config that looks like:
#
#    genericpdf.Importer({"desc":"Paycheck (My Company)",
#        "main_account":"Income:Employment",
#        "paycheck_template": {}, # See beancount_reds_importers/libtransactionbuilder/paycheck.py for sample template
#        "currency": "PENNIES",
#    }),
#


class Importer(paycheck.Importer, pdfreader.Importer):
    IMPORTER_NAME = "Generic PDF Paycheck"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = r"paystub.*\.pdf"
        self.pdf_table_extraction_settings = {"join_tolerance": 4, "snap_tolerance": 4}
        self.pdf_table_extraction_crop = (0, 0, 0, 0)
        self.pdf_table_title_height = 0
        # Set this true as you play with the extraction settings and crop to view images of what the pdf parser detects
        self.debug = True

        self.header_map = {
            "CURRENT": "amount",
            "CURRENT PAY": "amount",
            "PAY DESCRIPTION": "description",
            "DEDUCTIONS": "description",
            "TAX TYPE": "description",
            "TOTAL NET PAY": "description",
            "YTD": "ytd",
            "YTD PAY": "ytd",
        }

        self.currency_fields = ["ytd", "amount"]
        self.date_format = "%m/%d/%Y"

    def paycheck_date(self, input_file):
        if not self.file_read_done:
            self.read_file(input_file)
        *_, d = self.alltables["table_1"].header()
        self.date = datetime.datetime.strptime(d, self.date_format)
        return self.date.date()

    def prepare_tables(self):
        def valid_header(label):
            if label in self.header_map:
                return self.header_map[header]

            return label.lower().replace(" ", "_")

        for section, table in self.alltables.items():
            # rename columns
            for header in table.header():
                if section == "table_6" and header == "":
                    table = table.rename(header, "amount")
                else:
                    table = table.rename(header, valid_header(header))
            # convert columns
            table = self.convert_columns(table)

            self.alltables[section] = table

    def build_metadata(self, file, metatype=None, data={}):
        return {"filing_account": self.config["main_account"]}
