""" Workday paycheck importer."""

import datetime
import re
from beancount.core.number import D
from beancount.core import data
from beancount_reds_importers.libimport import banking, xlsx_multitable_reader


class Importer(banking.Importer, xlsx_multitable_reader.Importer):
    def custom_init(self):
        self.max_rounding_error = 0.04
        self.account_number_field = 'number'
        self.filename_identifier_substring = '_Complete'
        self.header_identifier = '- Complete' + self.config.get('custom_header', '')
        self.includes_balances = False
        self.date_format = '%m/%d/%Y'
        self.skip_head_rows = 1
        self.skip_tail_rows = 1
        self.funds_db_txt = 'funds_by_ticker'
        self.header_map = {
            "Description": 'memo',
            "Symbol":      'security',
            "Quantity":    'units',
            "Price":       'unit_price',
            }

    def prepare_raw_columns(self, rdr):
        return rdr

    def convert_columns(self, rdr):
        # fixup decimals
        decimals = ['units']
        for i in decimals:
            rdr = rdr.convert(i, D)

        # fixup currencies
        def remove_non_numeric(x):
            return re.sub("[^0-9\.]", "", x)  # noqa: W605
        currencies = ['unit_price']
        for i in currencies:
            rdr = rdr.convert(i, remove_non_numeric)
            rdr = rdr.convert(i, D)

        return rdr

    def file_date(self, file):
        return self.date.date()

    def get_max_transaction_date(self):
        return self.date.date()

    def prepare_tables(self):
        # first row has date
        # TODO: replace with rawdate = tables['Payslip Information'][0].Check_Date
        d = self.raw_rdr[0][0].split(' ', 3)[2]
        self.date = datetime.datetime.strptime(d, self.date_format)

        def valid_header_label(label):
            return label.lower().replace(' ', '_')

        for section, table in self.alltables.items():
            for header in table.header():
                table = table.rename(header, valid_header_label(header))
            self.alltables[section] = table

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
        entry = data.Transaction(metadata, self.date.date(), self.FLAG,
                                 config['desc'], None, data.EMPTY_SET, data.EMPTY_SET, [])

        entry = self.build_postings(entry)
        return([entry])
