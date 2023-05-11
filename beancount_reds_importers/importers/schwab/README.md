## Notes on Schwab Importers

### schwab_csv_checking.py

The test file
[here](tests/schwab_csv_checking/schwab_Checking_Transactions_1234.csv) has two
subsections in its table of:
- Posted Transactions
- Pending Transactions

It also has this additional line:
```
Total Pending Check and other Credit(s)
```

The importer is currently not setup to extract these from the table. The importer works
on a different (perhaps active earlier?) incarnation of a Schwab Investor Checking
account banking file format.

TODO: determine exactly what type of Schwab account and exports schwab_csv_checking.py
works on.
