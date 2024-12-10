from pprint import pformat

import pdfplumber
import petl as etl

from beancount_reds_importers.libreader import csvreader

LEFT = 0
TOP = 1
RIGHT = 2
BOTTOM = 3

BLACK = (0, 0, 0)
RED = (255, 0, 0)
PURPLE = (135, 0, 255)
TRANSPARENT = (0, 0, 0, 0)


class Importer(csvreader.Importer):
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

    ### Outputs
    self.meta_text: `str`
        contains all text found in the document outside of tables

    self.alltables: `{'table_1': <petl table of first table in document>, ...}`
        contains all the tables found in the document keyed by the extracted title if available, otherwise by the 1-based index in the form of `table_#`
    """

    FILE_EXTS = ["pdf"]

    def initialize_reader(self, file):
        if getattr(self, "file", None) != file:
            self.pdf_table_extraction_settings = {}
            self.pdf_table_extraction_crop = (0, 0, 0, 0)
            self.pdf_table_title_height = 20
            self.pdf_page_break_top = 45
            self.debug = False

            self.meta_text = ""
            self.file = file
            self.file_read_done = False
            self.reader_ready = True

    def file_date(self, file):
        raise "Not implemented, must overwrite, check self.alltables, or self.meta_text for the data"
        pass

    def prepare_tables(self):
        return

    def read_file(self, file):
        tables = []

        with pdfplumber.open(file.name) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                # all bounding boxes are (left, top, right, bottom)
                adjusted_crop = (
                    min(0 + self.pdf_table_extraction_crop[LEFT], page.width),
                    min(0 + self.pdf_table_extraction_crop[TOP], page.height),
                    max(page.width - self.pdf_table_extraction_crop[RIGHT], 0),
                    max(page.height - self.pdf_table_extraction_crop[BOTTOM], 0),
                )

                # Debug image
                image = page.crop(adjusted_crop).to_image()
                image.debug_tablefinder(tf=self.pdf_table_extraction_settings)

                table_ref = page.crop(adjusted_crop).find_tables(
                    table_settings=self.pdf_table_extraction_settings
                )
                page_tables = [{"table": i.extract(), "bbox": i.bbox} for i in table_ref]

                # Get Metadata (all data outside tables)
                meta_page = page
                meta_image = meta_page.to_image()
                for table in page_tables:
                    meta_page = meta_page.outside_bbox(table["bbox"])
                    meta_image.draw_rect(table["bbox"], BLACK, RED)

                meta_text = meta_page.extract_text()
                self.meta_text = self.meta_text + meta_text

                # Attach section headers
                for table_idx, table in enumerate(page_tables):
                    section_title_bbox = (
                        table["bbox"][LEFT],
                        max(table["bbox"][TOP] - self.pdf_table_title_height, 0),
                        table["bbox"][RIGHT],
                        table["bbox"][TOP],
                    )

                    bbox_area = pdfplumber.utils.calculate_area(section_title_bbox)
                    if bbox_area > 0:
                        section_title = meta_page.crop(section_title_bbox).extract_text()
                        image.draw_rect(section_title_bbox, TRANSPARENT, PURPLE)
                        page_tables[table_idx]["section"] = section_title
                    else:
                        page_tables[table_idx]["section"] = ""

                    # replace None with ''
                    for row_idx, row in enumerate(table["table"]):
                        page_tables[table_idx]["table"][row_idx] = [
                            "" if v is None else v for v in row
                        ]

                tables = tables + page_tables

                if self.debug:
                    image.save(".debug-pdf-table-detection-page_{}.png".format(page_idx))
                    meta_image.save(".debug-pdf-metadata-page_{}.png".format(page_idx))

            # Find and fix page broken tables
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

        if self.debug:
            # generate helpers
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

        self.alltables = {table["section"]: etl.wrap(table["table"]) for table in tables}
        self.prepare_tables()

        if self.debug:
            with open(".debug-pdf-prepared-tables.txt", "w") as debug_file:
                debug_file.write(pformat({"prepared_tables": self.alltables}))

        self.file_read_done = True
