"""
Amazon gift card transactions screenscrape importer.

This is to import gift card transactions by going to:
---
Amazon website -> Accounts -> Gift cards -> Gift Card Activity
---
and copy-pasting the table of gift card transactions along with the header into a file, which this
importer then imports into Beancount.

Header looks like this (include it in the file):
Date 	Description 	Amount

Config looks like this:

amazongc.Importer({
    'main_account'    : 'Assets:Gift-Cards-and-Credits:Amazon-com-Gift-Cards',
    'target_account'  : 'Assets:Zero-Sum-Accounts:Amazon-Purchases',
    })

"""

import datetime
import itertools
import ntpath
from beancount.core import data
from beancount.ingest import importer
from beancount.core.number import D

# account flow                          ingest source
# ----------------------------------------------------
# credit_card -> amazon_purchases       credit card
# gift_card   -> amazon_purchases       amazon account
# amazon_purchases -> expenses          amazon account


class Importer(importer.ImporterProtocol):
    def __init__(self, config):
        self.config = config
        self.currency = self.config.get('currency', 'CURRENCY_NOT_CONFIGURED')
        self.filename_pattern_def = 'amazon-gift-card.tsv'

    def identify(self, file):
        return self.filename_pattern_def in file.name

    def file_name(self, file):
        return '{}'.format(ntpath.basename(file.name))

    def file_account(self, _):
        return self.config['main_account']

    def file_date(self, file):
        "Get the maximum date from the file."
        maxdate = datetime.date.min
        for line in open(file.name, 'r').readlines()[1:]:
            f = line.split('\t')
            f = [i.strip() for i in f]
            date = datetime.datetime.strptime(f[0], '%B %d, %Y').date()
            maxdate = max(date, maxdate)
        return maxdate

    def extract(self, file, existing_entries=None):
        config = self.config

        new_entries = []

        counter = itertools.count()
        for line in open(file.name, 'r').readlines()[1:]:
            f = line.split('\t')
            f = [i.strip() for i in f]
            date = datetime.datetime.strptime(f[0], '%B %d, %Y').date()
            description = f[1].encode("ascii", "ignore").decode()
            number = D(f[2].replace('$', ''))

            metadata = data.new_metadata(file.name, next(counter))
            entry = data.Transaction(metadata, date, self.FLAG,
                                     None, description, data.EMPTY_SET, data.EMPTY_SET, [])
            data.create_simple_posting(entry, config['main_account'], number, self.currency)
            data.create_simple_posting(entry, config['target_account'], None, None)
            new_entries.append(entry)

        return new_entries
