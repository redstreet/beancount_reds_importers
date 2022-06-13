# Changelog

## (unreleased)


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
