# beancount_reds_importers

Simple importers and tools for beancount. Separates the file format reader from the
transaction builder code. New importers are easily built by mixing and matching a
fileformat reader and a transaction builder, and specifying (via python code) the
semantics of the file format.

File format readers included are:
- ofx
- csv (single and multitable support)
- xlsx (single and multitable support)

Transaction builders included are:
- banking (for banks and credit cards)
- investments/brokerages (to handle the associated complexity of investment transactions)
- paychecks (to handle paychecks, which typically contain many postings)

The coding goal is to factor out importer code into well maintained common libraries for
banks, credit cards, investment houses, paychecks and so on, to minimize institution
specific code and make writing new importers easy.

Input in ofx format (over csv) minimizes data and coding errors, eliminates format
breaking changes in csv, and typically includes balances that are used to generate
balance assertions, and commodity prices.

Look inside the importers/ directory to see a list of institutions supported. More
investment, credit card, and banking institutions will be added in the future.
Contributions welcome.

## Installation
`pip install beancount-reds-importers`

## Running
1. Create your own my.import. An example my.import is provided. At the least, include your account numbers
2. Include fund information. Copy the included `fund_info.py` to start with.
2. You can now run `bean-identify`, `bean-extract`, etc. See the included script: Run `./import.sh <your_input_ofx>`
3. If cusip info is missing, the importer will let you know. Add it to your `fund_info.py`

## Testing
I run tests across hundreds of actual ofx and csv files, against reference outputs that
I know to be correct from my personal file. However, I'm unable to share them since
these are personal. Testing against real world files is best, so I recommend you do this
with your own input files. Having said that, Unit tests are probably useful, even if
limited, and I'll add these shortly (contributions welcome).

## Contributions
Test ofx files and test infra appreciated.
