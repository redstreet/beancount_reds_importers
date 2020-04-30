# beancount_reds_ingestor

Simple ingesting tools and importers for various institutions for Beancount (personal
finance software).

The importers are primarily ofx based, and the tools are built on top of `ofxparse`.

Look inside the importers/ directory to see a list of institutions supported. More
investment, credit card, and banking institutions will be added in the future.

## Installation
`pip install beancount-reds-importers`

## Running
1. Create your own my.import. An example my.import is provided. At the least, include your account numbers
2. Include fund information. Copy the included `fund_info.py` to start with.
2. You can now run `bean-identify`, `bean-extract`, etc. See the included script: Run `./import.sh <your_input_ofx>`
3. If cusip info is missing, the importer will let you know. Add it to your `fund_info.py`

The code should be simple enough to understand.

## Contributions
Test ofx files and test infra appreciated.
