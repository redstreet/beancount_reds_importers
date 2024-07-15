"""IBKR Flex Query importer for beancount.

TODO:
- balance assertions for positions
- balance assertions for cash
- Flex Web Service API to programmatically retrieve all of this

Activity Flex Query Details
Query ID XXX
Query Name XXX

Sections
========

Account Information
-------------------
1.ClientAccountID
2.CurrencyPrimary

Cash Transactions
-----------------

Options: Dividends, Payment in Lieu of Dividends, Withholding Tax, 871(m) Withholding, Advisor Fees, Other Fees, Deposits & Withdrawals, Carbon Credits, Bill Pay, Broker Interest Paid, Broker Interest Received, Broker Fees, Bond Interest Paid, Bond Interest Received, Price Adjustments, Commission Adjustments, Detail

1.Date/Time
2.Amount
3.Type
4.CurrencyPrimary
5.Symbol
6.CommodityType
7.ISIN

Net Stock Position Summary
--------------------------
1.Symbol
2.CUSIP

Open Dividend Accruals
----------------------
1.Symbol
2.GrossAmount
3.NetAmount
4.PayDate
5.Quantity
6.ISIN

Trades
------
Options: Execution
1.SecurityID
2.DateTime
3.TransactionType
4.Quantity
5.TradePrice
6.TradeMoney
7.Proceeds
8.IBCommission
9.IBCommissionCurrency
10.NetCash
11.CostBasis
12.FifoPnlRealized
13.Buy/Sell
14.CurrencyPrimary
15.ISIN


Delivery Configuration
----------------------
Accounts
Format XML
Period Last N Calendar Days
Number of Days 120


General Configuration
---------------------
Profit and Loss Default
Include Canceled Trades? No
Include Currency Rates? No
Include Audit Trail Fields? No
Display Account Alias in Place of Account ID? No
Breakout by Day? No
Date Format yyyy-MM-dd
Time Format HH:mm:ss TimeZone
Date/Time Separator ' ' (single-space)

"""

import datetime
from beancount_reds_importers.libreader import xmlreader
from beancount_reds_importers.libtransactionbuilder import investments
from beancount.core.number import D

class DictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)

# xml on left, ofx on right
ofx_type_map = {
    'BUY': 'buystock',
    'SELL': 'selltock',
}


class Importer(investments.Importer, xmlreader.Importer):
    IMPORTER_NAME = "IBKR Flex Query"

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_pattern_def = "Transaction_report"
            self.custom_init_run = True
            self.date_format = '%Y-%m-%d'
            self.get_ticker_info = self.get_ticker_info_from_id

    def set_currency(self):
        self.currency = list(self.get_xpath_elements("/FlexQueryResponse/FlexStatements/FlexStatement/AccountInformation"))[0]['currency']

    # fixup dates
    def convert_date(self, d):
        d = d.split(' ')[0]
        return datetime.datetime.strptime(d, self.date_format)

    def trade_to_ofx_dict(self, xml_data):
        # Mapping the input dictionary to the OFX dictionary format
        ofx_dict = {
            'security':   xml_data['isin'],
            'tradeDate':  self.convert_date(xml_data['dateTime']),
            'memo':       xml_data['transactionType'],
            'type':       ofx_type_map[xml_data['buySell']],
            'units':      D(xml_data['quantity']),
            'unit_price': D(xml_data['tradePrice']),
            'commission': -1 * D(xml_data['ibCommission']),
            'total':      D(xml_data['netCash']),
        }
        return ofx_dict

    def cash_to_ofx_dict(self, xml_data):
        # Mapping the input dictionary to the OFX dictionary format
        ofx_dict = {
            'tradeDate':  self.convert_date(xml_data['dateTime']),
            'amount':     D(xml_data['amount']),
            'security':   xml_data.get('isin', None),
            'type':       'cash',
            'memo':       xml_data['type'],
        }

        if xml_data['type'] == 'Dividends':
            ofx_dict['type'] = 'dividends'
            ofx_dict['total'] = ofx_dict['amount']

        return ofx_dict

    def xml_trade_interpreter(self, element):
        ot = self.trade_to_ofx_dict(element)
        return DictToObject(ot)

    def xml_cash_interpreter(self, element):
        ot = self.cash_to_ofx_dict(element)
        return DictToObject(ot)

    def get_transactions(self):
        yield from self.get_xpath_elements('/FlexQueryResponse/FlexStatements/FlexStatement/Trades/Trade',
                                           xml_interpreter=self.xml_trade_interpreter)
        yield from self.get_xpath_elements('/FlexQueryResponse/FlexStatements/FlexStatement/CashTransactions/CashTransaction',
                                           xml_interpreter=self.xml_cash_interpreter)

    def get_balance_assertion_date(self):
        ac = list(self.get_xpath_elements('/FlexQueryResponse/FlexStatements/FlexStatement/CashReport/CashReportCurrency'))[0]
        return self.convert_date(ac['toDate']).date()

    def get_available_cash(self, settlement_fund_balance=0):
        """Assumes there's only one cash currency.
        TODO: get investments transaction builder to accept date from get_available_cash
        """
        ac = list(self.get_xpath_elements('/FlexQueryResponse/FlexStatements/FlexStatement/CashReport/CashReportCurrency'))[0]
        return D(ac['slbNetCash'])
