# Beancount Red's Importers

Simple importers and tools for [Beancount](https://beancount.github.io/), software for
[plain text](https://plaintextaccounting.org/), double entry bookkeeping. _More
importantly, a framework to allow you to easily write your own importers._

### Introduction

This is a reference implementation of the principles expressed in
**[The Five Minute Ledger Update](https://reds-rants.netlify.app/personal-finance/the-five-minute-ledger-update/).**

Importers can be ugly and painful to write, yet are important in automating the grunt
work out of maintaining personal finance software. The philosophy is to make writing
sustainable, dependable importers easy. To achieve this, the design separates importers
in to three parts:

1. file format reader (reusable)
2. transaction builder (reusable)
3. institution-specific declarations and code (minimal, institution specific) <- _The
   only one you have to write_

This design helps move most of the heavy-lifting common code into (1) and (2) above.
Writing new importers is made easier since one only has to write code to address the
institution-specific formatting and quirks for each bank/brokerage. See working examples
of an [ofx based](https://github.com/redstreet/beancount_reds_importers/blob/main/beancount_reds_importers/importers/citi/__init__.py)
and [csv](https://github.com/redstreet/beancount_reds_importers/blob/main/beancount_reds_importers/importers/schwab/schwab_csv_brokerage.py)
based importers.

### Importers

File format readers included are:
- `.ofx`
- `.csv` (single and multitable support)
- `.xlsx` (single and multitable support)

Transaction builders included are:
- Banking (for banks and credit cards, which benefit from a postings predictor like
  [smart_importer](https://github.com/beancount/smart_importer).  Note that,
  depending on the institution, the `payee` and `narration` fields in generated
  transactions may appear to be switched. This is described by
  [libtransactionbuilder/banking.py](https://github.com/redstreet/beancount_reds_importers/blob/main/beancount_reds_importers/libtransactionbuilder/banking.py).
  and the fields can be swapped in a `custom_init`.
- Investments/brokerages (to handle the very many distinct cases of investment related
  transactions).
- Paychecks (to handle paychecks, which typically contain very many mostly
  pre-determined postings in a single entry).

[Input in `.ofx` format (over `.csv`) is preferred](https://reds-rants.netlify.app/personal-finance/a-word-about-input-formats-use-ofx-when-you-can/),
when provided by the institution, as it minimizes data and coding errors, eliminates
format breaking changes in .csv files, and typically includes balances that are used to
generate balance assertions, and commodity prices.

See [here](https://github.com/redstreet/beancount_reds_importers/tree/main/beancount_reds_importers)
for a list of institutions built-in. More investment, credit card, and banking
institutions will be added in the future. Contributions welcome.

### Tools and Utilities
These commands are installed as a part of the pip installation:

- `ofx-summarize`: Quick and dirty way to summarize a .ofx file, and peek inside it
- `bean-download`: [Download account statements automatically](https://reds-rants.netlify.app/personal-finance/direct-downloads/)
  (for supporting institutions), from your configuration of accounts. Multi-threaded.

The commands include shell auto-completion (tab-to-complete) via
[click](https://click.palletsprojects.com/en/8.1.x/shell-completion/). `bean-download`, in
particular, can complete the account or account groups you want to download, which can
be handy. To enable it, do:

```
mkdir -p ~/.zcomplete
_OFX_SUMMARIZE_COMPLETE=zsh_source ofx-summarize > ~/.zcomplete/ofx-summarize-complete.zsh
_BEAN_DOWNLOAD_COMPLETE=zsh_source bean-download > ~/.zcomplete/bean-download-complete.zsh

# Place this in your shell's rc file (.zshrc or .bashrc or .fishrc):
for f in ~/.zcomplete/*; do source $f; done
```

## Features
- supports [Beancount](https://github.com/beancount/beancount) output via `bean-extract`
  - should be easy to extend to ledger/hledger, etc. (contributions welcome)
- automatically generates [balance assertions](https://reds-rants.netlify.app/personal-finance/automating-balance-assertions/)
- support for:
  - investment accounts (brokerages including retirement accounts)
    - handles sweep funds, money market funds, and all standard brokerage transactions
  - banking and credit card
  - paychecks
- file format independent (ofx, csv, xlsx supported out of the box; single and
  multitable for csv and xlsx; write your own reusable handler if needed)
- supports commodity-leaf accounts
- see [The Five Minute Ledger Update](https://reds-rants.netlify.app/personal-finance/the-five-minute-ledger-update/)
  for automating downloads via `ofxclient`, connecting to `smart_importer` to
  auto-classify transactions, and more


## Installation
```
pip3 install beancount-reds-importers
```

Or to install the bleeding edge version from git:
```
pip3 install git+https://github.com/redstreet/beancount_reds_importers
```


## Running

### Running the included examples:
1. `cd <your pip installed dir>/example #eg: cd ~/.local/lib/python3.8/site-packages/beancount_reds_importers/example`
2. `./import.sh OfxDownload.qfx` # Imports investments
3. `./import.sh transactions.qfx` # Import bank transactions; uses smart_importer to classify transactions


### Creating and running your own config:
1. Create your own my.import. An example my.import is provided. At the least, include your account numbers
2. Include fund information. Copy the included `fund_info.py` to start with.
3. You can now run `bean-identify`, `bean-extract`, etc. See the included script: Run `./import.sh <your_input_ofx>`
4. If identifier/cusip/isin info is missing, the importer will let you know. Add it to your
   `fund_info.py` See
   [this article](https://reds-rants.netlify.app/personal-finance/tickers-and-identifiers/)
   for automating and managing identifier info

## Testing

Some importers are tested with
[regression_pytest.py](https://github.com/beancount/beancount/blob/v2/beancount/ingest/regression_pytest.py).
Run `pytest --generate` then `pytest`.

More broadly I run tests across hundreds of actual ofx and csv files, against
reference outputs that I know to be correct from my personal file. However, I'm
unable to share them since these are personal. Testing against real world files
is best, so I recommend you do this with your own input files.

## Contact
Feel free to post questions/concerns in the [Beancount groups](https://groups.google.com/forum/#!forum/beancount)
or on [The Five Minute Ledger Update](https://reds-rants.netlify.app/personal-finance/the-five-minute-ledger-update/)
site. For bugs, open an issue here on Github.

## Contributions
Contributions welcome. New importers for institutions and test input files appreciated.
Sharing importers helps the community.
