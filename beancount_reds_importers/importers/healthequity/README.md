# HealthEquity HSA cash importer

For HSA cash-only accounts managed by HealthEquity.

Copy-pasting the transactions on website into a file along with the header. Name it
hsa.tsv or hsa.txt. It will look like:

```text
Date    Transaction    Amount    HSA Cash Balance    Attachments
```

Parenthesized amounts are treated as withdrawals. Transactions containing `Contribution`
are skipped; record those separately, such as through your payroll importer. The closing
balance assertion still includes the effect of contributions.

## Sample configuration

With `smart_importer` installed, use `PredictPostings` to predict counterpart postings
from your existing ledger:

```python
import beangulp
from smart_importer import PredictPostings

from beancount_reds_importers.importers import hsa

CONFIG = [
    PredictPostings().wrap(
        hsa.Importer({
            "main_account": "Assets:HSA:Cash",
            "currency": "USD",
            "filename_pattern": r"hsa\.(txt|tsv)$",
        })
    ),
]

if __name__ == "__main__":
    beangulp.Ingest(CONFIG)()
```

Replace `Assets:HSA:Cash` with your ledger account. The filename pattern is optional;
the importer also checks the column headers.
