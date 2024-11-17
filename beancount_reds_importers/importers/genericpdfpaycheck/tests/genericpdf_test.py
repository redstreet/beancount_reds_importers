from os import path

from beancount.ingest import regression_pytest as regtest

from beancount_reds_importers.importers import genericpdfpaycheck


@regtest.with_importer(
    genericpdfpaycheck.Importer(
        {
            "desc": "Paycheck",
            "main_account": "Income:Salary:FakeCompany",
            "paycheck_template": {
                "table_4": {
                    "Bonus": "Income:Bonus:FakeCompany",
                    "Overtime": "Income:Overtime:FakeCompany",
                    "Regular": "Income:Salary:FakeCompany",
                },
                "table_5": {
                    "Federal MED/EE": "Expenses:Taxes:Medicare",
                    "Federal OASDI/EE": "Expenses:Taxes:SocialSecurity",
                    "Federal Withholding": "Expenses:Taxes:FederalIncome",
                    "State Withholding": "Expenses:Taxes:StateIncome",
                },
                "table_6": {"CURRENT": "Assets:Checking:ABCBank"},
            },
            "currency": "USD",
        }
    )
)
@regtest.with_testdir(path.dirname(__file__))
class TestGenericPDFPaycheck(regtest.ImporterTestBase):
    pass
