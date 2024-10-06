"""IBKR Flex Query importer for beancount.

TODO:
- Flex Web Service API to programmatically retrieve data

Activity Flex Query Details

Sections
Account Information
1.ClientAccountID
2.CurrencyPrimary

Cash Report
1.CurrencyPrimary
2.StartingCash
3.EndingCash
4.NetCashBalanceSLB
5.ToDate

Cash Transactions
1.Date/Time
2.Amount
3.Type
4.CurrencyPrimary
5.Symbol
6.CommodityType
7.ISIN

Net Stock Position Summary
1.Symbol
2.ISIN
3.ReportDate
4.NetShares

Open Dividend Accruals
1.Symbol
2.GrossAmount
3.NetAmount
4.PayDate
5.Quantity
6.ISIN

Open Positions
Options: Summary
1.Symbol
2.ISIN
3.Quantity

Trades
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

Transfers
Options: Transfer
1.Symbol
2.ISIN
3.DateTime
4.Quantity
5.TransferPrice


Delivery Configuration
Accounts Format XML
Period Last N Calendar Days
Number of Days 120


General Configuration
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

from beancount.core.number import D

from beancount_reds_importers.libreader import xmlreader
from beancount_reds_importers.libtransactionbuilder import investments


class DictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)


# xml on left, ofx on right
ofx_type_map = {
    "BUY": "buystock",
    "SELL": "selltock",
}


class Importer(investments.Importer, xmlreader.Importer):
    IMPORTER_NAME = "IBKR Flex Query"

    def custom_init(self):
        if not self.custom_init_run:
            self.max_rounding_error = 0.04
            self.filename_pattern_def = "ibkr"
            self.custom_init_run = True
            self.date_format = "%Y-%m-%d"
            self.get_ticker_info = self.get_ticker_info_from_id

    def deep_identify(self, file):
        try:
            if self.config.get("account_number", None):
                # account number specific matching
                return (
                    self.config["account_number"]
                    == list(
                        self.get_xpath_elements(
                            "/FlexQueryResponse/FlexStatements/FlexStatement/AccountInformation"
                        )
                    )[0]["accountId"]
                )
            else:
                # base check: simply ensure this looks like a valid IBKR Flex Query file
                return list(self.get_xpath_elements("/FlexQueryResponse"))[0] is not None
        except IndexError:
            return False

    def set_currency(self):
        self.currency = list(
            self.get_xpath_elements(
                "/FlexQueryResponse/FlexStatements/FlexStatement/AccountInformation"
            )
        )[0]["currency"]

    # fixup dates
    def convert_date(self, d):
        d = d.split(" ")[0]
        return datetime.datetime.strptime(d, self.date_format)

    def xml_transfer_interpreter(self, xml_data):
        # map, with ofx fields on the left and xml fields on the right
        ofx_dict = {
            "security": xml_data["isin"],
            "tradeDate": self.convert_date(xml_data["dateTime"]),
            "units": D(xml_data["quantity"]),
            "memo": "Transfer in kind",
            "type": "transfer",
        }
        return DictToObject(ofx_dict)

    def xml_trade_interpreter(self, xml_data):
        # map, with ofx fields on the left and xml fields on the right
        ofx_dict = {
            "security": xml_data["isin"],
            "tradeDate": self.convert_date(xml_data["dateTime"]),
            "memo": xml_data["transactionType"],
            "type": ofx_type_map[xml_data["buySell"]],
            "units": D(xml_data["quantity"]),
            "unit_price": D(xml_data["tradePrice"]),
            "commission": -1 * D(xml_data["ibCommission"]),
            "total": D(xml_data["netCash"]),
        }
        return DictToObject(ofx_dict)

    def xml_cash_interpreter(self, xml_data):
        # map, with ofx fields on the left and xml fields on the right
        ofx_dict = {
            "tradeDate": self.convert_date(xml_data["dateTime"]),
            "amount": D(xml_data["amount"]),
            "security": xml_data.get("isin", None),
            "type": "cash",
            "memo": xml_data["type"],
        }

        if xml_data["type"] == "Dividends":
            ofx_dict["type"] = "dividends"
            ofx_dict["total"] = ofx_dict["amount"]

        return DictToObject(ofx_dict)

    def get_transactions(self):
        yield from self.get_xpath_elements(
            "/FlexQueryResponse/FlexStatements/FlexStatement/Trades/Trade",
            xml_interpreter=self.xml_trade_interpreter,
        )
        yield from self.get_xpath_elements(
            "/FlexQueryResponse/FlexStatements/FlexStatement/CashTransactions/CashTransaction",
            xml_interpreter=self.xml_cash_interpreter,
        )
        yield from self.get_xpath_elements(
            "/FlexQueryResponse/FlexStatements/FlexStatement/Transfers/Transfer",
            xml_interpreter=self.xml_transfer_interpreter,
        )

    def get_balance_assertion_date(self):
        ac = list(
            self.get_xpath_elements(
                "/FlexQueryResponse/FlexStatements/FlexStatement/CashReport/CashReportCurrency"
            )
        )[0]
        return self.convert_date(ac["toDate"]).date()

    def get_available_cash(self, settlement_fund_balance=0):
        """Assumes there's only one cash currency.
        TODO: get investments transaction builder to accept date from get_available_cash
        """
        ac = list(
            self.get_xpath_elements(
                "/FlexQueryResponse/FlexStatements/FlexStatement/CashReport/CashReportCurrency"
            )
        )[0]
        return D(ac["slbNetCash"])

    def get_balance_positions(self):
        for pos in self.get_xpath_elements(
            "/FlexQueryResponse/FlexStatements/FlexStatement/OpenPositions/OpenPosition"
        ):
            balance = {
                "security": pos["isin"],
                "units": D(pos["position"]),
            }
            yield DictToObject(balance)
