"""Generic banking ofx importer for beancount."""

import datetime
import itertools
from beancount.core import data
from beancount.core.number import D
from beancount.core import amount
from beancount.ingest import importer
from beancount_reds_importers.libtransactionbuilder import banking


# paychecks are typically transaction with many (10-30) postings including several each of income, taxes,
# pre-tax and post-tax deductions, transfers, reimbursements, etc. This importer enables importing a single
# paycheck, resulting in a single entry. The source can be a pdf that has been turned to text, or a .csv or
# other format. The input specification is a dictionary corresponding to various sections of a paycheck and
# the text in them to match. For example:
# template = {
#         # keys correspond to text found in the paycheck being imported. Values are postings to generate.
#         Each value generates a single posting for the matching text. Lists of accounts therefore generate
#         multiple postings.
#
#         'Employer Paid Benefits': {
#             "401(k) Employer Match": ["Income:Benefits:Employer-401k",
#                                       "Assets:Zero-Sum-Accounts:Transfers:Paycheck:Y401k:Match"],
#         },
#
#         'Earnings' : {
#         "Salary Pay"                :"Income:Salary:Regular",
#         "BONUS"                     :"Income:Salary:Bonus:Annual",
#         "Relocation Bonus"          :"Income:Salary:Bonus:Relocation",
#         "Spot Bonus"                :"Income:Salary:Bonus:Spot",
#         "EquityUnit"                :"Income:Salary:Equity",
#         },
#
#         'Employee Taxes': {
#         "Social Security":     "Expenses:Taxes:FICA",
#         "Medicare":            "Expenses:Taxes:Medicare",
#         "State Tax":           "Expenses:Taxes:State-Income-Tax:Withheld",
#         "Federal Withholding": "Expenses:Taxes:Federal-Income-Tax:Withheld",
#         },
#
#         'Deductions': {
#             "..." : "...",
#         },
# }


class Importer(banking.Importer):
    def file_date(self, file):
        return self.paycheck_date()


    def get_max_transaction_date(self):
        return self.date.date()

    def build_postings(self, entry):
        template = self.config['paycheck_template']
        currency = self.config['currency']
        total = 0

        for section, table in self.alltables.items():
            if section not in template:
                continue
            for row in table.namedtuples():
                if row.description in template[section]:
                    accounts = template[section][row.description]
                    accounts = [accounts] if not isinstance(accounts, list) else accounts
                    for account in accounts:
                        if not hasattr(row, 'amount'):
                            continue
                        amount = D(row.amount)
                        if 'Income:' in account and amount >= 0:
                            amount *= -1
                        total += amount
                        if amount:
                            data.create_simple_posting(entry, account, amount, currency)
        if total != 0:
            data.create_simple_posting(entry, "TOTAL:NONZERO", total, currency)
        newentry = entry._replace(postings=sorted(entry.postings))
        return newentry

    def extract(self, file, existing_entries=None):
        self.initialize(file)
        config = self.config

        self.read_file(file)
        metadata = data.new_metadata(file.name, 0)
        entry = data.Transaction(metadata, self.paycheck_date(), self.FLAG,
                                 config['desc'], None, data.EMPTY_SET, data.EMPTY_SET, [])

        entry = self.build_postings(entry)
        return([entry])
