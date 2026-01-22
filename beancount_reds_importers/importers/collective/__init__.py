"""Collective insurance EOBs importer.
Also see https://reds-rants.netlify.app/personal-finance/double-entry-bookkeeping-for-us-healthcare/
"""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(csvreader.Importer, banking.Importer):
    IMPORTER_NAME = "Collective insurance EOBs importer"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = "ClaimDownloadReport"
        self.column_labels_line = "Service Date,Claim Number,Name,Claim Type,Network,Provider,Summary,Your anticipated Cost,Status,Copay,Deductible,Coinsurance,Not Covered"
        self.header_identifier = self.column_labels_line
        self.date_format = "%Y-%m-%d"
        self.currency_fields = ["Copay", "Deductible", "Coinsurance", "Not Covered"]
        self.header_map = {
            "Service Date": "date",
            "Summary": "payee",
            "Your anticipated Cost": "amount",
        }
        self.currency = "USD"
        self.transaction_type_map = {}
        self.skip_transaction_types = []
        self.get_narration = lambda ot: ""

    def prepare_processed_table(self, rdr):
        return rdr.convert("amount", lambda x: -1 * x)

    def skip_transaction(self, ot):
        return not ot.amount

    @staticmethod
    def claim_type_map(claim_type):
        if claim_type in ["Medical", "Pharmacy"]:
            return "Medical:" + claim_type
        return claim_type

    def get_main_account(self, ot):
        account_leaf = self.config.get("account_leaf", {})
        if account_leaf:
            return self.config["main_account"].format(
                Name=account_leaf[ot.Name], Claim_Type=self.claim_type_map(ot.Claim_Type)
            )
        return self.config["main_account"].format(Claim_Type=self.claim_type_map(ot.Claim_Type))

    def get_target_account(self, ot):
        account_leaf = self.config.get("account_leaf", {})
        if account_leaf:
            return self.config["target_account"].format(
                Name=account_leaf[ot.Name], Claim_Type=self.claim_type_map(ot.Claim_Type)
            )
        return self.config["target_account"].format(Claim_Type=self.claim_type_map(ot.Claim_Type))

    def build_metadata(self, file, metatype=None, data={}):
        fa = (
            {"filing_account": self.config["filing_account"]}
            if "filing_account" in self.config
            else {}
        )
        ot = data["transaction"]
        fields = self.currency_fields
        fields = [s.replace(" ", "_") for s in fields]
        return fa | {k.lower(): getattr(ot, k) for k in fields if getattr(ot, k)}
