"""Test xlsx formatting-aware precision handling."""

from os import path

from beancount_reds_importers.libreader import xlsxreader
from beancount_reds_importers.libtransactionbuilder import banking
from beancount_reds_importers.util import regression_pytest as regtest


class TestXLSXImporter(xlsxreader.Importer, banking.Importer):
    """Simple test importer for XLSX files"""

    IMPORTER_NAME = "Test XLSX Importer"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = "gains_losses"
        self.header_identifier = "Record Type.*Symbol.*Quantity"
        self.column_labels_line = (
            "Record Type,Symbol,Quantity,Date Sold,Total Proceeds,Gain/Loss,Cost Basis"
        )
        self.date_format = "%m/%d/%Y"
        self.header_map = {
            "Record Type": "type",
            "Date Sold": "date",
            "Symbol": "payee",
            "Gain/Loss": "amount",
            "Total Proceeds": "total",
            "Cost Basis": "balance",
        }
        self.transaction_type_map = {}
        self.skip_transaction_types = []
        self.currency_fields = []  # Let default currency fields handle it

    def prepare_table(self, rdr):
        # Add a memo field and currency
        rdr = rdr.addfield("memo", lambda x: f"Trade {x['Quantity']} shares")
        rdr = rdr.addfield("currency", lambda x: "USD")
        return rdr


@regtest.with_importer(
    TestXLSXImporter(
        {
            "main_account": "Assets:Brokerage:TestAccount",
            "currency": "USD",
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestXLSX(regtest.ImporterTestBase):
    pass
