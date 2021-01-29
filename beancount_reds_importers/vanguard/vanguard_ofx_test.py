__copyright__ = "Copyright (C) 2016  Martin Blais"
__license__ = "GNU GPLv2"

import datetime
import re
import unittest

from beancount.parser import cmptest
from beancount_reds_importers import vanguard

fund_info = {
        'fund_data' : [ ('VTI', '922908769', 'VANGUARD TOTAL STOCK MARKET ETF', ), ],
        'money_market' : [ 'VMMXX' ]
        }

conf = {
    'account_number' : '1234567890',
    'main_account'   : 'Assets:Vanguard',
    'transfer'       : 'Assets:Transfer',
    'dividends'      : 'Income:Dividends',
    'cg'             : 'Income:Capital-Gains',
    'fees'           : 'Expenses:Brokerage-Fees',
    'rounding_error' : 'Equity:Rounding-Errors',
    'fund_info'       : fund_info,
}

class TestVanguardOFXImporter(cmptest.TestCase):

    def test_file_name(self):
        importer = vanguard.Importer(conf)
        import pdb; pdb.set_trace()
        self.assertEqual(('VTI', 'VANGUARD TOTAL STOCK MARKET ETF'),
                importer.get_ticker_info('922908769'))

        
if __name__ == '__main__':
    unittest.main()
