from pprint import pformat

import pdfplumber
import petl as etl

from beancount_reds_importers.libreader import csv_multitable_reader

LEFT = 0
TOP = 1
RIGHT = 2
BOTTOM = 3

BLACK = (0, 0, 0)
RED = (255, 0, 0)
PURPLE = (135, 0, 255)
TRANSPARENT = (0, 0, 0, 0)


class Importer(csv_multitable_reader.Importer):
    """
    A reader that converts a pdf with tables into a multi-petl-table format understood by transaction builders.


    ### Attributes customized in `custom_init`
    self.pdf_table_extraction_settings: `{}`
        a dictionary containing settings used to extract tables, see [pdfplumber documentation](https://github.com/jsvine/pdfplumber?tab=readme-ov-file#table-extraction-settings) for what settings are available

    self.pdf_table_extraction_crop: `(int,int,int,int)`
        a tuple with 4 values representing distance from left, top, right, bottom of the page respectively,
        this will crop the input (each page) before searching for tables

    self.pdf_table_title_height: `int`
        an integer representing how far up from the top of the table should we look for a table title.
        Set to 0 to not extract table titles, in which case sections will be labelled as `table_#` in the order
        they were encountered

    self.pdf_page_break_top: `int`
        an integer representing the threshold where a table can be considered page-broken. If the top of a table is
        lower than the provided value, it will be in consideration for amending to the previous page's last table.
        Set to 0 to never consider page-broken tables

    self.debug: `boolean`
        When debug is True a few images and text file are generated:
            .debug-pdf-metadata-page_#.png
                shows the text available in self.meta_text with table data blacked out

            .debug-pdf-table-detection-page_#.png
                shows the tables detected with cells outlined in red, and the background light blue. The purple box shows where we are looking for the table title.

            .debug-pdf-data.txt
                is a printout of the meta_text and table data found before being processed into petl tables, as well as some generated helper objects to add to new importers or import configs

    self.transaction_table_section: `str`
        When reading a pdf that contains transactions, set this setting to the name of the table section that
        contains the transactions. This is the key for the table in the self.alltables dictionary.

    ### Outputs
    self.meta_text: `str`
        contains all text found in the document outside of tables

    self.alltables: `{'table_1': <petl table of first table in document>, ...}`
        contains all the tables found in the document keyed by the extracted title if available, otherwise by the 1-based index in the form of `table_#`
    """

    FILE_EXTS = ["pdf"]

    def initialize_reader(self, file):
        if getattr(self, "file", None) != file:
            self.file = file
            self.meta_text = ""
            self.debug_images = {}
            self.file_read_done = False
            self.reader_ready = True

    def prepare_tables(self):
        """Make final adjustments to tables before processing by the transaction builder."""
        for section, table in self.alltables.items():
            table = table.rename(self.header_map)
            table = self.convert_columns(table)
            table = self.fix_column_names(table)
            table = self.prepare_processed_table(
                table
            )  # override this to make additonal adjustments

            self.alltables[section] = table
        return

    def get_transactions(self):
        """Provides the transactions to the transaction builder."""
        # Transactions are usually in a single table with other tables containing additonal
        # context information for the institution or statement period (See csv_multitable_reader definition).
        # Specify the transaction table section in the config.
        try:
            transaction_table = self.alltables[self.transaction_table_section]
        except KeyError:
            raise KeyError(
                f"Table section '{self.transaction_table_section}' not found in self.alltables."
                "Check the configuration value set in self.transaction_table_section."
            )

        for ot in transaction_table.namedtuples():
            if self.skip_transaction(ot):
                continue
            yield ot

    def get_adjusted_crop(self, page_idx, page):
        """Calculate the adjusted crop coordinates for the page."""
        return (
            min(0 + self.pdf_table_extraction_crop[LEFT], page.width),
            min(0 + self.pdf_table_extraction_crop[TOP], page.height),
            max(page.width - self.pdf_table_extraction_crop[RIGHT], 0),
            max(page.height - self.pdf_table_extraction_crop[BOTTOM], 0),
        )

    def extract_tables(self, page_idx, page, adjusted_crop):
        """Extract tables from a page within the given crop area."""
        cropped_page = page.crop(adjusted_crop)

        image = page.crop(adjusted_crop).to_image()  # debug
        image.debug_tablefinder(tf=self.pdf_table_extraction_settings)  # debug
        self.debug_images[page_idx] = image  # debug

        table_refs = cropped_page.find_tables(
            table_settings=self.pdf_table_extraction_settings
        )

        return [{"table": t.extract(), "bbox": t.bbox} for t in table_refs]

    def extract_metadata(self, page_idx, page, tables):
        """Extract metadata text outside of table bounding boxes."""
        meta_page = page
        meta_image = meta_page.to_image()  # debug

        for table in tables:
            meta_page = meta_page.outside_bbox(table["bbox"])
            meta_image.draw_rect(table["bbox"], BLACK, RED)  # debug

        if self.debug:
            meta_image.save(".debug-pdf-metadata-page_{}.png".format(page_idx))  # debug

        return meta_page.extract_text()

    def attach_section_headers(self, page_idx, page_tables, page):
        """Attach section headers to tables."""
        image = self.debug_images[page_idx]  # debug

        for table_idx, table in enumerate(page_tables):
            section_title_bbox = (
                table["bbox"][LEFT],
                max(table["bbox"][TOP] - self.pdf_table_title_height, 0),
                table["bbox"][RIGHT],
                table["bbox"][TOP],
            )

            bbox_area = pdfplumber.utils.calculate_area(section_title_bbox)
            if bbox_area > 0:
                section_title = page.crop(section_title_bbox).extract_text()
                image.draw_rect(section_title_bbox, TRANSPARENT, PURPLE)  # debuglogic
                page_tables[table_idx]["section"] = section_title
            else:
                page_tables[table_idx]["section"] = ""

            # replace None with ''
            for row_idx, row in enumerate(table["table"]):
                page_tables[table_idx]["table"][row_idx] = [
                    "" if v is None else v for v in row
                ]

        return page_tables

    def find_and_fix_broken_tables(self, tables):
        """Combine tables that are split up by page breaks."""
        for table_idx, table in enumerate(tables[:]):
            if (
                # if not the first table,
                table_idx >= 1
                # and the top of the table is close to the top of the page
                and table["bbox"][TOP] < self.pdf_page_break_top
                # and there is no section title
                and table["section"] == ""
                # and the header rows are the same,
                and tables[table_idx - 1]["table"][0] == tables[table_idx]["table"][0]
            ):  # assume a page break
                tables[table_idx - 1]["table"] = (
                    tables[table_idx - 1]["table"] + tables[table_idx]["table"][1:]
                )
                del tables[table_idx]
                continue

            # if there is no table section give it one
            if table["section"] == "":
                tables[table_idx]["section"] = "table_{}".format(table_idx + 1)

        return tables

    def generate_debug_helpers(self, tables):
        if self.debug:
            paycheck_template = {}
            header_map = {}
            for table in tables:
                for header in table["table"][0]:
                    header_map[header] = "overwrite_me"
                paycheck_template[table["section"]] = {}
                for row_idx, row in enumerate(table["table"]):
                    if row_idx == 0:
                        continue
                    paycheck_template[table["section"]][row[0]] = "overwrite_me"
            with open(".debug-pdf-data.txt", "w") as debug_file:
                debug_file.write(
                    pformat(
                        {
                            "_output": {"tables": tables, "meta_text": self.meta_text},
                            "_input": {
                                "table_settings": self.pdf_table_extraction_settings,
                                "crop_settings": self.pdf_table_extraction_crop,
                                "pdf_table_title_height": self.pdf_table_title_height,
                                "pdf_page_break_top": self.pdf_page_break_top,
                            },
                            "helpers": {
                                "header_map_generated": header_map,
                                "paycheck_template_generated": paycheck_template,
                            },
                        }
                    )
                )

    def read_file(self, file):
        """Main method to read and process a PDF into self.alltables."""
        if self.file_read_done:
            return

        self.meta_text = ""
        tables = []

        with pdfplumber.open(file) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                adjusted_crop = self.get_adjusted_crop(page_idx, page)
                page_tables = self.extract_tables(page_idx, page, adjusted_crop)
                self.meta_text += self.extract_metadata(page_idx, page, page_tables)
                page_tables = self.attach_section_headers(page_idx, page_tables, page)

                if self.debug:
                    self.debug_images[page_idx].save(
                        ".debug-pdf-table-detection-page_{}.png".format(page_idx)
                    )  # debug

                tables.extend(page_tables)

        tables = self.find_and_fix_broken_tables(tables)
        self.generate_debug_helpers(tables)  # debug

        self.alltables = {
            table["section"]: etl.wrap(table["table"]) for table in tables
        }
        self.prepare_tables()

        if self.debug:  # debug
            with open(".debug-pdf-prepared-tables.txt", "w") as debug_file:
                debug_file.write(pformat({"prepared_tables": self.alltables}))

        self.file_read_done = True
