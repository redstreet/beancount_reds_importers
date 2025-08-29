import os
import shutil
import tempfile
import zipfile
from typing import List, Optional, Sequence

from beancount.core.data import Directive  # Beancount v3 core entries
from beangulp import Importer as BGImporter
from smart_importer import PredictPostings

from beancount_reds_importers.importers.amazongdpr import amazon_orders, amazon_returns


class AmazonGDPRZipImporter(BGImporter):
    """
    A delegating importer for Amazon GDPR "container" downloads.

    It detects GDPR ZIPs, extracts the CSVs that are interesting, and then runs your existing CSV
    importers on those CSVs.

    Usage (add amazon_importer to your list of beangulp importers):
    amazon_importer = amazongdpr.AmazonGDPRZipImporter({
        'importers' : {
            'orders': amazon_importer_orders(),
            'returns': amazon_importer_returns(),
        }
    })
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
        # ZIP itself is just a container; Let's save the individual .csv files
        return "Assets:Zero-Sum-Accounts:Amazon"
        # for kind, path in self.unzip_and_yield(file):
        #     self.importers[kind].file(path, existing_entries)
        # return entries
