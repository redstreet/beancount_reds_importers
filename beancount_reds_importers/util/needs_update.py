#!/usr/bin/env python3
"""Determine the list of accounts needing updates based on the last balance entry."""

import click
import re
import tabulate
from beancount import loader
from beancount.core import getters
from beancount.core.data import Balance, Close, Custom
from datetime import datetime
import ast


tbl_options = {'tablefmt': 'simple'}


def get_config(entries, args):
    """Get beancount config for the given plugin that can then be used on the command line"""
    global excluded_re, included_re
    _extension_entries = [e for e in entries
                          if isinstance(e, Custom) and e.type == 'reds-importers']
    config_meta = {entry.values[0].value:
                   (entry.values[1].value if (len(entry.values) == 2) else None)
                   for entry in _extension_entries}

    config = {k: ast.literal_eval(v) for k, v in config_meta.items() if 'needs-updates' in k}
    config = config.get('needs-updates', {})
    if args['all_accounts']:
        config['included_account_pats'] = []
        config['excluded_account_pats'] = ['$-^']
    included_account_pats = config.get('included_account_pats', ['^Assets:', '^Liabilities:'])
    excluded_account_pats = config.get('excluded_account_pats', ['$-^'])  # exclude nothing by default
    excluded_re = re.compile('|'.join(excluded_account_pats))
    included_re = re.compile('|'.join(included_account_pats))


def is_interesting_account(account, closes):
    return account not in closes and \
           included_re.match(account) and \
           not excluded_re.match(account)


def handle_commodity_leaf_accounts(last_balance):
    """
    Handle commodity leaf accounts. If an account ends with all capital letters, it is a
    commodity leaf. Eg: Assets:Investments:Etrade:AAPL

    Commodity leaf accounts are ascribed to their parent. The parent's last updated date is
    considered to be the latest date of a balance assertion on any child.
    """
    d = {}
    pat_ticker = re.compile(r'^[A-Z0-9]+$')
    for acc in last_balance:
        parent, leaf = acc.rsplit(':', 1)
        if pat_ticker.match(leaf):
            if parent in d:
                if d[parent].date < last_balance[acc].date:
                    d[parent] = last_balance[acc]
            else:
                d[parent] = last_balance[acc]
        else:
            d[acc] = last_balance[acc]
    return d


def accounts_with_no_balance_entries(entries, closes, last_balance):
    """Find interesting accounts with zero balance assertion entries."""
    accounts = getters.get_accounts(entries)
    asset_accounts = [a for a in accounts if is_interesting_account(a, closes)]
    accs_no_bal_raw = [a for a in asset_accounts if a not in last_balance]

    # Handle commodity leaf accounts
    accs_no_bal = []

    pat_ticker = re.compile(r'^[A-Z0-9]+$')

    def acc_or_parent(acc):
        parent, leaf = acc.rsplit(':', 1)
        if pat_ticker.match(leaf):
            return parent
        return acc
    accs_no_bal = [acc_or_parent(i) for i in accs_no_bal_raw]

    # Remove accounts where one or more children do have a balance entry. Needed because of
    # commodity leaf accounts
    accs_no_bal = [(i,) for i in set(accs_no_bal) if not any(j.startswith(i) for j in last_balance)]
    return accs_no_bal


def pretty_print_table(not_updated_accounts, sort_by_date):
    field = 0 if sort_by_date else 1
    output = sorted([(v.date, k) for k, v in not_updated_accounts.items()], key=lambda x: x[field])
    headers = ['Last Updated', 'Account']
    print(click.style(tabulate.tabulate(output, headers=headers, **tbl_options)))


@click.command("needs-update", context_settings={'show_default': True})
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('--recency', help='How many days ago should the last balance assertion be to be considered old', default=15)
@click.option('--sort-by-date', help='Sort output by date (instead of account name)', is_flag=True)
@click.option('--all-accounts', help='Show all account (ignore include/exclude in config)', is_flag=True)
def accounts_needing_updates(beancount_file, recency, sort_by_date, all_accounts):
    """
    Show a list of accounts needing updates, and the date of the last update (which is defined as
    the date of the last balance assertion on the account).

    Only accounts in the included list which are not in the excluded list are considered. Both
    lists are specified as regular expressions. These can be used to include only accounts
    existing in the real world, and filter out those that are not interesting (eg: accounts
    known to not be used often).

    Commodity leaf accounts are ascribed to their parent. The parent's last updated date is
    considered to be the latest date of a balance assertion on any child.

    Closed accounts are filtered out.

    Accounts matching the criteria above with zero balance entries are also printed out, since by
    definition, they don't have a (recent) balance assertion.

    The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on
    the command line.

    The (optional) configuration for this utility is to be supplied as a custom directive like the
    following example in your beancount file:

    \b
     2010-01-01 custom "reds-importers" "needs-updates" "{
       'included_account_pats' : ['^Assets:Banks', '^Assets:Investments', '^Liabilities:Credit-Cards'],
       'excluded_account_pats' : ['.*Inactive', '.*Closed']
     }}"

    Default values for the configuration are:

    \b
     2010-01-01 custom "reds-importers" "needs-updates" "{
       'included_account_pats' : ['^Assets:', '^Liabilities:'],
       'excluded_account_pats' : []
     }}"
    """

    entries, _, _ = loader.load_file(beancount_file)
    get_config(entries, locals())
    closes = [a.account for a in entries if isinstance(a, Close)]
    balance_entries = [a for a in entries if isinstance(a, Balance) and
                       is_interesting_account(a.account, closes)]
    last_balance = {v.account: v for v in balance_entries}
    d = handle_commodity_leaf_accounts(last_balance)

    # find accounts with balance assertions older than N days
    need_updates = {acc: bal for acc, bal in d.items() if ((datetime.now().date() - d[acc].date).days > recency)}
    pretty_print_table(need_updates, sort_by_date)

    # If there are accounts with zero balance entries, print them
    accs_no_bal = accounts_with_no_balance_entries(entries, closes, last_balance)
    if accs_no_bal:
        headers = ['Accounts without balance entries:']
        print(click.style('\n' + tabulate.tabulate(sorted(accs_no_bal), headers=headers, **tbl_options)))


if __name__ == '__main__':
    accounts_needing_updates()
