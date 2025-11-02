import os
import shutil
import tempfile
import zipfile
from typing import List, Optional, Sequence

from beancount.core.data import Directive  # Beancount v3 core entries
from beangulp import Importer as BGImporter
from smart_importer import PredictPostings

from beancount_reds_importers.importers.amazon import amazon_orders, amazon_returns


class Importer(BGImporter):
    """
    A delegating importer for Amazon GDPR downloads. See accompanying README.md for more

    Amazon lets you download your entire order data to meet GDPR requirements. The download is in
    the form of a zip file that contains many csv files among other things. This importer detects
    GDPR ZIPs, extracts the CSVs that are interesting, and then runs separate CSV importers on
    those CSVs.

    Usage (to be added to your list of beangulp importers):

    from beancount_reds_importers.importers import amazongdpr
    amazongdpr.Importer({
        'account_purchases': "Assets:Zero-Sum-Accounts:Amazon:Purchases",
        'account_returns':   "Assets:Zero-Sum-Accounts:Amazon:Returns",
        'account_returns_other': "Assets:Zero-Sum-Accounts:Returns-and-Temporary",
        'filing_directory': "Assets:Zero-Sum-Accounts:Amazon",
    }),
    """

    def __init__(self, config) -> None:
        self.interesting_files = {
            "orders": "Retail.OrderHistory.1/Retail.OrderHistory.1.csv",
            "returns": "Retail.CustomerReturns.1.1/Retail.CustomerReturns.1.1.csv",
        }
        self.importers = {
            "orders": PredictPostings().wrap(
                amazon_orders.Importer({"main_account": config["account_purchases"]})
            ),
            "returns": amazon_returns.Importer(
                {
                    "main_account": config["account_returns"],
                    "target_account": config["account_returns_other"],
                }
            ),
        }
        self.config = config

    def identify(self, file: str) -> bool:
        """Return True if this looks like an Amazon GDPR ZIP."""
        if not file.lower().endswith(".zip"):
            return False

        try:
            with zipfile.ZipFile(file) as zf:
                names = zf.namelist()
        except zipfile.BadZipFile:
            return False

        return any(n in self.interesting_files.values() for n in names)

    def unzip_and_yield(self, file: str):
        tempdir = tempfile.mkdtemp("amazon_gdpr_zip_")
        try:
            with zipfile.ZipFile(file) as zf:
                members = zf.namelist()
                from pathlib import Path, PurePosixPath

                temp_root = Path(tempdir).resolve()

                for member in members:
                    if member in self.interesting_files.values():
                        # Map the ZIP's POSIX path into the temp dir
                        rel = Path(*PurePosixPath(member).parts)
                        out_path = (temp_root / rel).resolve()

                        # Safety: prevent paths escaping temp_root (zip-slip)
                        if not str(out_path).startswith(str(temp_root) + os.sep):
                            raise ValueError(f"Unsafe member path in zip: {member}")

                        # Ensure parent dirs exist
                        out_path.parent.mkdir(parents=True, exist_ok=True)

                        # Extract
                        with zf.open(member) as zfh, open(out_path, "wb") as out:
                            shutil.copyfileobj(zfh, out)

            # Delegate to your existing CSV importers:
            for kind, opath in self.interesting_files.items():
                path = (temp_root / opath).resolve()
                if os.path.isfile(path):
                    yield kind, path

        finally:
            # Clean up tempdir; if you prefer to keep for debugging, comment this out.
            shutil.rmtree(tempdir, ignore_errors=True)

    def extract(  # type: ignore[override]
        self,
        file: str,
        existing_entries: Optional[Sequence[Directive]] = None,
    ) -> List[Directive]:
        """
        Extract relevant CSVs from the ZIP and delegate to the inner CSV importers.
        Returns a combined list of entries (orders + returns).
        """

        entries: List[Directive] = []
        for kind, path in self.unzip_and_yield(file):
            entries.extend(self.importers[kind].extract(path, existing_entries))
        return entries

    # Optional (beangulp often calls these; safe defaults below)
    def file(self, file: str) -> Optional[str]:
        return os.path.basename(file)

    def account(self, file: str) -> Optional[str]:
        """TODO: this is WIP. Ideally, we only want to save the csv files we imported. That may
        not be possible to do here because that is handled by Beangulp. Currently, we just save the
        entire zip file.

        Note that smart_importer calls this same function to do something entirely different: to
        filter the list of relevant transactions. Given that, the suggestion is to use a common
        parent of the Purchases and Returns accounts for now:

        'account_purchases': "Assets:Zero-Sum-Accounts:Amazon:Purchases",
        'account_returns':   "Assets:Zero-Sum-Accounts:Amazon:Returns",
        'filing_directory': "Assets:Zero-Sum-Accounts:Amazon",

        """

        return self.config.get("filing_directory", "Assets:Zero-Sum-Accounts:Amazon")
