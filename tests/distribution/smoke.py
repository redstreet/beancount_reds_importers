"""Run from outside the checkout with a freshly installed distribution."""

import importlib.metadata
import subprocess
import sys
from pathlib import Path

from beancount import loader
from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.number import D

import beancount_reds_importers

PREFIX = Path(sys.prefix).resolve()
assert Path(beancount_reds_importers.__file__).resolve().is_relative_to(PREFIX)
assert importlib.metadata.version("beancount_reds_importers") == sys.argv[1]

for command in ("bean-download", "ofx-summarize", "reds-ibkr-flexquery-download"):
    subprocess.run([str(PREFIX / "bin" / command), "--help"], check=True, capture_output=True)
template = subprocess.check_output(
    [str(PREFIX / "bin/bean-download"), "config-template"], text=True
)
assert "[" in template

bank = Path("bank_XX234_Checking_Transactions_20250102.csv")
bank.write_text(
    '"Date","Status","Type","CheckNumber","Description","Withdrawal","Deposit","RunningBalance"\n'
    '"01/02/2025","Posted","INTADJUST","","Interest Paid","","$5.00","$5.00"\n'
)
broker = Path("broker_XX678_Transactions_20250102.csv")
broker.write_text(
    '"Date","Action","Symbol","Description","Quantity","Price","Fees & Comm","Amount"\n'
    '"01/02/2025","Buy","ABC","Example Fund","2","$10.00","","-$20.00"\n'
)

output = subprocess.check_output(
    [sys.executable, "import_config.py", "extract", str(bank), str(broker)],
    text=True,
)
ledger = (
    """
2025-01-01 open Assets:Bank USD
2025-01-01 open Assets:Broker:ABC ABC
2025-01-01 open Assets:Broker:USD USD
2025-01-01 open Income:Interest USD
2025-01-03 balance Assets:Bank 5 USD
2025-01-03 balance Assets:Broker:ABC 2 ABC
2025-01-03 balance Assets:Broker:USD -20 USD
"""
    + output
)
Path("imported.beancount").write_text(ledger)
entries, errors, _ = loader.load_string(ledger)
assert not errors, errors
transactions = [e for e in entries if isinstance(e, data.Transaction)]
assert len(transactions) == 2, output
bank_entry = next(e for e in transactions if e.narration == "Interest Paid")
assert bank_entry.postings[0].units == Amount(D("5"), "USD")
assert bank_entry.postings[1].units == Amount(D("-5"), "USD")
purchase = next(e for e in transactions if e.narration == "[ABC] Example Fund")
assert purchase.postings[0].units == Amount(D("2"), "ABC")
assert purchase.postings[0].cost.number == D("10")
assert purchase.postings[1].units == Amount(D("-20"), "USD")
subprocess.run([str(PREFIX / "bin/bean-check"), "imported.beancount"], check=True)
print(
    "Installed package: commands, banking import, investment import, and ledger balances passed."
)
