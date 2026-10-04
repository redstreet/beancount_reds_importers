"""Import tab-separated HSA cash transaction history (.txt or .tsv)."""

from beancount.core import data

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "HSA cash transactions"
    FILE_EXTS = ["txt", "tsv"]

    def custom_init(self):
        self.filename_pattern_def = ".*"
        self.csv_delimiter = "\t"
        self.header_identifier = "Date\tTransaction\tAmount\tHSA Cash Balance\tAttachments"
        self.date_format = "%m/%d/%Y"
        self.header_map = {
            "Date": "date",
            "Transaction": "payee",
            "Amount": "amount",
            "HSA Cash Balance": "balance",
        }
        self.skip_transaction_types = []
        self.currency = self.config.get("currency", "USD")

    def prepare_table(self, rdr):
        for column in ("Amount", "HSA Cash Balance"):
            rdr = rdr.convert(column, lambda value: value.replace("(", "-").replace(")", ""))
        return rdr.addfield("memo", "")

    def custom_entry_mods(self, entries):
        return [
            entry
            for entry in entries
            if not (isinstance(entry, data.Transaction) and "Contribution" in entry.narration)
        ]

    def get_balance_statement(self, file=None):
        # History is newest first, including transactions on the same day.
        if len(self.rdr) > 1:
            yield banking.Balance(
                self.get_balance_assertion_date(), self.rdr.namedtuples()[0].balance, self.currency
            )
