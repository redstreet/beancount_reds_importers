"""xlsx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import re
from decimal import ROUND_HALF_UP, Decimal
from os import devnull

import petl as etl
from beancount.core.number import D

from beancount_reds_importers.libreader import csvreader


class Importer(csvreader.Importer):
    FILE_EXTS = ["xls"]

    def initialize_reader(self, file):
        if getattr(self, "file", None) != file:
            self.file = file
            self.file_read_done = False
            self.reader_ready = False

            # TODO: this reads the entire file. Chop off after perhaps 2k or n lines
            rdr = self.read_raw(file)
            header = ""
            for r in rdr:
                line = "".join(str(x) for x in r)
                header += line

            # TODO
            # account_number = self.config.get('account_number', '')
            # self.reader_ready = re.match(self.header_identifier, cache.get_file(file).head()) and \
            #                     account_number in cache.get_file(file).head()

            if re.match(self.header_identifier, header):
                self.reader_ready = True

    def read_raw(self, file):
        # set logfile to ignore WARNING *** file size (92598) not 512 + multiple of sector size (512)
        return etl.fromxls(file, logfile=open(devnull, "w"))

    def get_currency_fields(self):
        """Return list of fields to be treated as currency amounts"""
        return getattr(self, "currency_fields", []) + [
            "unit_price",
            "fees",
            "total",
            "amount",
            "balance",
        ]

    def get_precision_for_field(self, rdr, field_name):
        """Return the precision to use for quantizing a currency field.

        This method can be overridden by subclasses (e.g., xlsxreader) to provide
        custom precision logic based on file-specific metadata.

        Returns:
            int: Number of decimal places (e.g., 2 for standard currency, 0 for JPY)
        """
        return getattr(self, "currency_precision", 2)

    def convert_columns(self, rdr):
        """Override to apply quantization for Excel files"""
        # First, call parent's convert_columns to do standard conversions
        rdr = super().convert_columns(rdr)

        # Apply quantization to currency fields
        for field in self.get_currency_fields():
            if field not in rdr.header():
                continue

            precision = self.get_precision_for_field(rdr, field)
            quantizer = Decimal("0." + "0" * precision) if precision > 0 else Decimal("1")
            rdr = rdr.convert(
                field, lambda x: D(x).quantize(quantizer, rounding=ROUND_HALF_UP) if x else x
            )

        return rdr
