"""Transaction builder module base class Transaction builders such as the investment, banking, and
paycheck inherit this."""

from beancount.core import data

class TransactionBuilder():
    def skip_transaction(self, ot):
        """For custom importers to override"""
        return False

    def get_tags(self, ot=None):
        """For custom importers to override"""
        return data.EMPTY_SET

