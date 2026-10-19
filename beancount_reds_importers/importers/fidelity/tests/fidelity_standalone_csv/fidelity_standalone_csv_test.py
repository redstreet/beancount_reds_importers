import csv
from datetime import date
from pathlib import Path

import pytest
from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.number import D

from beancount_reds_importers.importers.fidelity import fidelity_standalone_csv


def make_importer(account_number="5678"):
    return fidelity_standalone_csv.Importer(
        {
            "account_number": account_number,
            "currency": "USD",
            "main_account": "Assets:Fidelity:{ticker}",
            "cash_account": "Assets:Fidelity:{currency}",
            "dividends": "Income:Dividends",
            "interest": "Income:Interest",
            "cg": "Income:Capital-Gains",
            "capgainsd_lt": "Income:Capital-Gains:Long",
            "capgainsd_st": "Income:Capital-Gains:Short",
            "fees": "Expenses:Fees",
            "rounding_error": "Equity:Rounding",
            "fund_info": {
                "fund_data": [
                    ("SOXX", "464287523", "Configured semiconductor fund description"),
                    ("VTI", "922908769", "Configured total stock market description"),
                ],
                "money_market": [],
            },
        }
    )


def write_history(tmp_path, filename="History_for_Account_12345678.csv", statuses=None):
    if statuses is None:
        statuses = ["Processing", "Processing", "Processing", "1000.00", "Pending"]
    file = tmp_path / filename
    with file.open("w", encoding="utf-8-sig", newline="") as stream:
        stream.write("\n\n")
        writer = csv.writer(stream)
        writer.writerow(
            [
                "Run Date",
                "Action",
                "Symbol",
                "Description",
                "Type",
                "Price ($)",
                "Quantity",
                "Commission ($)",
                "Fees ($)",
                "Accrued Interest ($)",
                "Amount ($)",
                "Cash Balance ($)",
                "Settlement Date",
            ]
        )
        trades = [
            ("YOU BOUGHT", "SOXX", "497.89", "0.123", "", "-61.24"),
            ("YOU BOUGHT", "SOXX", "497.97", "30", "", "-14939.1"),
            ("YOU SOLD", "VTI", "374.02", "-40", "0.31", "14960.49"),
        ]
        for index, status in enumerate(statuses):
            action, symbol, price, quantity, fees, amount = trades[index % len(trades)]
            writer.writerow(
                [
                    "10/16/2026",
                    f"{action} Example (Cash)",
                    symbol,
                    "Example",
                    "Cash",
                    price,
                    quantity,
                    "",
                    fees,
                    "",
                    amount,
                    status,
                    "10/19/2026",
                ]
            )
        stream.write("\nDisclaimer text\nDate downloaded 10/16/2026 11:19 am\n")
    return str(file)


@pytest.mark.parametrize("account_number", ["5678", "12345678", "X99995678"])
def test_processing_trades(tmp_path, account_number):
    file = write_history(tmp_path)
    importer = make_importer(account_number)
    assert importer.identify(file)
    entries = importer.extract(file)
    assert len(entries) == 3
    assert all(isinstance(entry, data.Transaction) for entry in entries)
    assert all(entry.date == date(2026, 10, 16) for entry in entries)
    assert importer.date(file) == date(2026, 10, 16)
    assert [entry.narration for entry in entries] == [
        "[SOXX] Configured semiconductor fund description",
        "[SOXX] Configured semiconductor fund description",
        "[VTI] Configured total stock market description",
    ]
    for entry, units, symbol, cash in zip(
        entries,
        ["0.123", "30", "-40"],
        ["SOXX", "SOXX", "VTI"],
        ["-61.24", "-14939.1", "14960.49"],
    ):
        assert entry.postings[0].units == Amount(D(units), symbol)
        assert any(
            posting.account == "Assets:Fidelity:USD" and posting.units == Amount(D(cash), "USD")
            for posting in entry.postings
        )
    assert any(
        posting.account == "Expenses:Fees" and posting.units == Amount(D("0.31"), "USD")
        for posting in entries[-1].postings
    )


@pytest.mark.parametrize("account_number", ["1234", "", "678", "123456789"])
def test_wrong_or_missing_account(tmp_path, account_number):
    assert not make_importer(account_number).identify(write_history(tmp_path))


@pytest.mark.parametrize(
    "filename",
    [
        "History_for_Account_56781234.csv",
        "History_for_Account_123456780.csv",
        "Other5678.csv",
    ],
)
def test_suffix_must_match_account_in_basename(tmp_path, filename):
    directory = tmp_path / "5678"
    directory.mkdir()
    assert not make_importer().identify(write_history(directory, filename))


def test_wrong_header(tmp_path):
    file = tmp_path / "History_for_Account_12345678.csv"
    file.write_text("unrelated,data\n")
    assert not make_importer().identify(str(file))


@pytest.mark.parametrize("statuses", [[], ["1000.00", "Pending"]])
def test_no_processing_transactions(tmp_path, statuses):
    file = write_history(tmp_path, statuses=statuses)
    importer = make_importer()
    assert importer.identify(file)
    assert importer.extract(file) == []
    assert importer.date(file) is None


def test_inherited_reinvestment_and_distribution_handling(tmp_path):
    file = write_history(tmp_path, statuses=["Processing", "Processing"])
    path = Path(file)
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("YOU BOUGHT Example (Cash)", "REINVESTMENT SOXX", 1)
    text = text.replace("YOU BOUGHT Example (Cash)", "DISTRIBUTION SOXX", 1)
    path.write_text(text, encoding="utf-8-sig")

    importer = make_importer()
    assert importer.identify(file)
    entries = importer.extract(file)
    assert len(entries) == 1
    assert entries[0].payee == "REINVESTMENT SOXX"
    assert entries[0].narration == "[SOXX] Configured semiconductor fund description"
    assert entries[0].postings[0].units == Amount(D("0.123"), "SOXX")
