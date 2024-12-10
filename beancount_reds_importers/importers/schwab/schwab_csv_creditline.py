"""Schwab Credit Line (eg: Pledged Asset Line) .csv importer."""

from beancount_reds_importers.importers.schwab import schwab_csv_checking
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(schwab_csv_checking.Importer):
    IMPORTER_NAME = "Schwab Line of Credit CSV"

    def custom_init(self):
        super().custom_init()
        self.filename_pattern_def = ".*_Transactions_"
        self.column_labels_line = (
            '"Date","Type","CheckNumber","Description","Withdrawal","Deposit","RunningBalance"'
        )

    def get_balance_statement(self, file=None):
        """Return the balance on the first and last dates"""

        for i in super().get_balance_statement(file):
            yield banking.Balance(i.date, -1 * i.amount, i.currency)
