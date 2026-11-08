from os import path

from beancount_reds_importers.importers import mercurycards
from beancount_reds_importers.util import regression_pytest as regtest


@regtest.with_importer(
    mercurycards.Importer(
        {
            "main_account": "Liabilities:Credit-Cards:Mercury",
            "emit_filing_account_metadata": False,
            "filename_pattern": "mercury_statement_20241105.pdf",
            "skip_transaction_types": {},
            "currency": "USD",
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestMercuryCards(regtest.ImporterTestBase):
    pass


def test_date_on_fresh_importer():
    """Beangulp may request a date before identify() or extract()."""
    importer = mercurycards.Importer({"main_account": "Liabilities:Credit-Cards:Mercury"})
    result = importer.date(path.join(path.dirname(__file__), "mercury_statement_20241105.pdf"))
    assert result.isoformat() == "2024-11-05T00:00:00"
