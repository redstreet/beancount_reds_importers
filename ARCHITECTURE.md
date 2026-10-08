_This is an AI generated file, useful for AI to read_

# Architecture

This repo is a Beancount/Beangulp importer framework plus a large library of ready-made institution importers.

## What It Is

- Core purpose: convert downloaded financial files (`.ofx/.qfx`, `.csv`, `.xlsx`, `.pdf`, `.xml`, etc.) into Beancount entries.
- Design is explicitly 3-layered: reader + transaction builder + institution-specific glue (documented in [README.md](README.md)).

## How It’s Structured

- Reusable file readers in [`libreader/`](beancount_reds_importers/libreader):
  - Base interface: [reader.py](beancount_reds_importers/libreader/reader.py)
  - Format implementations: [ofxreader.py](beancount_reds_importers/libreader/ofxreader.py), [csvreader.py](beancount_reds_importers/libreader/csvreader.py), [pdfreader.py](beancount_reds_importers/libreader/pdfreader.py), [xmlreader.py](beancount_reds_importers/libreader/xmlreader.py), etc.
- Reusable transaction builders in [`libtransactionbuilder/`](beancount_reds_importers/libtransactionbuilder):
  - Base: [transactionbuilder.py](beancount_reds_importers/libtransactionbuilder/transactionbuilder.py)
  - Domain logic: [banking.py](beancount_reds_importers/libtransactionbuilder/banking.py), [investments.py](beancount_reds_importers/libtransactionbuilder/investments.py), [paycheck.py](beancount_reds_importers/libtransactionbuilder/paycheck.py)
- Institution modules in [`importers/`](beancount_reds_importers/importers) (47 importer classes), usually very thin customizations.

## Core Pattern (Most Important)

- Institution importers use multiple inheritance to combine:
  - a reader mixin (file parsing/normalization)
  - a transaction builder mixin (Beancount entry construction)
- Example:
  - [citi importer](beancount_reds_importers/importers/citi/__init__.py): `class Importer(banking.Importer, ofxreader.Importer)`
  - [schwab csv importer](beancount_reds_importers/importers/schwab/schwab_csv_brokerage.py): `class Importer(csvreader.Importer, investments.Importer)`

## Runtime Flow

1. `identify(file)` checks extension + filename/header/account matching.
2. reader `read_file()` parses and normalizes source rows/transactions.
3. builder `extract()` maps normalized data to Beancount transactions, balances, prices, metadata.
4. `beangulp.Ingest(CONFIG)` runs this over files (see [example/import.py](beancount_reds_importers/example/import.py)).

## Config-Driven Behavior

- Importers are mostly configured by dicts: account numbers, account targets, type mappings, fund metadata, filename patterns, balance date policy, etc.
- Investments rely heavily on `fund_info` and account templates with variables like `{ticker}` / `{currency}`.

## Testing + Tooling

- Regression-style tests compare generated outputs to checked-in fixtures (`.extract/.date/.filename/.account`), via [regression_pytest.py](beancount_reds_importers/util/regression_pytest.py).
- CLI utilities:
  - [ofx_summarize.py](beancount_reds_importers/util/ofx_summarize.py)
  - [bean_download.py](beancount_reds_importers/util/bean_download.py) (+ `needs-update` helper)

## Optional Deep Dive

If needed, the next useful extension for this document is an end-to-end walkthrough of one importer (for example Schwab CSV or IBKR XML), showing exactly which methods to override when adding a new institution importer.
