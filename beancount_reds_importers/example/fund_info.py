#!/usr/bin/env python3

# cusip info: https://www.quantumonline.com/search.cfm

# eventually, the plan is to automate downloading of cusip and ticker info as needed. For now, manually
# include a list here.

cusip_map = {
    '808524805': 'SCHF',
}

ticker_map = {
    'Schwab International Equity ETF':   'SCHF',
}

money_market = ['VMFXX']

fund_info = {
    'money_market': money_market,
    'cusip_map': cusip_map,
    'ticker_map': ticker_map,
}
