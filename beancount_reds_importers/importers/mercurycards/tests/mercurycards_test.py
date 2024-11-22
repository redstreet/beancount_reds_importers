from os import path

from beancount.ingest import regression_pytest as regtest

from beancount_reds_importers.importers import mercurycards


@regtest.with_importer(
    mercurycards.Importer(
        {
            'main_account'                 : 'Liabilities:Credit-Cards:Mercury',
            'emit_filing_account_metadata' : False,
            'filename_pattern'             : 'mercury_statement_20241105.pdf',
            'skip_transaction_types'       : {},
            'currency'                     : 'USD'
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestMercuryCards(regtest.ImporterTestBase):
    pass
