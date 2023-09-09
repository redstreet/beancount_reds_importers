"""Generic banking ofx importer for beancount."""

from beancount.core import data
from beancount.core.number import D
from beancount_reds_importers.libtransactionbuilder import banking


# paychecks are typically transaction with many (10-40) postings including several each of income, taxes,
# pre-tax and post-tax deductions, transfers, reimbursements, etc. This importer enables importing a single
# paycheck, resulting in a single transaction. The source can be a pdf that has been turned to text, or a .csv
# or .xlsx, or another format. The input specification is a dictionary corresponding to various sections of a
# paycheck and the text in them to match. For example:

#
# template = {
#
#         # top level keys (eg: 'Earnings') correspond to sections of the paycheck.
#
#         # Inner keys correspond to text found in the row of the paycheck being imported. Values
#         are accounts in postings to generate, and can be a string or a list. Each string
#         generates a single posting. A list therefore generates multiple postings. The example
#         shows where this is useful:
#
#         'Employer Paid Benefits': {
#             "401(k) Employer Match": ["Income:Benefits:Employer-401k",
#                                       "Assets:Zero-Sum-Accounts:Transfers:Paycheck:Y401k:Match"],
#         },
#
#         Note that , the 'amount' column in any row is extracted. If that column doesn't exist,
#         'amount_in_pay_group_currency' (currently hardcoded) is extracted. If neither of those
#         exist, no extraction is done.
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

def flip_if_needed(amount, account):
    if amount >= 0 and any(account.startswith(prefix) for prefix in ['Income:', 'Equity:', 'Liabilities:']):
        amount *= -1
    if amount < 0 and any(account.startswith(prefix) for prefix in ['Expenses:', 'Assets:']):
        amount *= -1
    return amount


class Importer(banking.Importer):
    def file_date(self, input_file):
        return self.paycheck_date(input_file)

    def build_postings(self, entry):
        template = self.config['paycheck_template']
        currency = self.config['currency']
        total = 0

        for section, table in self.alltables.items():
            if section not in template:
                continue
            for row in table.namedtuples():
                # TODO: 'bank' is workday specific; move it there
                row_description = getattr(row, 'description', getattr(row, 'bank', None))
                row_pattern = next(filter(lambda ts: row_description.startswith(ts), template[section]), None)
                if row_pattern:
                    accounts = template[section][row_pattern]
                    accounts = [accounts] if not isinstance(accounts, list) else accounts
                    for account in accounts:
                        # TODO: 'amount_in_pay_group_currency' is workday specific; move it there
                        amount = getattr(row, 'amount', getattr(row, 'amount_in_pay_group_currency', None))
                        # import pdb; pdb.set_trace()

                        if not amount:
                            continue
                        amount = D(amount)
                        amount = flip_if_needed(amount, account)
                        total += amount
                        if amount:
                            data.create_simple_posting(entry, account, amount, currency)
        if total != 0:
            data.create_simple_posting(entry, "TOTAL:NONZERO", total, currency)

        if self.config.get('sort_postings', True):
            postings = sorted(entry.postings)
        else:
            postings = entry.postings
        newentry = entry._replace(postings=postings)
        return newentry

    def build_metadata(self, file, metatype=None, data={}):
        """This method is for importers to override. The overridden method can
        look at the metatype ('transaction', 'balance', 'account', 'commodity', etc.)
        and the data dictionary to return additional metadata"""
        return {}

    def extract(self, file, existing_entries=None):
        self.initialize(file)
        config = self.config

        self.read_file(file)
        metadata = data.new_metadata(file.name, 0)
        metadata.update(self.build_metadata(file, metatype='transaction'))
        entry = data.Transaction(metadata, self.paycheck_date(file), self.FLAG,
                                 None, config['desc'], self.get_tags(), data.EMPTY_SET, [])

        entry = self.build_postings(entry)
        return [entry]
