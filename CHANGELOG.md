# Changelog

## [1.0.0](https://github.com/redstreet/beancount_reds_importers/compare/0.10.0...1.0.0) (2026-11-08)


### Features

* ad blueshield EOB importer and collective haealth ([2ca0895](https://github.com/redstreet/beancount_reds_importers/commit/2ca08959c919e64ea2a94bb8a8558edbe7b4e10c))
* add ARCHITECTURE.md ([25559d8](https://github.com/redstreet/beancount_reds_importers/commit/25559d82168ebde76aa9ffcfe0eb9bfcec86dd26))
* add deduplication to multiplexer importer. [#184](https://github.com/redstreet/beancount_reds_importers/issues/184) ([051b106](https://github.com/redstreet/beancount_reds_importers/commit/051b106a839987c76fd790b28e3c6e66cb01cd3c))
* add fidelity_all_account_positions_csv ([80e956d](https://github.com/redstreet/beancount_reds_importers/commit/80e956deea4402fa9eefe37b857d052f3e2aaab9))
* add get_links() to TransactionBuilders ([#166](https://github.com/redstreet/beancount_reds_importers/issues/166)) ([c0f5bab](https://github.com/redstreet/beancount_reds_importers/commit/c0f5bab392a1b77d86e22585ac9eddff03c85a1c))
* add healthequity HSA importer ([102b537](https://github.com/redstreet/beancount_reds_importers/commit/102b5375691f058a990a9959ae66f44aaaa29a32))
* add logging to account matching ([243ace1](https://github.com/redstreet/beancount_reds_importers/commit/243ace1e81b32cc9f55f34b2613a1e9f2c35ac4c)), closes [#135](https://github.com/redstreet/beancount_reds_importers/issues/135)
* add transaction type to schwab_csv_brokerage ([b478b10](https://github.com/redstreet/beancount_reds_importers/commit/b478b105f1b366b25599171e831551990c76f27b))
* add unit tests ([48820a1](https://github.com/redstreet/beancount_reds_importers/commit/48820a111c7fec7d9e7d6b2f439847db1759a254))
* additional transaction types in fidelity_all_accounts_csv ([de5fa56](https://github.com/redstreet/beancount_reds_importers/commit/de5fa5635454012a7c850a24d452a875de10f794))
* allow custom modifications to imported transactions ([4daf442](https://github.com/redstreet/beancount_reds_importers/commit/4daf4422486ef00537ca5b9e97f7d99183e59e07))
* amazon gift card: book to returns if amount is &gt; 0 ([c0e8923](https://github.com/redstreet/beancount_reds_importers/commit/c0e89235048318ce125c110629d7345ece14d177))
* amazon_giftcard now adds a balance assertion at the end ([b0ef3aa](https://github.com/redstreet/beancount_reds_importers/commit/b0ef3aa1a58a3cafb33b4f5a86534f0d4bd89f18))
* amazon_giftcard: fall back to pdb if parsing fails ([04e95c2](https://github.com/redstreet/beancount_reds_importers/commit/04e95c29f9fd0683f62147c591272a684a0cda7c))
* amazon_orders: add payment instrument type as metadata ([cdbaefd](https://github.com/redstreet/beancount_reds_importers/commit/cdbaefdca8443aba5686eaf506fb699ca246002d))
* consolidate Amazon importers ([8653323](https://github.com/redstreet/beancount_reds_importers/commit/8653323ac9366a603eafff80adb8d9c02005d068))
* copy beancount v2.0 regression test helper ([c22d66c](https://github.com/redstreet/beancount_reds_importers/commit/c22d66c894aac977ff2fac0a72fcb2befd541d6a))
* **csv:** make delimiter configurable ([ebdd2b1](https://github.com/redstreet/beancount_reds_importers/commit/ebdd2b1dca262ceb7484b7b5b9e3380688504a21))
* **fidelity:** import processing standalone account transactions ([af8d46f](https://github.com/redstreet/beancount_reds_importers/commit/af8d46f3e0212ef2241760c94a345564b41e24e2))
* genericpdfpaycheck automatically replace periods in header ([87b6919](https://github.com/redstreet/beancount_reds_importers/commit/87b6919f226d372c70a0dce2a8cc0bd7b6e4a5de))
* ibkr: add options expiry detection ([fd5708a](https://github.com/redstreet/beancount_reds_importers/commit/fd5708afc45eab6c8f5568fe106b01fa9797089a))
* IBKR: handle cash transfers in flex query ([976baeb](https://github.com/redstreet/beancount_reds_importers/commit/976baebdb1ad742a6b04d111d4fb03b8aad0faea))
* make the record currency available ([2fcf6ca](https://github.com/redstreet/beancount_reds_importers/commit/2fcf6ca4f0590ab1416ed3b3e46a5eddbe8cda20))
* map more actions to types ([1edbd12](https://github.com/redstreet/beancount_reds_importers/commit/1edbd122956d96fa4cdd956b91ebb3df33604677))
* modify regression_test to use beangulp ([850b6e6](https://github.com/redstreet/beancount_reds_importers/commit/850b6e6dd6b9628a9c919e16fcd430bcc5f4e34b))
* multi-account support for ibkr ([93ce5ad](https://github.com/redstreet/beancount_reds_importers/commit/93ce5add8c188ffce0c574a3d0907a534f21e772))
* multiplexer importer, quick and dirty version [#122](https://github.com/redstreet/beancount_reds_importers/issues/122) ([ad99682](https://github.com/redstreet/beancount_reds_importers/commit/ad99682f599dec14ce1630d2061753e2a34353d0))
* needs_update: display recency threshold; allow threshold in config ([da3ddc3](https://github.com/redstreet/beancount_reds_importers/commit/da3ddc374c9bd0755958c808dfd13747dd3718f1))
* needs_update: support for per-account recency thresholds ([428e303](https://github.com/redstreet/beancount_reds_importers/commit/428e303efcd03c90028fb2cdbcc616ee30720219))
* parse OFX security list to auto populate fund data ([1502a56](https://github.com/redstreet/beancount_reds_importers/commit/1502a56deafbd5c77c4bb7aabeb34e3330f14251))
* sort fidelty transactions by the implicit order of appearance ([2469810](https://github.com/redstreet/beancount_reds_importers/commit/2469810e5aab37696836d5b37082ca470cf56b41))
* update tests to use modified regression_test ([b8ee5a9](https://github.com/redstreet/beancount_reds_importers/commit/b8ee5a98d5f38a0c951e245532ce2fab0981ad2d))
* use record currency if available ([2507fe4](https://github.com/redstreet/beancount_reds_importers/commit/2507fe4cfb361be79ead67c2db3363b6294009f5))


### Bug Fixes

* add __init__.py to amazon ([8a08853](https://github.com/redstreet/beancount_reds_importers/commit/8a08853a5839636428ff2bc5cd0fd0a508147560))
* add dependency on beangulp ([640ae79](https://github.com/redstreet/beancount_reds_importers/commit/640ae79a73a668d9fd8d2c405ed3c0e8d5bb7735))
* add more fidelity transaction types [#170](https://github.com/redstreet/beancount_reds_importers/issues/170) ([bcf7ad4](https://github.com/redstreet/beancount_reds_importers/commit/bcf7ad446dc89f8ffb76624dd977256f3a078bed))
* address issues reported by `pytest` ([aebe955](https://github.com/redstreet/beancount_reds_importers/commit/aebe95593f9b9f1f2920e053a6b7c3bc30307dba))
* amazon gdpr upstream files and formats changed ([6653d71](https://github.com/redstreet/beancount_reds_importers/commit/6653d7166da1ad6a597554dd9266bb4a04fad1dc))
* amazon_* import fixes; returns: skip transactions ([58c26f3](https://github.com/redstreet/beancount_reds_importers/commit/58c26f360c6a409495b69633444f83b1ce465d34))
* amazon_gdpr upstream change to zip structure ([1c6ddb9](https://github.com/redstreet/beancount_reds_importers/commit/1c6ddb9c7db1a7b16304b5e318e549164334e904))
* amazon_giftcard `is None` bug ([1b764e6](https://github.com/redstreet/beancount_reds_importers/commit/1b764e67cffa25ece9cd98da17829eacb2094785))
* amazongc (amazon gift card scrape) importer: fix for beangulp ([b8c81da](https://github.com/redstreet/beancount_reds_importers/commit/b8c81da63fee2628b08df25b2abe5c4e0defe598))
* amazongc importer (define account()) ([8a58ca8](https://github.com/redstreet/beancount_reds_importers/commit/8a58ca86fd6e7c3d094667615d4cbe584a34f61e))
* broken example with updated smart_importer ([fe3cd12](https://github.com/redstreet/beancount_reds_importers/commit/fe3cd1209db175f2307e32a87edadee1797df604))
* collective: ignore ADJUSTED transactions ([b88e6ed](https://github.com/redstreet/beancount_reds_importers/commit/b88e6ed649baef1208922881bda3a70e53995c1d))
* csvreader: make header case insensitive ([05b6d46](https://github.com/redstreet/beancount_reds_importers/commit/05b6d4641c1b8f676886da6384426d512e1a06ba))
* examples ([1029d63](https://github.com/redstreet/beancount_reds_importers/commit/1029d63e5778f653d2fe3d58203e49c896bbd40f))
* fidelity csv upper case ([85a6987](https://github.com/redstreet/beancount_reds_importers/commit/85a69873d5ddcf130961fa105190e3af2ac95771))
* fidelity_all_accounts_csv: add direct rollover ([5666f65](https://github.com/redstreet/beancount_reds_importers/commit/5666f651b3f7b5a4da93da9d67a257837261a514))
* file -&gt; filename deprecation in fidelity_brokerage_csv ([7c13f7a](https://github.com/redstreet/beancount_reds_importers/commit/7c13f7aaff59e9baf2d44023d6d7a4678a06785b))
* file.name -&gt; file for beangulp ([983482f](https://github.com/redstreet/beancount_reds_importers/commit/983482f53e6a88078c1379e7d589d3e0d5f36267))
* honor Excel number formatting for currency precision ([028b788](https://github.com/redstreet/beancount_reds_importers/commit/028b788b2822f19885b221f446d553153865f2f3))
* ibkr importer: sell action name ([#138](https://github.com/redstreet/beancount_reds_importers/issues/138)) ([e5b49fb](https://github.com/redstreet/beancount_reds_importers/commit/e5b49fb9319a0dcac2fefb76b23e724ee7f1c3f5))
* IBKR importer: update FlexQuery field names and ordering ([#137](https://github.com/redstreet/beancount_reds_importers/issues/137)) ([3a0d263](https://github.com/redstreet/beancount_reds_importers/commit/3a0d263422f868a2359109ea55ae51616e544162))
* ibkr: exit with meaningful output if unable to parse ([c16384b](https://github.com/redstreet/beancount_reds_importers/commit/c16384bd2ed5776c469846f44ba20319bb769b4f))
* initialize commissions to 0 in addtion to fees ([4db5aeb](https://github.com/redstreet/beancount_reds_importers/commit/4db5aeb3da565e87b9780108ed5e1ac810f52679))
* investments: manually compute unit_price if missing ([cbc75f9](https://github.com/redstreet/beancount_reds_importers/commit/cbc75f956b9872bf78e61f6db7afdfb808f0bbbb))
* list pytest as dev dependencies ([0400d3d](https://github.com/redstreet/beancount_reds_importers/commit/0400d3de29eb5949b0e41dc206b86aed010e1453))
* map DIVIDENDS action type ([199798c](https://github.com/redstreet/beancount_reds_importers/commit/199798c23d21d513e1647ef867f007da85f7d477))
* **mercurycards:** restore regression tests and initialize statement dates ([4729cb6](https://github.com/redstreet/beancount_reds_importers/commit/4729cb6515b28945a505c6c43c4b5bd9f181bca7))
* minor ([97ff3f8](https://github.com/redstreet/beancount_reds_importers/commit/97ff3f81b16c47a4f7b5aa3f4152ec0e9a83f344))
* multiplexer doesn't work when there are multiple in one's CONFIG ([6324764](https://github.com/redstreet/beancount_reds_importers/commit/6324764c19ddd8e8a98e30b502cd39ea832a4094))
* need to reinitialize if file is different [#120](https://github.com/redstreet/beancount_reds_importers/issues/120) ([34b6b7e](https://github.com/redstreet/beancount_reds_importers/commit/34b6b7e3157519bf43b6f5e2f91e59e37d1f4b5b))
* perms ([977c191](https://github.com/redstreet/beancount_reds_importers/commit/977c1919f4a302416fd1cb951118c3c6c37461de))
* remaining readers convert to beangulp ([c9630fa](https://github.com/redstreet/beancount_reds_importers/commit/c9630faead90e526b7f7b8620355d9f7d1c3fc9c))
* remove ahoy ([81065b0](https://github.com/redstreet/beancount_reds_importers/commit/81065b0a1b3db361c477e7beb1f56ae256296baf))
* remove build_metadata (it's there in libtransactionbuilder) ([8d1b84d](https://github.com/redstreet/beancount_reds_importers/commit/8d1b84dbfac37dbde309f52d171016286f3d01bd))
* remove comment [#165](https://github.com/redstreet/beancount_reds_importers/issues/165) ([e74ac84](https://github.com/redstreet/beancount_reds_importers/commit/e74ac845124be57ad5af9bb1a291585d6ec1a782))
* remove empty tag before ofxparse parsing ([b80502e](https://github.com/redstreet/beancount_reds_importers/commit/b80502e857edb1203f15653e7eae581c001b0f09))
* return `None` when no transactions exist for balance assertions ([74a5732](https://github.com/redstreet/beancount_reds_importers/commit/74a57325d50ac969a6fa67309cab97f0de5a3063))
* run `isort --profile black` ([0fd950b](https://github.com/redstreet/beancount_reds_importers/commit/0fd950b463c8caf409532cc52031faea1091e04c))
* run `ruff check` and address reported issues ([da118ce](https://github.com/redstreet/beancount_reds_importers/commit/da118cec9e914f8e5ad7c0b6145f95d5c62db852))
* run `ruff format` ([1537298](https://github.com/redstreet/beancount_reds_importers/commit/15372988352f4804d943eb7cea23043a88fba9c2))
* schwab PAL changed labels ([dfcdef1](https://github.com/redstreet/beancount_reds_importers/commit/dfcdef157ace134dc7d4ad23b9c3c958d6bd6324))
* schwab positions importer: ignore total line ([09993d7](https://github.com/redstreet/beancount_reds_importers/commit/09993d755f9a5ec8acc0a292e10e27ad0af3ebc2))
* schwab_csv_positions format seems to have changed ([04a03b4](https://github.com/redstreet/beancount_reds_importers/commit/04a03b43eadd901a55d3067cf6ca9bd710fc97a5))
* schwab_csv_positions: fields update ([3f2aff0](https://github.com/redstreet/beancount_reds_importers/commit/3f2aff07df57f0afed31f98363a8c27330323394))
* support Fidelity RECEIVED FROM stock transfers ([d752fed](https://github.com/redstreet/beancount_reds_importers/commit/d752fed39a769e72ba86d8631774e67e6683df8f))
* **tests:** correct HealthEquity imports and expectations ([1bc6bb8](https://github.com/redstreet/beancount_reds_importers/commit/1bc6bb81736cd589a6b60ab0b012b4546eb46192))
* unit tests for fidelity's output ordering ([2d7770d](https://github.com/redstreet/beancount_reds_importers/commit/2d7770d06a1d1438440a629e2ad786da41a02abc))
* update importer functions to match new names ([d5f636e](https://github.com/redstreet/beancount_reds_importers/commit/d5f636e3cd3e3970a9fcce42cb97020e39ef9381)), closes [#131](https://github.com/redstreet/beancount_reds_importers/issues/131)
* update pdfreader to work with pdfplumber &gt;  v0.11.5 ([c3290bd](https://github.com/redstreet/beancount_reds_importers/commit/c3290bd81152b1a52d668b1738dfcef3f2353d3f))
* upgrade to compatible with beancount v3 ([bbac420](https://github.com/redstreet/beancount_reds_importers/commit/bbac4207121d0a737f57c6b587dffb287246c53d))
* upper case for consistency ([a8ba10e](https://github.com/redstreet/beancount_reds_importers/commit/a8ba10e812560a46c5724fd2ef6e5695f8910c78))
* uppercase all actions ([70f4c57](https://github.com/redstreet/beancount_reds_importers/commit/70f4c57682b3775230437ff54446cbc295cdc4a1))


### Documentation

* clarify xlsx formatting note in currency precision section ([1ca6124](https://github.com/redstreet/beancount_reds_importers/commit/1ca612437873accba3535b9418a8c0a4a2c8479d))
* correct the module in the example ([21ea7ff](https://github.com/redstreet/beancount_reds_importers/commit/21ea7ff79156f1fabe4a642c550105f6a535e285))
* explain direct pushes release automation and publisher setup ([322bef7](https://github.com/redstreet/beancount_reds_importers/commit/322bef74f30c5025c36665d91302e53b6fbf8bb3))


### Continuous Integration

* automate tested releases through maintainer-approved release PRs ([113cbbc](https://github.com/redstreet/beancount_reds_importers/commit/113cbbc11c3a98e71dbc2e6cd883737c1d6726ff))

## 0.10.0 (2025-02-23)


### Improvements

- improvements to pdfreader. [gary-roach]

  Refactored pdfreader to be more extensible and added a mercurycards importer which uses the pdfreader to read credit card transactions.
- turn on emit_filing_account by default. [Red S]

  Else, we are dependent on the order of postings determined by Python
- feat! : add generic json reader. [dev]

  BREAKING CHANGE: old jsonreader.py is rename into schwabjsonreader.py
- fidelity_brokerage_csv importer (ofx is limited to 90 days) [Red S]
- minor: add deep_identify to ibkr. [Red S]
- ibkr flex query web API downloader (reds-ibkr-flexquery-download) [Red S]

  the new command is: reds-ibkr-flexquery-download
- ibkr: add transfers; minor refactor. [Red S]
- IBKR add balance assertions for positions. [Red S]
- ibkr balance assertion for cash balance. [Red S]
- xml reader + ibkr flex query importer. [Red S]

### Fixes

- silent exit if there's nothing to print. [Justus Pendleton]

  Only print table header if there are actually accounts
  that need updates.
- #114: rerun checks on push to PRs. [Red S]
- failing unit tests because of emit_filing_account change. [Red S]

  - emit_filing_account was turned on by default in 07d972d, which broke
    unit tests
- #109: raise notimplemented for get_transactions() [Red S]
- schwab_csv_brokerage: add more transaction types. [Red S]
- constrain Beancount dependency version. [dev]

  The project doesn't work with beancount v3.
- '' in securities bug. [Red S]
- csvreader: strip before parsing dates. [Red S]
- wip, fix fidelity_cma_csv. [Red S]

  TODO:
  - this needs a pytest so tests don't go stale
  - needs much more fixing, or removal
- remove blank ticker, common with brokerage-bank combos. [Red S]
- ibkr trade commissions fix. [Red S]
- add interest to schwab_csv_brokerage. [Red S]

### Other

- Merge pull request #117 from hoostus/main. [Red S]

  Only print table header if there are actually accounts that need updates
- Merge pull request #107 from dev590t/main. [Red S]

  Support JSON File


## 0.9.0 (2024-05-14)

### New Features

- add genericpdf paycheck importer. [Ammon Sarver]
- add bamboohr paycheck importer. [Ammon Sarver]
- add pdfreader libreader importer. [Ammon Sarver]
- minor: add 'show_configured' in paycheck transaction builder. [Red S]

### New Importers
- add CSV importer for Digital Credit Union (#89) [Harlan Lieberman-Berg]
- add importer for Alliant Federal Credit Union (#88) [Harlan Lieberman-Berg]
- add schwab csv credit line importer. [Red S]

### Improvements

- minor: add_custom_postings to banking.py. [Red S]
- minor: add identification based on filename to schwab importers. [Red S]
- minor: overridable add_custom_postings() [Red S]
- minor: add tdameritrade to template.cfg. [Red S]


### Fixes

- update requirements to add back lost packages. [Ammon Sarver]
- schwab_csv_creditline balance sign. [Red S]
- add file encoding support to csvreader. [Ad Timmering]
- only emit filing account metadata if configured #97. [Red S]
- one-file-per-account broke with smart_importer #97. [Red S]
- timestamp issue in balance assertions. [Red S]
- balance date on test. [Red S]
- schwab tests. [Red S]
- schwab doesn't use a header in their csv any more. [Red S]
- schwab_csv_checking format changed #91. [Red S]

### Other
- enforce formatting with ruff. [Rane Brown]
- format with isort, use pyproject.toml. [Rane Brown]
- switch to ruff for linting (#90) [Harlan Lieberman-Berg]
- style: reformat to 99 col width (previously 88 col) [Red S]


## 0.8.0 (2023-11-24)


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
