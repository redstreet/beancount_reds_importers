#!/usr/bin/env python3

# cusip info: https://www.quantumonline.com/search.cfm

# eventually, the plan is to automate downloading of cusip and ticker info as needed. For now, manually
# include a list here.

fund_data = [
 ('SCHF',   '808524805', 'Schwab International Equity ETF'),
 ('VGTEST', '012345678', 'Vanguard Test Fund'),
 ('VMFXX',  '922906300', 'Vanguard Federal Money Market Fund'),
]

# list of money_market accounts. These will not be held at cost, and instead will use price conversions
money_market = ['VMFXX']

fund_info = {
        'fund_data' : fund_data,
        'money_market' : money_market,
        }
