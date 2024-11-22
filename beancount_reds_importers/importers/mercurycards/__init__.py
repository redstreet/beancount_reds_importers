"""Mercury Cards pdf importer for beancount."""

import re
from datetime import datetime

import petl as etl

from beancount_reds_importers.libreader import pdfreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(banking.Importer, pdfreader.Importer):
    IMPORTER_NAME = "Mercury Cards"

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_pattern_def = "Mercury Statement *.pdf"
            self.pdf_table_extraction_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
            }
            self.pdf_table_extraction_crop = (0, 0, 0, 0)
            self.pdf_table_title_height = 0
            self.pdf_page_break_top = 0
            self.date_format = "%m/%d/%Y"
            self.transaction_table_section = "table_1"
            self.meta_text = ""
            self.skip_transaction_types = {}
            self.header_map = {
                "Post Date": "settleDate",
                "Trans Date": "date",
                "Description": "memo",
                "Reference": "reference",
                "Amount": "amount",
            }

            # payee and narration are swapped
            # We need to swap them back. See banking.py
            self.get_payee = lambda ot: ot.memo
            self.get_narration = lambda ot: None  # setting to none to use smart importer

            self.debug = True
            self.custom_init_run = True

    def file_date(self, file):
        if not self.file_read_done:
            self.read_file(file)

        return self.get_closing_date()

    def get_closing_date(self):
        if self.meta_text == "":
            raise ValueError("No meta_text has been found")

        # Pattern to match "Closing Date" followed by a date in mm/dd/yyyy format
        pattern = r"Closing Date\s+(\d{2}/\d{2}/\d{4})"

        # Search for all matches in self.meta_text
        matches = re.findall(pattern, self.meta_text)

        date_string = matches[0]
        date_format = "%m/%d/%Y"
        datetime_object = datetime.strptime(date_string, date_format)

        return datetime_object

    def get_adjusted_crop(self, page_idx, page):
        """Dynamically find the crop positon based on the position of text found on the page."""
        adjusted_crop = (0, 0, 1, 1)
        table_start_search_text = "TRANSACTIONS"
        table_start_search_results = page.search(table_start_search_text)
        if table_start_search_results:
            table_start = table_start_search_results[0]
            table_start_x = table_start["x0"] - 30
            table_start_y = table_start["bottom"] + 50

            table_end_search_text = "YEAR-TO-DATE"
            table_end_search_results = page.search(table_end_search_text)

            if table_end_search_results:
                table_end = table_end_search_results[0]
                table_end_y = table_end["top"] - 10
            else:
                table_end_y = page.bbox[3]  # if no end text is found use the whole page

            adjusted_crop = (
                (table_start_x),
                (table_start_y),
                (page.bbox[2]),
                (table_end_y),
            )
        return adjusted_crop

    def fix_years(self, table):
        """
        Determine the correct year for the given date string (MM/DD format).
        """

        def get_year(d):
            # Get the current year
            current_year = self.get_closing_date().year

            return f"{d}/{current_year}"

        date_headers = ["Post Date", "Trans Date"]
        for i in date_headers:
            if i in table.header():
                table = table.convert(i, lambda d: get_year(d))

        return table

    def prepare_tables(self):
        """Make final adjustments to tables before processing by the transaction builder."""
        for section, table in self.alltables.items():
            # set table headers. table was goofy, so they had to be croped out
            headers = [
                "Post Date",
                "Trans Date",
                "Description",
                "City",
                "State",
                "Reference",
                "Amount",
            ]
            table = etl.wrap(etl.pushheader(table, headers))

            # add year to mm/dd formatted date
            table = self.fix_years(table)

            table = table.rename(self.header_map)
            table = self.convert_columns(table)

            # the amounts should be negative since they're charges
            table = etl.convert(table, "amount", lambda a: a * -1)

            table = self.fix_column_names(table)
            table = self.prepare_processed_table(
                table
            )  # override this to make additonal adjustments

            self.alltables[section] = table

        self.combine_tables()
        return

    def combine_tables(self):
        # Initialize an empty table
        combined_table = None

        for section, table in self.alltables.items():
            # Convert each table to a petl table
            petl_table = etl.wrap(table)

            # Combine tables
            if combined_table is None:
                combined_table = petl_table  # First table initializes the combined table
            else:
                combined_table = etl.cat(
                    combined_table, petl_table
                )  # Concatenate additional tables

        return combined_table
