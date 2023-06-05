"""Transaction builder module base class Transaction builders such as the investment, banking, and
paycheck inherit this."""

from beancount.core import data

class TransactionBuilder():
    def get_tags(self, ot=None):
        """Can be overridden by importer"""
        return data.EMPTY_SET

