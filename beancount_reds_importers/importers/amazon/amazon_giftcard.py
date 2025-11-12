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

from beancount_reds_importers.importers.amazon import amazon_giftcard
amazon_giftcard.Importer({
    'main_account'    : 'Assets:Gift-Cards-and-Credits:Amazon-com-Gift-Cards',
    'target_account'  : 'Assets:Zero-Sum-Accounts:Amazon-Purchases',
    })

"""

import datetime
import itertools
import ntpath

from beancount.core import amount, data, flags
from beancount.core.number import D
from beangulp import Importer as BGImporter

# account flow                          ingest source
# ----------------------------------------------------
# credit_card -> amazon_purchases       credit card
# gift_card   -> amazon_purchases       amazon account
# amazon_purchases -> expenses          amazon account


class Importer(BGImporter):
    FLAG = flags.FLAG_OKAY

    def __init__(self, config):
        self.config = config
        self.currency = self.config.get("currency", "CURRENCY_NOT_CONFIGURED")
        self.filename_pattern_def = "amazon-gift-card.tsv"

    def identify(self, file):
        return self.filename_pattern_def in file

    def filename(self, file):
        return "{}".format(ntpath.basename(file))

    def date(self, file):
        "Get the maximum date from the file."
        maxdate = datetime.date.min
        for line in open(file, "r").readlines()[1:]:
            f = line.split("\t")
            f = [i.strip() for i in f]
            date = datetime.datetime.strptime(f[0], "%B %d, %Y").date()
            maxdate = max(date, maxdate)
        return maxdate

    def extract(self, file, existing_entries=None):
        config = self.config

        new_entries = []
        balance_date = datetime.date.min
        balance_amount = 0

        self.counter = itertools.count()
        for line in open(file, "r").readlines()[1:]:
            f = line.split("\t")
            f = [i.strip() for i in f]
            date = datetime.datetime.strptime(f[0], "%B %d, %Y").date()
            description = f[1].encode("ascii", "ignore").decode()
            number = D(f[2].replace("$", ""))
            balance = D(f[3].replace("$", ""))

            metadata = data.new_metadata(file, next(self.counter))
            entry = data.Transaction(
                metadata,
                date,
                self.FLAG,
                None,
                description,
                data.EMPTY_SET,
                data.EMPTY_SET,
                [],
            )
            data.create_simple_posting(entry, config["main_account"], number, self.currency)
            data.create_simple_posting(entry, config["target_account"], None, None)
            new_entries.append(entry)

            if date > balance_date:
                balance_date = date
                balance_amount = balance

        balance_assertion = self.construct_balance_entry(balance_date, balance_amount)
        new_entries.append(balance_assertion)
        return new_entries

    def construct_balance_entry(self, balance_date, balance_amount):
        if not balance_amount or (balance_date == datetime.date.min):
            return
        metadata = data.new_metadata(None, next(self.counter))
        balance_entry = data.Balance(
            metadata,
            balance_date,
            self.config["main_account"],
            amount.Amount(balance_amount, self.currency),
            None,
            None,
        )
        return balance_entry

    def account(self, file):
        if "filing_account" in self.config:
            return self.config["filing_account"]
        return self.config["main_account"]
