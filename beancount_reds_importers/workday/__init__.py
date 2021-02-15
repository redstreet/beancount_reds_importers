""" Workday paycheck importer."""

import datetime
import re
from beancount.core.number import D
from beancount_reds_importers.libreader import xlsx_multitable_reader
from beancount_reds_importers.libtransactionbuilder import paycheck

# Workday exports paycheck stubs to a .xlsx, one paycheck per .xlsx, with multiple tables on a single sheet,
# that this importer imports. Call this importer with a config that looks like:
#
# workday.Importer({'desc': "Paycheck (Acme Company)",
#      'main_account' : 'Income:Employment',
#      'paycheck_template': '{}' # See paychecks.py for sample template
#      'currency' : 'PENNIES',
#     }),


class Importer(paycheck.Importer, xlsx_multitable_reader.Importer):
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

    def paycheck_date(self):
        d = self.alltables['Payslip Information'].namedtuples()[0].check_date
        self.date = datetime.datetime.strptime(d, self.date_format)
        return self.date.date()

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

    def prepare_tables(self):

        def valid_header_label(label):
            return label.lower().replace(' ', '_')

        for section, table in self.alltables.items():
            for header in table.header():
                table = table.rename(header, valid_header_label(header))
            self.alltables[section] = table
