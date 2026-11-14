"""Unit tests for Excel number-format aware precision in xlsxreader.

README ("Configuring currency precision") states that .xlsx files honor Excel cell
number formats when available, and fall back to `currency_precision` otherwise.
xlsxreader.Importer.get_precision_for_field() is the hook that implements this: it
looks up the number format recorded by read_raw() for the cells of a column.

These tests write a tiny workbook, format its amount column, and check the precision
of the resulting Decimals.
"""

from os import path

import openpyxl
import pytest

from beancount_reds_importers.libreader import xlsxreader
from beancount_reds_importers.libtransactionbuilder import banking

ROWS = [("01/02/2024", "one", 1.5), ("01/03/2024", "two", 2.25)]


class PrecisionImporter(xlsxreader.Importer, banking.Importer):
    """Minimal xlsx importer over a Date/Description/Amount sheet."""

    IMPORTER_NAME = "Test XLSX Precision Importer"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = ".*precision.*"
        self.header_identifier = ""
        self.date_format = "%m/%d/%Y"
        self.header_map = {
            "Date": "date",
            "Description": "memo",
            "Amount": "amount",
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []


def write_workbook(directory, number_format):
    """Write a workbook whose amount column carries `number_format`."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Date", "Description", "Amount"])
    for row in ROWS:
        ws.append(row)
    for row_idx in range(2, len(ROWS) + 2):
        ws.cell(row=row_idx, column=3).number_format = number_format
    filename = path.join(directory, "precision.xlsx")
    wb.save(filename)
    return filename


def amounts(tmp_path, number_format, **attrs):
    filename = write_workbook(str(tmp_path), number_format)
    importer = PrecisionImporter({"main_account": "Assets:Brokerage:Test", "currency": "USD"})
    for k, v in attrs.items():
        setattr(importer, k, v)
    importer.initialize(filename)
    importer.read_file(filename)
    return [row.amount for row in importer.rdr.namedtuples()]


@pytest.mark.parametrize(
    "number_format, expected",
    [
        ('"$"#,##0.0000', ["1.5000", "2.2500"]),  # more precision than the default
        ("#,##0", ["2", "2"]),  # less precision than the default
        ('"$"#,##0.00', ["1.50", "2.25"]),
    ],
)
def test_precision_follows_cell_number_format(tmp_path, number_format, expected):
    assert [str(a) for a in amounts(tmp_path, number_format)] == expected


def test_unformatted_cells_fall_back_to_currency_precision(tmp_path):
    # "General" carries no precision, so currency_precision decides.
    assert [str(a) for a in amounts(tmp_path, "General", currency_precision=3)] == [
        "1.500",
        "2.250",
    ]
