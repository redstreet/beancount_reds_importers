# Fidelity standalone account CSV

For Fidelity standalone account history CSVs, use `fidelity_standalone_csv` to
import only rows whose `Cash Balance ($)` is `Processing`:

```python
from beancount_reds_importers.importers.fidelity import fidelity_standalone_csv

# Use your normal investment account configuration.
config["account_number"] = "5678"  # Full account numbers also work.
importer = fidelity_standalone_csv.Importer(config)
```

This importer extends `fidelity_all_accounts_csv`, sharing its transaction
handling, fund lookup, and transaction exclusions.

The last four digits of `account_number` must match the account suffix in
`History_for_Account_12345678.csv`. Settled rows are excluded, and this importer
does not emit balance assertions. Sales use the usual investment importer lot
selection workflow.

Fund descriptions come from `config["fund_info"]["fund_data"]`, using the CSV's
symbol to look up each `(ticker, security_id, description)` tuple by ticker.
Pass the fund info loaded from your commodity file, as for the other investment
importers. A missing ticker produces a fund-info error listing missing symbols.
