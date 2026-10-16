"""Import only Processing transactions from Fidelity standalone account history CSVs.

Use the standard investment importer config with account_number set to either the
full account number or its last four digits. Files must be named
History_for_Account_<account number>.csv; only the last four digits are matched.
"""

import re
from pathlib import Path

from beancount_reds_importers.importers.fidelity import fidelity_all_accounts_csv
from beancount_reds_importers.libreader import csvreader


class Importer(fidelity_all_accounts_csv.Importer):
    IMPORTER_NAME = "Fidelity Standalone Account CSV"

    def custom_init(self):
        super().custom_init()
        self.filename_pattern_def = r"History_for_Account_[A-Za-z0-9]+\.csv$"
        self.header_identifier = r"(?m)^Run Date,Action,Symbol,Description,Type,"
        self.column_labels_line = (
            "Run Date,Action,Symbol,Description,Type,Price ($),Quantity,Commission ($),"
            "Fees ($),Accrued Interest ($),Amount ($),Cash Balance ($),Settlement Date"
        )

    def deep_identify(self, file):
        match = re.fullmatch(r"History_for_Account_([A-Za-z0-9]+)\.csv", Path(file).name)
        account_number = str(self.config.get("account_number", ""))
        return bool(
            match
            and len(account_number) >= 4
            and account_number[-4:].isdigit()
            and match[1][-4:] == account_number[-4:]
            and csvreader.Importer.deep_identify(self, file)
        )

    def prepare_table(self, rdr):
        rdr = rdr.select(lambda row: row["Cash Balance ($)"].strip() == "Processing")
        rdr = rdr.cutout("Cash Balance ($)")
        # Normalize standalone headers to the all-accounts format.
        rdr = rdr.rename({field: field.removesuffix(" ($)") for field in rdr.fieldnames()})
        for field in ["Action", "Symbol", "Description"]:
            rdr = rdr.convert(field, lambda value: value.lstrip())
        # Account identity was checked against the filename, not a CSV column.
        # Supply it so the parent's account and transaction filters still apply.
        rdr = rdr.addfield("Account Number", self.config["account_number"])
        return super().prepare_table(rdr)

    def extract_balances_and_prices(self, file, counter):
        # Pending activity provides neither positions nor a settled cash balance.
        return []
