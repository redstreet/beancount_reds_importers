"""Blue Shield insurance EOBs importer.
Also see https://reds-rants.netlify.app/personal-finance/double-entry-bookkeeping-for-us-healthcare/
"""

import re

from beancount.core.number import D

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Blue Shield insurance EOBs importer."

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = "MedicalClaims"
        self.column_labels_line = "Group ID,Patient,Provider Name,Doctor Name,Specialty,Dates of Service,Claim Number,Amount Provider Billed,Network Savings,Paid by Medicare,Paid by Other Insurance,Paid by Blue Shield,Patient Responsibility Non-Covered,Patient Responsibility Deductible,Patient Responsibility Copay/Coinsurance,Process Date"
        self.header_identifier = ".*" + self.column_labels_line
        self.date_format = "%m/%d/%y"
        self.currency_fields = [
            "Patient Responsibility Non-Covered",
            "Patient Responsibility Deductible",
            "Patient Responsibility Copay/Coinsurance",
        ]
        self.header_map = {
            "Provider Name": "payee",
            "Doctor Name": "memo",
            "Dates of Service": "date",
        }
        self.currency = "USD"
        self.transaction_type_map = {}
        self.skip_transaction_types = []
        self.get_narration = lambda ot: ""

    def deep_identify(self, file):
        return re.match(self.header_identifier, file.head(), flags=re.DOTALL)

    def prepare_table(self, rdr):
        def sum_patient_resposibility(x):
            return -1 * sum(D(x[field]) for field in self.currency_fields)

        rdr = rdr.addfield("amount", sum_patient_resposibility)
        return rdr

    def skip_transaction(self, ot):
        return not ot.Group_ID

    def build_metadata(self, file, metatype=None, data={}):
        fa = (
            {"filing_account": self.config["filing_account"]}
            if "filing_account" in self.config
            else {}
        )
        ot = data["transaction"]
        fields = self.currency_fields
        fields = [re.sub("[-/ ]", "_", s) for s in fields]
        return fa | {k.lower(): getattr(ot, k) for k in fields if getattr(ot, k)}
