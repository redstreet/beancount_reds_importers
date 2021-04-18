# beancount_reds_importers

Simple importers and tools for [beancount](https://github.com/beancount/beancount).

For a comprehensive look at writing importers, see
**[The Five Minute Ledger Update](https://reds-rants.netlify.app/personal-finance/the-five-minute-ledger-update/).**

Importers can be ugly and painful to write, yet are important in automating the grunt
work out of maintaining personal finance software. The philosophy is to make writing
importers easy. To achieve this, the design goal is to separate importers in to three
parts:

1. file format reader (reusable)
2. transaction builder (reusable)
3. institution-specific declarations and code (minimal, institution specific)

This helps move common code into (1) and (2) above, and makes writing new importers easy
by sipmly picking from one of those two along with with minimal declarations and code in
(3).

File format readers included are:
- ofx
- csv (single and multitable support)
- xlsx (single and multitable support)

Transaction builders included are:
- banking (for banks and credit cards, which benefit from a postings predictor like
  [smart_importer](https://github.com/beancount/smart_importer)
- investments/brokerages (to handle the very many distinct cases of investment related
  transactions)
- paychecks (to handle paychecks, which typically contain very many pre-determined
  postings in a single entry)

Input in ofx format (over csv) minimizes data and coding errors, eliminates format
breaking changes in csv, and typically includes balances that are used to generate
balance assertions, and commodity prices.

Look inside the importers/ directory to see a list of institutions supported. More
investment, credit card, and banking institutions will be added in the future.
Contributions welcome.

## Installation
`pip install beancount-reds-importers`

If you plan on importing excel files, also run:
`pip install openpyxl`

## Running
1. Create your own my.import. An example my.import is provided. At the least, include your account numbers
2. Include fund information. Copy the included `fund_info.py` to start with.
3. You can now run `bean-identify`, `bean-extract`, etc. See the included script: Run `./import.sh <your_input_ofx>`
4. If cusip info is missing, the importer will let you know. Add it to your `fund_info.py`

## Testing
I run tests across hundreds of actual ofx and csv files, against reference outputs that
I know to be correct from my personal file. However, I'm unable to share them since
these are personal. Testing against real world files is best, so I recommend you do this
with your own input files. Having said that, Unit tests are probably useful, even if
limited, and I'll add these shortly (contributions welcome).

## Contributions
Test ofx files and test infra appreciated.
