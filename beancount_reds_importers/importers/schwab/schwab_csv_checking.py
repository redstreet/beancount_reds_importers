"""Schwab Checking .csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Schwab Checking account CSV"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = ".*_Checking_Transactions_"
        self.header_identifier = ""
        self.column_labels_line = '"Date","Status","Type","CheckNumber","Description","Withdrawal","Deposit","RunningBalance"'
        self.date_format = "%m/%d/%Y"
        self.skip_comments = "# "
        # fmt: off
        self.header_map = {
            "Date":             "date",
            "Type":             "type",
            "CheckNumber":      "checknum",
            "Description":      "payee",
            "Withdrawal":       "withdrawal",
            "Deposit":          "deposit",
            "RunningBalance":   "balance",
        }
        self.transaction_type_map = {
            "INTADJUST":    "income",
            "TRANSFER":     "transfer",
            "ACH":          "transfer",
        }
        # fmt: on
        self.skip_transaction_types = ["Journal"]

    def deep_identify(self, file):
        last_three = self.config.get("account_number", "")[-3:]
        return self.column_labels_line in file.head() and f"XX{last_three}" in file.name

    def prepare_table(self, rdr):
        rdr = rdr.addfield(
            "amount",
            lambda x: "-" + x["Withdrawal"] if x["Withdrawal"] != "" else x["Deposit"],
        )
        rdr = rdr.addfield("memo", lambda x: "")
        return rdr

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""

        date = self.get_balance_assertion_date()
        if date:
            yield banking.Balance(
                date, self.rdr.namedtuples()[0].balance, self.currency
            )
