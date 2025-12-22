"""xlsx importer module for beancount to be used along with investment/banking/other importer modules in
beancount_reds_importers."""

import re
from decimal import ROUND_HALF_UP, Decimal

import openpyxl
import petl as etl
from beancount.core.number import D

from beancount_reds_importers.libreader import xlsreader


class Importer(xlsreader.Importer):
    FILE_EXTS = ["xlsx"]

    def read_raw(self, file):
        """Read xlsx file, preserving number formatting information for currency fields"""
        wb = openpyxl.load_workbook(file, data_only=True)
        ws = wb.active

        # Extract data with formatting metadata
        data = []
        formatting_info = {}  # Store formatting by (row, col)

        for row_idx, row in enumerate(ws.iter_rows()):
            row_data = []
            for col_idx, cell in enumerate(row):
                value = cell.value
                number_format = cell.number_format

                # Store formatting info for numeric cells
                if isinstance(value, (int, float)) and number_format:
                    formatting_info[(row_idx, col_idx)] = number_format

                row_data.append(value)
            data.append(row_data)

        # Store formatting info for use in convert_columns
        rdr = etl.wrap(data)

        # Store formatting metadata so convert_columns can access it
        # This is a bit of a hack, but petl doesn't have a clean way to pass metadata
        rdr._xlsx_formatting = formatting_info
        rdr._xlsx_header_row = 0  # Will be updated after we find the actual header

        return rdr

    def convert_columns(self, rdr):
        """Override to apply formatting-aware quantization for currency fields"""
        # First, call parent's convert_columns to do standard conversions
        rdr = super().convert_columns(rdr)

        # Now apply Excel formatting-aware quantization to currency fields
        currencies = getattr(self, "currency_fields", []) + [
            "unit_price",
            "fees",
            "total",
            "amount",
            "balance",
        ]

        for field in currencies:
            if field in rdr.header():
                rdr = self._quantize_currency_field(rdr, field)

        return rdr

    def _quantize_currency_field(self, rdr, field_name):
        """Quantize a currency field based on Excel number formatting"""
        # Get column index for this field
        try:
            col_idx = rdr.header().index(field_name)
        except (ValueError, AttributeError):
            return rdr

        # Get formatting info if available
        formatting_info = getattr(rdr, "_xlsx_formatting", {})

        # Analyze formats in this column to determine precision
        precisions = []
        for row_idx in range(len(rdr)):
            fmt = formatting_info.get((row_idx, col_idx))
            if fmt:
                precision = self._get_precision_from_format(fmt)
                if precision is not None:
                    precisions.append(precision)

        # Use most common precision, or default to 2
        if precisions:
            precision = max(set(precisions), key=precisions.count)
        else:
            precision = getattr(self, "currency_precision", 2)

        quantizer = Decimal("0." + "0" * precision) if precision > 0 else Decimal("1")

        # Apply quantization
        rdr = rdr.convert(
            field_name, lambda x: D(x).quantize(quantizer, rounding=ROUND_HALF_UP) if x else x
        )

        return rdr

    def _get_precision_from_format(self, fmt):
        """Extract decimal places from Excel number format string

        Examples:
            "$#,##0.00" → 2
            "0.00" → 2
            "#,##0.0" → 1
            "0" → 0
            "General" → None (use default)
        """
        if not fmt or fmt == "General":
            return None

        # Look for decimal point followed by zeros
        # Handles: 0.00, #,##0.00, $#,##0.00, etc.
        match = re.search(r"\.0+", str(fmt))
        if match:
            return len(match.group()) - 1  # -1 for the dot

        # Check if it's an integer format (no decimal point)
        if re.search(r"^[#0,\$€£¥\s\[\]]+$", str(fmt)):
            return 0

        return None  # Unknown format, use default
