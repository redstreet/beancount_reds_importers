"""DCU (Digital Federal Credit Union) csv importer for beancount."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "DCU"

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_pattern_def = ".*Account_Transactions"
            self.header_identifier = ""
            self.column_labels_line = (
                '"DATE","TRANSACTION TYPE","DESCRIPTION","AMOUNT","ID","MEMO","CURRENT BALANCE"'
            )
            self.date_format = "%m/%d/%Y"
            # fmt: off
            self.header_map = {
                "DATE":             "date",
                "DESCRIPTION":      "payee",
                "MEMO":             "memo",
                "AMOUNT":           "amount",
                "CURRENT BALANCE":  "balance",
                "TRANSACTION TYPE": "type",
            }
            self.transaction_type_map = {
                "DEBIT":    "transfer",
                "CREDIT":   "transfer",
            }
            # fmt: on
            self.skip_transaction_types = []

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""

        date = self.get_balance_assertion_date()
        if date:
            yield banking.Balance(date, self.rdr.namedtuples()[0].balance, self.currency)
