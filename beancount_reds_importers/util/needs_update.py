#!/usr/bin/env python3
"""Determine the list of accounts needing updates based on the last balance entry."""

import ast
import re
from datetime import datetime

import click
import tabulate
from beancount import loader
from beancount.core import getters
from beancount.core.data import Balance, Close, Custom, Open
from click.core import ParameterSource

tbl_options = {"tablefmt": "simple"}


def get_config(entries, args, ctx):
    """Get beancount config for the given plugin that can then be used on the command line"""
    retval = {}
    _extension_entries = [
        e for e in entries if isinstance(e, Custom) and e.type == "reds-importers"
    ]
    config_meta = {
        entry.values[0].value: (entry.values[1].value if (len(entry.values) == 2) else None)
        for entry in _extension_entries
    }

    config = {k: ast.literal_eval(v) for k, v in config_meta.items() if "needs-updates" in k}
    config = config.get("needs-updates", {})
    if args["all_accounts"]:
        config["included_account_pats"] = []
        config["excluded_account_pats"] = ["$-^"]
    included_account_pats = config.get("included_account_pats", ["^Assets:", "^Liabilities:"])
    excluded_account_pats = config.get(
        "excluded_account_pats", ["$-^"]
    )  # exclude nothing by default
    retval["excluded_re"] = re.compile("|".join(excluded_account_pats))
    retval["included_re"] = re.compile("|".join(included_account_pats))

    # what's supplied on the command line must always override what's in the config
    retval["recency"] = args["recency"]
    recency_source = ctx.get_parameter_source("recency")
    if recency_source == ParameterSource.DEFAULT and config.get("recency"):
        retval["recency"] = config.get("recency")

    return retval


def is_interesting_account(account, closes, config):
    included_re = config["included_re"]
    excluded_re = config["excluded_re"]
    return account not in closes and included_re.match(account) and not excluded_re.match(account)


def handle_commodity_leaf_accounts_old(last_balance):
    """
    Handle commodity leaf accounts. If an account ends with all capital letters, it is a
    commodity leaf. Eg: Assets:Investments:Etrade:AAPL

    Commodity leaf accounts are ascribed to their parent. The parent's last updated date is
    considered to be the latest date of a balance assertion on any child.
    """
    d = {}
    pat_ticker = re.compile(r"^[A-Z0-9]+$")
    for acc in last_balance:
        parent, leaf = acc.rsplit(":", 1)
        if pat_ticker.match(leaf):
            if parent in d:
                if d[parent].date < last_balance[acc].date:
                    d[parent] = last_balance[acc]
            else:
                d[parent] = last_balance[acc]
        else:
            d[acc] = last_balance[acc]
    return d


pat_ticker = re.compile(r"^[A-Z0-9]+$")


def strip_commodity_leaf(acc):
    parent, leaf = acc.rsplit(":", 1)
    if pat_ticker.match(leaf):
        return parent
    return acc


def handle_commodity_leaf_accounts(need_updates):
    """
    Handle commodity leaf accounts. If an account ends with all capital letters, it is a
    commodity leaf. Eg: Assets:Investments:Etrade:AAPL

    Commodity leaf accounts are ascribed to their parent. The parent's last updated date is
    considered to be the latest date of a balance assertion on any child.
    """
    d = {}
    for acc in need_updates:
        parent, leaf = acc.rsplit(":", 1)
        if pat_ticker.match(leaf):
            if parent in d:
                if d[parent] < need_updates[acc]:
                    d[parent] = need_updates[acc]
            else:
                d[parent] = need_updates[acc]
        else:
            d[acc] = need_updates[acc]
    return d


def accounts_with_no_balance_entries(entries, closes, last_balance, config):
    """Find interesting accounts with zero balance assertion entries."""
    accounts = getters.get_accounts(entries)
    asset_accounts = [a for a in accounts if is_interesting_account(a, closes, config)]
    accs_no_bal_raw = [a for a in asset_accounts if a not in last_balance]

    # Handle commodity leaf accounts
    accs_no_bal = []

    pat_ticker = re.compile(r"^[A-Z0-9]+$")

    def acc_or_parent(acc):
        parent, leaf = acc.rsplit(":", 1)
        if pat_ticker.match(leaf):
            return parent
        return acc

    accs_no_bal = [acc_or_parent(i) for i in accs_no_bal_raw]

    # Remove accounts where one or more children do have a balance entry. Needed because of
    # commodity leaf accounts
    accs_no_bal = [
        (i,) for i in set(accs_no_bal) if not any(j.startswith(i) for j in last_balance)
    ]
    return accs_no_bal


def pretty_print_table(not_updated_accounts, sort_by_date):
    field = 0 if sort_by_date else 2
    output = sorted(
        [(v[0], v[1], k) for k, v in not_updated_accounts.items()], key=lambda x: x[field]
    )
    headers = ["Last Updated", "Threshold", "Account"]
    print(click.style(tabulate.tabulate(output, headers=headers, **tbl_options)))


def get_account_thresholds(entries):
    """
    If per-account thresholds are specified, get them.

    Propagate children to parent. We only expect one child to have it. Accounts are imported
    at an account level. So Assets:Investments:Fidelity-Acc-1234 is imported as an account.
    However, when a commodity leaf based account structure is used
    (Assets:Investments:Fidelity-Acc-1234:AAPL), we typically specify needs_update_days on
    one of the leaves (since the parent doesn't exist). We propagate that to the parent here

    """

    return {
        strip_commodity_leaf(op.account): op.meta["needs_update_days"]
        for op in entries
        if isinstance(op, Open) and "needs_update_days" in op.meta
    }


@click.command("needs-update", context_settings={"show_default": True})
@click.argument("beancount-file", type=click.Path(exists=True), envvar="BEANCOUNT_FILE")
@click.option(
    "--recency",
    help="How many days ago should the last balance assertion be to be considered old",
    default=15,
)
@click.option(
    "--ignore-metadata",
    help="Ignore account metadata (`needs_update_days`) and usewhat --recency specifies instead",
    is_flag=False,
)
@click.option("--sort-by-date", help="Sort output by date (instead of account name)", is_flag=True)
@click.option(
    "--all-accounts",
    help="Show all account (ignore include/exclude in config)",
    is_flag=True,
)
@click.pass_context
def accounts_needing_updates(
    ctx, beancount_file, recency, ignore_metadata, sort_by_date, all_accounts
):
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
    config = get_config(entries, locals(), ctx)
    closes = [a.account for a in entries if isinstance(a, Close)]
    balance_entries = [
        a
        for a in entries
        if isinstance(a, Balance) and is_interesting_account(a.account, closes, config)
    ]
    last_balance = {v.account: v for v in balance_entries}
    last_balance = handle_commodity_leaf_accounts_old(last_balance)

    account_thresholds = get_account_thresholds(entries)

    need_updates = {}
    today = datetime.now().date()
    for acc, bal in last_balance.items():
        # look for an account-specific override in metadata

        threshold = config["recency"]
        if not ignore_metadata:
            custom_recency = account_thresholds.get(acc)
            threshold = custom_recency if custom_recency else config["recency"]
        age = (today - bal.date).days
        if age > threshold:
            need_updates[acc] = bal.date, threshold

    if need_updates:
        pretty_print_table(need_updates, sort_by_date)

    # If there are accounts with zero balance entries, print them
    accs_no_bal = accounts_with_no_balance_entries(entries, closes, last_balance, config)
    if accs_no_bal:
        headers = ["Accounts without balance entries:"]
        print(
            click.style(
                "\n" + tabulate.tabulate(sorted(accs_no_bal), headers=headers, **tbl_options)
            )
        )


if __name__ == "__main__":
    accounts_needing_updates()
