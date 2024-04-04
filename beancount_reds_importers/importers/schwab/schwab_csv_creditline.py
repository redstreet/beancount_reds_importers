"""Schwab Credit Line (eg: Pledged Asset Line) .csv importer."""

from beancount_reds_importers.importers.schwab import schwab_csv_checking


class Importer(schwab_csv_checking.Importer):
    IMPORTER_NAME = "Schwab Line of Credit CSV"

    def custom_init(self):
        super().custom_init()
        self.filename_pattern_def = ".*_Transactions_"
        self.column_labels_line = (
            '"Date","Type","CheckNumber","Description","Withdrawal","Deposit","RunningBalance"'
        )
