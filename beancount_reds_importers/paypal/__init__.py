""" Paypal csv importer."""

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import banking


class Importer(banking.Importer, csvreader.Importer):
    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_identifier_substring = 'paypal'
            self.header_identifier = 'Date, Time, Time Zone, Name, Type, Status, Currency, Amount, Receipt ID, Balance'
            self.date_format = '%m/%d/%Y'

            self.header_map = {
                    "Date" : 'date',
                    "Type" : 'type',
                    "Currency" : 'currency',
                    "Amount" : 'amount',
                    "Receipt ID" : 'meta_receipt_id',
                }
            self.skip_transaction_types = []

    def prepare_raw_columns(self, rdr):
        rdr = rdr.cutout('')  # clean up last column
        return rdr


# TODO:
# - custom currency
# - skip rows based on:
#     if index > 0 and row.balance == prev_balance: # hack to deterimne what rows to ignore
#         continue
#     prev_balance = row.balance
# - balance assertion generation
# - auto column matching
