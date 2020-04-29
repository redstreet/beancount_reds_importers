# beancount_reds_ingestor

Simple ingesting tools and importers for various institutions for Beancount (personal
finance software).

The importers are primarily ofx based, and the tools are built on top of `ofxparse`.

Look inside the importers/ directory to see a list of institutions supported. More
investment, credit card, and banking institutions will be added in the future.

## Installation
`pip install ofxparse`

## Running
1. modify my.import, add your account numbers
2. `./import.sh <your_input_ofx>`
3. If cusip info is missing, the importer will let you know. Add it to `fund_info.py`

The code should be simple enough to understand.

## Contributions
Test ofx files appreciated.
