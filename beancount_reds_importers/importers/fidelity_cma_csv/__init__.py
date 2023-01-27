"""Fidelity CMA/checking csv importer for beancount."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking

class Importer(banking.Importer, csvreader.Importer):
    IMPORTER_NAME = 'Fidelity Cash Management Account'

    def custom_init(self):
       self.max_rounding_error = 0.04
       self.filename_pattern_def = '.*History'
       self.date_format = '%m/%d/%Y'
       self.header_identifier = ".*Run Date,Action,Symbol,Security Description,Security Type,Quantity,Price \(\$\),Commission \(\$\),Fees \(\$\),Accrued Interest \(\$\),Amount \(\$\),Settlement Date"
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

    def prepare_raw_columns(self,rdr):

        for field in ['Action']:
            rdr = rdr.convert(field, lambda x: x.lstrip())

        def create_payee(d):
            # payee_types = ['DIRECT DEPOSIT','DIRECT DEBIT','Check Paid','INTEREST EARNED','TRANSFERRED TO','TRANSFERRED FROM']
            if d.startswith('DIRECT DEPOSIT'):
                return 'DIRECT DEPOSIT'
            elif d.startswith('DIRECT DEBIT'):
                return 'DIRECT DEBIT'
            elif d.startswith('Check Paid'):
                return 'Check Paid'
            elif d.startswith('INTEREST EARNED'):
                return 'INTEREST EARNED'
            elif d.startswith('TRANSFERRED TO'):
                return 'TRANSFERRED TO'
            elif d.startswith('TRANSFERRED FROM'):
                return 'TRANSFERRED FROM'
            else:
                print("error no matching payee")
            return d
 
        def create_memo(d):
            # payee_types = ['DIRECT DEPOSIT','DIRECT DEBIT','Check Paid','INTEREST EARNED','TRANSFERRED TO','TRANSFERRED FROM']
            if d.startswith('DIRECT DEPOSIT'):
                return d.replace('DIRECT DEPOSIT', "")
            elif d.startswith('DIRECT DEBIT'):
                return d.replace('DIRECT DEBIT', "")
            elif d.startswith('Check Paid'):
                return d.replace('Check Paid', "")
            elif d.startswith('INTEREST EARNED'):
                return d.replace('INTEREST EARNED', "")
            elif d.startswith('TRANSFERRED TO'):
                return d.replace('TRANSFERRED TO', "")
            elif d.startswith('TRANSFERRED FROM'):
                return d.replace('TRANSFERRED FROM', "")
            else:
                print("error no matching payee")
            return d

        rdr = rdr.addfield('payee',lambda x: x['Action'])
        rdr = rdr.convert('payee',create_payee)
 
        rdr = rdr.addfield('memo',lambda x: x['Action'])
        rdr = rdr.convert('memo',create_memo)

        for field in ['memo']:
            rdr = rdr.convert(field, lambda x: x.lstrip())

        return rdr
