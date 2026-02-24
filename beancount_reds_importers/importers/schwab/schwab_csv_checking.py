"""Schwab Checking .csv importer."""

from beangulp import cache

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


def normalize_amount(tbl, neg_names, pos_names, out="amount"):
    """Banks split amounts across positive and negative columns. This function takes these and
    creates a single column with a positive/negative number. It accepts a list of column names for
    the positive and the negative column to accommodate csv variances.

    TODO: refacor by moving this into a common library and using it across importers
    """
    hdr = set(tbl.header())

    neg = next((c for c in neg_names if c in hdr), None)
    pos = next((c for c in pos_names if c in hdr), None)

    if not neg and not pos:
        raise ValueError("No amount columns found")

    def fn(row, n=neg, p=pos):
        vneg = row.get(n) if n else None
        vpos = row.get(p) if p else None
        return "-" + vneg if vneg not in ("", None) else vpos

    return tbl.addfield(out, fn)


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
            "TransactionType":  "type",
            "CheckNumber":      "checknum",
            "Description":      "payee",
            "Credits":          "deposit",
            "Debits":           "withdrawal",
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
        return self.column_labels_line in cache.get_file(file).head() and f"XX{last_three}" in file

    def prepare_table(self, rdr):
        rdr = normalize_amount(
            rdr,
            ["Withdrawal", "Debits"],
            ["Deposit", "Credits"],
        )
        rdr = rdr.addfield("memo", lambda x: "")
        return rdr

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""

        date = self.get_balance_assertion_date()
        if date:
            yield banking.Balance(date, self.rdr.namedtuples()[0].balance, self.currency)
