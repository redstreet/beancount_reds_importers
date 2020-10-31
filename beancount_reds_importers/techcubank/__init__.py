"""Tech CU checking/savings bank account ofx importer for beancount."""

import ntpath
import beancount_reds_importers.libimport.banking

class Importer(beancount_reds_importers.libimport.banking.Importer):
    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.account_number_field = 'account_id'
            self.filename_identifier_substring = 'transactions'
            self.filename_identifier_substring = 'Accounts'
            self.custom_init_run = True


