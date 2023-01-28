"""Fidelity CMA/checking csv importer for beancount."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking
import re


class Importer(banking.Importer, csvreader.Importer):
    IMPORTER_NAME = 'Fidelity Cash Management Account'

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.filename_pattern_def = '.*History'
        self.date_format = '%m/%d/%Y'
        header_s0 = ".*Run Date,Action,Symbol,Security Description,Security Type,Quantity,Price \\(\\$\\),"
        header_s1 = "Commission \\(\\$\\),Fees \\(\\$\\),Accrued Interest \\(\\$\\),Amount \\(\\$\\),Settlement Date"
        header_sum = header_s0 + header_s1
        self.header_identifier = header_sum
        self.skip_head_rows = 5
        self.skip_tail_rows = 16
        self.header_map = {
               "Run Date":             'date',
               "Action":               'description',
               "Amount ($)":           'amount',

               "Settlement Date":      'settleDate',
               "Accrued Interest ($)": 'accrued_interest',
               "Fees ($)":             'fees',
               "Security Type":        'security_type',
               "Commission ($)":       'commission',
               "Security Description": 'security_description',
               "Symbol":               'security',
               "Price ($)":            'unit_price',
               }

    def deep_identify(self, file):
        return re.match(self.header_identifier, file.head(), flags=re.DOTALL)

    def prepare_raw_columns(self, rdr):

        for field in ['Action']:
            rdr = rdr.convert(field, lambda x: x.lstrip())

        rdr = rdr.capture('Action', '(?:\\s)(?:\\w*)(.*)', ['memo'], include_original=True)
        rdr = rdr.capture('Action', '(\\S+(?:\\s+\\S+)?)', ['payee'], include_original=True)

        for field in ['memo', 'payee']:
            rdr = rdr.convert(field, lambda x: x.lstrip())

        return rdr
