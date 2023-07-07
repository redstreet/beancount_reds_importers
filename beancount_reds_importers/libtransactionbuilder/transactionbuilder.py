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

    @staticmethod
    def remove_empty_subaccounts(acct):
        """Translates 'Assets:Foo::Bar' to 'Assets:Foo:Bar'."""
        return ':'.join(x for x in acct.split(':') if x)

    def set_config_variables(self, substs):
        """
        Replaces {} strings in config with substitutions specified in a dictionary (substs)

        Eg: replaces 'Assets:Broker:{currency}' with 'Assets:Broker:USD'

        substs is the substitution dictionary. For example:
        substs = { 'currency': self.currency,
                  # Leave the other values as is
                  'ticker': '{ticker}',
                  'source401k': '{source401k}',
                  }
        """
        self.config = {k: v.format(**substs) if isinstance(v, str) else v for k, v in self.config.items()}

        # Prevent the replacement fields from appearing in the output of
        # the file_account method
        if 'filing_account' not in self.config:
            kwargs = {k: '' for k in substs}
            filing_account = self.config['main_account'].format(**kwargs)
            self.config['filing_account'] = self.remove_empty_subaccounts(filing_account)
