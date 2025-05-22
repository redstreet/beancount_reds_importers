'''
Tests for the IBKR importer.
'''
from os import path

from beancount_reds_importers.importers import ibkr
from beancount_reds_importers.util import regression_pytest as regtest

@regtest.with_importer(
    ibkr.Importer({

    })
)

@regtest.with_testdir(path.dirname(__file__))
class TestIbkr(regtest.ImporterTestBase):
    '''
    Tests for the IBKR importer.
    '''
    pass
