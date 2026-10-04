import datetime
from decimal import Decimal

from beancount.core import data

from beancount_reds_importers.importers.hsa import Importer


def test_hsa_history(tmp_path):
    history = tmp_path / "hsa.txt"
    history.write_text(
        "Date\tTransaction\tAmount\tHSA Cash Balance\tAttachments\n"
        "9/30/2026\tInterest for Sep-26\t$0.04\t$1,352.17\t\n"
        "9/30/2026\tEmployee Contribution (Tax year: 2026)\t$260.41\t$1,352.13\t\n"
        "7/20/2026\tEFT to broker\t($1,110.51)\t$50.02\t\n"
    )
    importer = Importer({"main_account": "Assets:HSA", "currency": "USD"})
    filename = str(history)
    assert importer.identify(filename)
    assert importer.date(filename) == datetime.date(2026, 9, 30)
    entries = importer.extract(filename)
    transactions = [entry for entry in entries if isinstance(entry, data.Transaction)]
    assert [entry.postings[0].units.number for entry in transactions] == [
        Decimal("0.04"),
        Decimal("260.41"),
        Decimal("-1110.51"),
    ]
    assert transactions[1].narration == "Employee Contribution (Tax year: 2026)"
    assert all(entry.postings[0].account == "Assets:HSA" for entry in transactions)
    balance = entries[-1]
    assert isinstance(balance, data.Balance)
    assert balance.date == datetime.date(2026, 10, 1)
    assert balance.amount.number == Decimal("1352.17")
    assert balance.amount.currency == "USD"


def test_unrelated_text(tmp_path):
    unrelated = tmp_path / "other.txt"
    unrelated.write_text("Date\tTransaction\tAmount\n")
    assert not Importer({"main_account": "Assets:HSA"}).identify(str(unrelated))
