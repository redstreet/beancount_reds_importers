#!/usr/bin/env python3

# Eventually, the goal is to automate downloading of CUSIP and ticker info as needed. For now, manually
# include a list here.

# The importer will complain if it comes across a CUSIP in your OFX, for which it does not have the fund info.
# This typically happens when you buy a new fund in your portfolio that you have never owned before. In this
# case, it needs to be given the ticker and a description of the fund so it can create transactions in
# Beancount.

# Your investments broker should list CUSIP for all commodities. As an example, searching for 922906300 in
# Vanguard's search bar brings up VMFXX, and this link, from which you can fill up the entry below in
# fund_data:
# https://institutional.vanguard.com/web/c1/investments/product-details/fund/0033

# A site that has CUSIP info for "securities traded on the NYSE, NYSE Arca, NYSE Amex, Nasdaq, OTCBB and the
# Pink Sheets" is here:
# https://www.quantumonline.com/search.cfm
# Note it wouldn't list VMFXX in the example below since that is a money market fund, nor would it list
# mutual funds since those are brokerage specific.

fund_data = [
 ('SCHF',   '808524805', 'Schwab International Equity ETF'),
 ('VGTEST', '012345678', 'Vanguard Test Fund'),
 ('VMFXX',  '922906300', 'Vanguard Federal Money Market Fund'),
]

# list of money_market accounts. These will not be held at cost, and instead will use price conversions
money_market = ['VMFXX']

fund_info = {
        'fund_data': fund_data,
        'money_market': money_market,
        }
