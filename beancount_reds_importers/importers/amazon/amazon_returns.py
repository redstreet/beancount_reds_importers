from decimal import ROUND_HALF_UP, Decimal

from beangulp import cache

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Amazon Returns Importer"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = "CustomerReturns"
        self.header_identifier = ""
        self.column_labels_line = '"OrderId","ContractId","DateOfReturn","ReturnAmount","ReturnAmountCurrency","ReturnReason","Resolution"'
        self.file_encoding = "utf-8-sig"  # Amazon files have BOM
        # fmt: off
        self.header_map = {
            "DateOfReturn": "date",
            "OrderId":      "payee",
            "ReturnAmount": "amount",
            "ReturnAmountCurrency": "currency",
        }
        self.transaction_type_map = {
            "":     "transfer",
        }
        # fmt: on
        self.skip_transaction_types = []

    def skip_transaction(self, row):
        return row.currency == "Not Available"

    def deep_identify(self, file):
        return self.column_labels_line in cache.get_file(file).head()

    def prepare_processed_table(self, rdr):
        rdr = rdr.addfield("memo", "Amazon Return")
        rdr = rdr.convert("amount", lambda i: i.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        return rdr
