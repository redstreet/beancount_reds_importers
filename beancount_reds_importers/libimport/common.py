#!/usr/bin/env python3

from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.position import Cost
from beancount.core.number import Decimal
from beancount.core.number import D


def create_simple_posting_with_price(entry, account,
                                     number, currency,
                                     price_number, price_currency):
    return create_simple_posting_with_cost_or_price(entry, account,
                                                    number, currency,
                                                    price_number=price_number, price_currency=price_currency)


def create_simple_posting_with_cost(entry, account,
                                    number, currency,
                                    cost_number, cost_currency):
    return create_simple_posting_with_cost_or_price(entry, account,
                                                    number, currency,
                                                    cost_number=cost_number, cost_currency=cost_currency)


def create_simple_posting_with_cost_or_price(entry, account,
                                             number, currency,
                                             price_number=None, price_currency=None,
                                             cost_number=None, cost_currency=None, costspec=None):
    """Create a simple posting on the entry, with a cost (for purchases) or price (for sell transactions).

    Args:
      entry: The entry instance to add the posting to.
      account: A string, the account to use on the posting.
      number: A Decimal number or string to use in the posting's Amount.
      currency: A string, the currency for the Amount.
      price_number: A Decimal number or string to use for the posting's price Amount.
      price_currency: a string, the currency for the price Amount.
      cost_number: A Decimal number or string to use for the posting's cost Amount.
      cost_currency: a string, the currency for the cost Amount.
    Returns:
      An instance of Posting, and as a side-effect the entry has had its list of
      postings modified with the new Posting instance.
    """
    if isinstance(account, str):
        pass
    if not isinstance(number, Decimal):
        number = D(number)
    units = Amount(number, currency)

    if not (price_number or cost_number):
        print("Either price ({}) or cost ({}) must be specified ({})".format(price_number, cost_number, entry))
        import pdb
        pdb.set_trace()
        raise Exception("Either price ({}) or cost ({}) must be specified".format(price_number, cost_number))

    price = Amount(price_number, price_currency) if price_number else None
    cost = Cost(cost_number, cost_currency, None, None) if cost_number else None
    cost = costspec if costspec else cost
    posting = data.Posting(account, units, cost, price, None, None)

    if entry is not None:
        entry.postings.append(posting)
    return posting
