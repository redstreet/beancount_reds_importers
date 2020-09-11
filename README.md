# beancount_reds_ingestor

Simple importers and tools, mostly ofx based and built on top of `ofxparse`. Using ofx (over csv) minimizes data and coding errors, eliminates format breaking changes in csv, allows for automatic imports of balances to generate balance assertions, and imports prices.

The coding goal is to factor out importer code into well maintained common libraries for banks, credit cards, and investment houses, to minimize institution specific code and make writing new importers easy.

Look inside the importers/ directory to see a list of institutions supported. More investment, credit card, and banking institutions will be added in the future. Contributions welcome.

## Installation
`pip install beancount-reds-importers`

## Running
1. Create your own my.import. An example my.import is provided. At the least, include your account numbers
2. Include fund information. Copy the included `fund_info.py` to start with.
2. You can now run `bean-identify`, `bean-extract`, etc. See the included script: Run `./import.sh <your_input_ofx>`
3. If cusip info is missing, the importer will let you know. Add it to your `fund_info.py`

## Contributions
Test ofx files and test infra appreciated.
