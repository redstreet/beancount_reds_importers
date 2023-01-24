""" Workday paycheck importer."""

import datetime
from beancount_reds_importers.libreader import xlsx_multitable_reader
from beancount_reds_importers.libtransactionbuilder import paycheck

# Workday exports paycheck stubs to a .xlsx, one paycheck per .xlsx, with multiple tables on a single sheet,
# that this importer imports. Call this importer with a config that looks like:
#
# workday.Importer({'desc': "Paycheck (Acme Company)",
#      'main_account' : 'Income:Employment',
#      'paycheck_template': '{}' # See beancount_reds_importers/libtransactionbuilder/paycheck.py for sample template
#      'currency' : 'PENNIES',
#     }),


class Importer(paycheck.Importer, xlsx_multitable_reader.Importer):
    IMPORTER_NAME = 'Workday Paycheck'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*_Complete'
        self.header_identifier = '- Complete' + self.config.get('custom_header', '')
        self.date_format = '%m/%d/%Y'
        self.skip_head_rows = 1
        # TODO: need to be smarter about this, and skip only when needed
        self.skip_tail_rows = 0
        self.funds_db_txt = 'funds_by_ticker'
        self.header_map = {
            "Description": 'memo',
            "Symbol":      'security',
            "Quantity":    'units',
            "Price":       'unit_price',
            }

    def paycheck_date(self, input_file):
        self.read_file(input_file)
        d = self.alltables['Payslip Information'].namedtuples()[0].check_date
        self.date = datetime.datetime.strptime(d, self.date_format)
        return self.date.date()

    def prepare_tables(self):
        def valid_header_label(label):
            return label.lower().replace(' ', '_')

        for section, table in self.alltables.items():
            for header in table.header():
                table = table.rename(header, valid_header_label(header))
            self.alltables[section] = table

    def build_metadata(self, file, metatype=None, data={}):
        return {'filing_account': self.config['main_account']}
