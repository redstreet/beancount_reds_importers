# beancount_reds_ingestor
Simple ingesting tools and importers for various institutions for Beancount (personal finance software)

## Installation
`pip install ofxparse`

## Running
1. modify my.import, add your account numbers
2. `./import.sh <your_input_ofx>`
3. If cusip info is missing, the importer will let you know. Add it to `fund_info.py`

The code should be simple enough to understand.

## Future work
Investment, credit card, and banking institutions will be added.

## Contributions
Test ofx files appreciated.
