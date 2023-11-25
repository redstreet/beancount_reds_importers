# Changelog

## (unreleased)


### Improvements

- Handle the INVEXPENSE field (#79) [Jacob Farkas]
  * Handle the INVEXPENSE field
  * Rename the 'expenses' property to 'invexpense' to match the OFX tag
- handle 'fee' ofx type in investments. [Red S]
- configurable balance assertion dates. [Red S]
- smarter balance assertion dates. [Red S]
  We find the statement's end date from the OFX file. However, banks and
  credit cards typically have pending transactions that are not included
  in downloads. When we download the next statement, new transactions may
  appear prior to the balance assertion date that we generate for this
  statement. To attempt to avoid this, we set the balance assertion date
  to either two days before the statement's end date or the last
  transaction's date, whichever is later.
- needs_update: add --all-accounts. [Red S]

### Fixes

- update requirements.txt; also replace == with >= #87. [Red S]
- #85, balance dates were returning function instead of date. [Red S]
- update unit tests to match smart date. [Red S]
- add 'xfer' to ofx types. [Red S]
- make "invexpense" optional with a smart default. [Red S]
- resolved several gotchas with balance assertion dates with ofx files. [Red S]
- #80 document xlrd requirement. [Red S]
  xlrd is optional, and thus not in requirements.txt, but is needed for
  xls files and for testing



## 0.7.0 (2023-08-28)

### New Features

- bean-download needs-update to determine accounts needing an update based on the latest
  balance assertion in the journal. [Red S]

### New Importers

- Fidelity cma csv importer (#47) [kantskernel]
  * adding support for importering Fidelity Cash Management Acct (checking). CSV.
  * cleaned up importer and merged required csvreader change with the version from main

- add Schwab CSV Positions importer. [Red S]

### Breaking Changes
- reorganized directories. Changes import lines. [Red S]

  Change your import lines from:

  1. For most importers
  from beancount_reds_importers import fidelity
  to:
  from beancount_reds_importers.importers import fidelity

  2. For institutions with alternative importers:
  from beancount_reds_importers.importers.schwab import schwab_csv_balances, schwab_csv_brokerage

  BREAKING CHANGE: users will need to change import lines

### Improvements

- Improve Vanguard support. [Matt Brown]

  Remove noisy Vanguard memos. Show Vanguard transaction type as payee.
- Add 401k support to investments. [Matt Brown]

  Support 401(k) source sub-accounts in account config values.

  Add some human-readable error handling if a config variable is missing.
- add get_tags to transactionbuilders (#68) [Sarah E Busch]

  * feat: add get_tags to banking.py

  * feat: add get_tags to investments.py

  * feat: add get_tags to paycheck.py
- schwab_csv_brokerage: more descriptive payee/memo. [Red S]
- tests: tests for schwab_csv_brokerage #59. [Red S]

  With these tests, #59 is reproduced. Fix pending.
- overridable target account in banking importer. [Red S]
- get_available_cash now takes as input settlement_fund_balance. [Red S]

  different institutions seem to compute this in different ways.
  overridable method now includes settlement_fund_balance for use if
  needed in importers
- use filing_account to file. [Red S]
- overridable main_account in banking. [Red S]
- overridable currency and date fields in csvreader. [Red S]
- remove double quotes from column headers. [Red S]
- SCB/UOB: add 'convert_currencies' as an option; fix conversions. [Red S]
- check for account number in csv files. [Red S]

  added untested, commented out code for xls
- perform table extraction in csvreader; scbbank now uses it. [Red S]

  Start at a given header, and extract a table until either the end of the
  file or until a blank line occurs.

  Useful high level extractor.
- scb/uob: enable custom header; xls/xlsx: respect header. [Red S]
- relax header finding condition in csv. [Red S]
- united overseas bank (uob) importers: card, srs. [Red S]
- standard chartered importers (bank, card) [Red S]
- united overseas bank csv importer. [Red S]
- xls reader (previous one was xlsx reader) [Red S]
- enable price conversions in banking transaction builder. See #38. [Red S]
- default currency to CURRENCY_NOT_CONFIGURED. [Red S]
- csvreader now can search for the header. [Red S]

  Eliminates the need to skip a set number of head/tail lines.
- attempt to get currency from input file instead of config. [Red S]
- Improve 401k and Vanguard support [Matt Brown]

### Fixes

- intergrate needs_update into bean-download cli. [Red S]
- file_account was returning '{ticker}'. refactored config vars. [Red S]

  TODO: refactor setting config vars better. format_raw_account() is
  closely related.
- uobbank importer: add unit tests, fix several issues #70. [Red S]

  - decimal places
    - still needs a full solution. The problem is, petl uses xlwt/xlrd to
      read excel, which use excel datatypes, which we don't want, as we
      want just the string, which we can then pass on to decimal.decimal
    - not sure exactly how decimals are stored in excel

  - don't end up with long floats
- ignore xls spurious warning #70. [Red S]

  - ignore WARNING *** file size (92598) not 512 + multiple of sector size (512)
- vanguard importer: clean up repeated memo. [Red S]
- filter out XMLParsedAsHTMLWarning from ofxparse. #40. [Red S]

  https://github.com/jseutter/ofxparse/issues/170
  https://github.com/jseutter/ofxparse/pull/108
- schwab_csv_checking: add tests, and fixes #63. [Red S]

  - fixed skipping "pending transactions" rows
  - move Balance namedtuple from importers to banking.py
- #52 unit price immutable. [Red S]
- schwab_csv_brokerage transfers #59. [Red S]
- counter -> next(counter) #62. [Red S]
- add 'Qualified Dividend' type to Schwab CSV Brokerage #60. [Red S]
- allow file_date() to be called without initialization #61. [Red S]
- minor fixes to schwab_csv_brokerage. [Red S]
- unitedoverseas xls doesn't convert amounts in strings. [Red S]
- remove special chars from column names. [Red S]
- ugly hack to handle #41 until that is resolved upstream. [Red S]
- banking: don't call self.build_metadata unless there is metadata. [Red S]
- scbcard: ignore unposted. [Red S]
- securities not found handling IndexError exception not caught. [Red S]
- Merge pull request #77 from mariolopjr/main. [Red S]

  Add buydebt which corresponds to CD for Fidelity
- add buydebt which corresponds to CD for fidelity. [Mario Lopez]

- #48 clean up get_balance_positions() [Red S]
- default currency to CURRENCY_NOT_CONFIGURED. [Red S]
- uobbank withdrawal/deposit. [Red S]
- typo in vanguard_screenscrape.py. [Wiebe Stolp]

### Other

- bean_download: catch config not in file gracefully. [Red S]
- style: Short-circuit in investments initialize to reduce indentation. [Matt Brown]
- test: Add Vanguard 401(k) test (#65) [Matt Brown]
- Add test for capitalonebank, which also demonstrates #57 (#58) [Matt Brown]
- Importer.extract: Explicitly name args to Transaction (#55) [Matt Brown]

  This shows that payee and narration are switched, as documented.
  https://github.com/beancount/beancount/blob/v2/beancount/core/data.py is
  the reference. This confused my use of smart_importer completion from an
  existing ledger and took me some time to figure out.

  I think the arguments should be swithed but I can see this would be
  difficult to do while maintaining backwards compatibility.
- Add a simple regression test for the ally importer. (#56) [Matt Brown]

  This uses a copy of transactions.qfx from example/.
- chore: directory structure. [Red S]

  ---------


## 0.6.0 (2023-01-22)

### New Importers

- add schwab_checking_csv. [Red S]
- importer: amazon gift card importer. [Red S]
- add Discover credit card csv importer. [Red S]
- importer: add capitalone 360 ofx. [Red S]
- add becu (Boeing Employees Credit Union) (#34) [Patrick Baker]

### Improvements

- Better missing security reporting (#43) [thehilll]

  * if get_ticker_info_from_id finds an id not present in fund_info.py try to use self.ofx.security_list
  to report more useful information.  At least in Fidelity ofx files both the symbol and security name
  are present, so in most cases the required additions to fund_info.py are already in the file.

  * Slightly better reportings...print a summary line before list of securities

  * remove unused f string

  * 1. Comments to explain what is going on
  2. Key the extracted securities dict by CUSIP (not symbol) which matches what is found
       in the transaction entries (not for bonds symbol generally matches CUSIP)
  3. Values of dict are now a tuple of (symbol, cusip, name) which for stocks should be all
       that is needed for fund_info.py

  * Remove another unnecessary f string

- Convert value to str before applying regex in remove_non_numeric (#32) [Balazs Keresztury]
- add overridable security_narration() method; use it in Fidelity. [Red S]
- add ability to use smart importer with investments (#36) [Patrick Baker]
- bean-download accepts a comma separated institution list. [Red S]
- bean-download display. [Red S]
- add skip_transaction to banking. [Red S]
- minor: workday importer now specifies filing account. [Red S]
- minor: add overridable post process step for csv. [Red S]
- minor: add etrade to direct download template. [Red S]
- minor: Chase filename regex is now [Cc]hase. [Red S]
- minor: allow overriding payee in investments. [Red S]

### Fixes

- fidelity rounding errors are frequently higher than current value. [Red S]
- date format wasn't getting set during bean-file. [Red S]
- #41 add 'check' to ofx transaction types. [Red S]
- #41 add 'payment' to ofx transaction types. [Red S]
  for investment accounts with banking features
- #40 check if ofx file provides balances instead of assuming it does. [Red S]
- #37 document `filename_pattern` in the demo example. [Red S]
- schwab_csv: update csv fields; custom payee. [Red S]
- csvreader returned blank when skip_comments was not present. [Red S]
- handle vanguard annoyance. [Red S]
- workday: skip last row to zero. [Red S]
- banking: fix the payee/narration order issue caused by 9057fcf j 9057fcf: #33. allow importers to override payee and narration fields. [Red S]
- catch ofxparse exceptions. [Red S]
- fix; schwab_checking_csv: withdrawals should be negative. [Red S]
- schwab_csv bug fixes. [Red S]
- #33. allow importers to override payee and narration fields. [Red S]
- when matching ofx security_id to funds_db prefer a complete match, if none found fall back to substring (#45) [thehilll]


## 0.5.1 (2022-06-14)


### Improvements

- util: bean-download: display download progress bars; pretty output. [Red S]
- util: bean-download template improvements. [Red S]

  - separate template file
  - working examples
- util: ofx_summarize: sort by date. [Red S]

### Other

- build: deps quoting. [Red S]
- build: requirements; gitchangelog. [Red S]
- doc: add changelog, and gitchangelog config. [Red S]
- doc: gitchangelog exclude 'feat' [Red S]
- README updates. [Red S]
- refactor: print verbose. [Red S]


## 0.5.0 (2022-06-07)
### Features
- New importer: vanguard screenscraped. [Red S]
- New util: `ofx-summarize`: Quick and dirty way to summarize a .ofx file, and peek inside it
- New util: `bean-download`: [Download account statements automatically](https://reds-rants.netlify.app/personal-finance/direct-downloads/)
  (for supporting institutions), from your configuration of accounts. Multi-threaded.

### Improvements
- Add a single-table xlsx reader (#24) [Gary Peck]
- feat: Add a build_metadata function that can be overridden by custom importers [savingsandloan]
- doc: Updated README for new tools, features. [Red S]
- Make sorting of paycheck postings configurable (#21) [Gary Peck]
- Bean-download: add --institutions alias. [Red S]
- Bean-download: shell completion for sites! [Red S]
- Rename bean-ingest to bean-download. [Red S]
- Consider isin to be a substring. [Red S]
- Support custom entries (commodities, open/close, etc.). see #30. [Red S]
- Csv_multitable_reader: add head/tail skipping, comments (#27) [savingsandloan]
- Vanguard: catch capital gains distributions using description. [Red S]
- Rename capgains_lt to capgainsd_lt (distribution) [Red S]
  BREAKING CHANGE
- Add settleDate to csv. [Red S]
- Allow filename_pattern override via config. [Red S]
- Change filename_identifier_substring to regex pattern. [Red S]
- Schwab defaults. [Red S]
- Commodity_leaf: filing string. [Red S]
- Commodity_leaf is now configurable via string replacement. [Red S]
- Schwab file name. [Red S]
- Add IMPORTER_NAME for debugging. [Red S]
- Schwab_csv_balances: support more general filenames. [Red S]
- Schwab csv importer: add more transaction types. [Red S]
- Add ticker to get_target_acct_custom() [Red S]
- commodity_leaf is now configurable via replacement of '{ticker}' and '{currency}'
  strings. See comments in libtransactionbuilder/investments.py for more info

  BREAKING CHANGE: you will need to rewrite your .import file with the strings above!


### Fixes
- Handle sign flipping for all account types in paycheck importer (#20) [Gary Peck]
- Fix missing return value in xlsx_multitable_reader.is_section_title() (#18) [Gary Peck]
- Bean-ingest: asyncio was not working correctly. [Red S]
- Metadata fixes. [Red S]
- Investments: generate balance + price entries even if end_date is missing. [Red S]
- Fix bug mentioned in #26 (use cash_account for cash transfers) [Red S]
- Fix bug causing ofxreader to fail on multiple calls by bean-extract. [Red S]
- Fix bug that read the same file upon multiple calls from bean-extract. [Red S]
- Fix target account for buy/sell. [Red S]
- Fix csvreader identification bug. [Red S]
- Fix several commodity leaf account bugs. [Red S]
- File_date was not returning value. [Red S]
- Add and expose handler for price and cost both zero. Closes #15. [Red S]

### Other
- Pythonpackage workflow. [Red S]
- Disable pytests. [Red S]
- Beta. [Red S]
- Update example to support {} strings; doc. [Red S]
- Reworked get_target_acct_custom. [Red S]
  BREAKING CHANGE: now, get_target_acct_custom() will be allowed to either return a
  target account (for special cases), or return a None, which will allow the default
  implementation to run
- Cleanup extraneous get_target_account_custom from ameritrade, etrade. [Red S]
- Rename master to main. [Red S]
- Disable pytest. [Red S]
- Refactor commodity leaf. [Red S]
- Removed redundant common.py. [Red S]



## 0.4.1 (2021-09-30)
## 0.4 (2021-04-18)
## 0.2.3 (2021-02-02)
## 0.2.2 (2021-01-30)
## 0.2.1 (2021-01-30)
### Major Features
 - added the commodity_leaf feature: by default, accounts will now include a commodity
   as their leaf (eg: Assets:Investments:HOOLI). This is configurable. Simply pass in a
   'commodity_leaf: False' in your importer config.

 - the source reader (eg: ofx, csv, ...) has now been separated from the importer type
   (eg: investment, banking, ...). This allows us easy combining of these.

## 0.2.0 (2021-01-30)
## 0.1.2 (2020-06-14)
## 0.1.1 (2020-06-14)
