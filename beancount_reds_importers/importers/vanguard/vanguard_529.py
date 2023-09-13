""" Vanguard 529 csv importer."""

import petl as etl
import sys
import re
import datetime

from beancount.core.number import D

from beancount_reds_importers.libreader import csv_multitable_reader
from beancount_reds_importers.libtransactionbuilder import investments

class Importer(investments.Importer, csv_multitable_reader.Importer):
    IMPORTER_NAME = 'Vanguard 529'

    def custom_init(self):
        self.max_rounding_error = 0.04
        # Vanguard only gives a csv download option for 529 accounts, but they name it "ofxdownload" to tease you
        self.filename_pattern_def = '.*ofxdownload.*'
        self.header_identifier = 'Fund Account Number,Fund Name,Price,Shares,Total Value.*'
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = '%m/%d/%Y'
        self.funds_db_txt = 'funds_by_ticker'
        self.header_map = {
            "Process Date":             'date',
            "Trade Date":               'tradeDate',
            "Transaction Type":         'type',
            "Transaction Description":  'memo',
            "Shares":                   'units',
            "Share Price":              'unit_price',
            "Gross Amount":             'amount',
            "Net Amount":               'total',
            "Price":                    'unit_price',
            }
        self.transaction_type_map = {
            'Contribution AIP':             'buystock',
            'Contribution EBT':             'buystock',
            }
        self.skip_transaction_types = []
        self.section_titles_are_headers = True
        self.config['add_currency_precision'] = self.config.get('add_currency_precision', True)
    
    def deep_identify(self, file):
        account_number = self.config.get('account_number', '')
        return super().deep_identify(file) and account_number in file.head()
    
    def file_date(self, file):
        return datetime.datetime.now()
    
    def prepare_tables(self):
        ticker_by_desc = {desc: ticker for ticker, _, desc in self.fund_data}

        alltables = {}
        maxdate = None
        for section, table in self.alltables.items():
            if section == 'Fund Account Number':
                section = 'Balance Positions'
                table = table.addfield('security', lambda x: ticker_by_desc.get(x['Fund Name'], x['Fund Name']))
                # We need to add a date field but we can't do that yet because we need to make sure 
                #  the transactions section has been processed and set
            elif section == 'Account Number':
                section = 'Transactions'
                table = table.addfield('security', lambda x: ticker_by_desc.get(x['Investment Name'], x['Investment Name']))
                # We have to do our own finding of the max date because the table data hasn't been cleaned up yet
                maxdate = max(datetime.datetime.strptime(d[0], self.date_format) for d in table.cut('Trade Date').rename('Trade Date', 'date').namedtuples()).date().strftime(self.date_format)
            alltables[section] = table
        self.alltables = alltables

        self.alltables['Balance Positions'] = self.alltables['Balance Positions'].addfield('date', maxdate)

    def is_section_title(self, row):
        if len(row) == 0:
            return False
        return row[0] == 'Fund Account Number' or row[0] == 'Account Number'
    
    def get_transactions(self):
        yield from self.alltables['Transactions'].namedtuples()

    def get_balance_positions(self):
        yield from self.alltables['Balance Positions'].namedtuples()
