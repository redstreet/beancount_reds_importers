"""IBKR Flex Query importer for beancount.

TODO:
- Flex Web Service API to programmatically retrieve data

Create an Activity Flex Query in Flex Queries using the following parameters:

Sections
Account Information
1.AccountID
2.Currency

Cash Report
1.Currency
2.StartingCash
3.EndingCash
4.NetCashBalance (SLB)
5.ToDate

Cash Transactions
1.Currency
2.Symbol
3.ISIN
4.Date/Time
5.Amount
6.Type
7.CommodityType

Net Stock Position Summary
1.Symbol
2.ISIN
3.ReportDate
4.NetShares

Open Dividend Accruals
1.Symbol
2.ISIN
3.PayDate
4.Quantity
5.GrossAmount
6.NetAmount

Open Positions
Options: Summary
1.Symbol
2.ISIN
3.Quantity

Trades
Options: Execution
- CurrencyPrimary
- SecurityID
- ISIN
- DateTime
- TransactionType
- Quantity
- TradePrice
- TradeMoney
- Proceeds
- IBCommission
- IBCommissionCurrency
- NetCash
- CostBasis
- Realized P/L
- Buy/Sell

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
Date Format yyyy-MM-dd
Time Format HH:mm:ss TimeZone
Date/Time Separator ' ' (single-space)
Profit and Loss Default
Include Canceled Trades? No
Include Currency Rates? No
Include Audit Trail Fields? No
Display Account Alias in Place of Account ID? No
Breakout by Day? No

"""

import datetime
from enum import Enum

from beancount.core import data
from beancount.core.number import D
from loguru import logger

from beancount_reds_importers.libreader import xmlreader
from beancount_reds_importers.libtransactionbuilder import investments


class DictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)


class IbkrCashTxnType(str, Enum):
    """IBKR cash transaction types"""

    BROKERINT = "Broker Interest Received"
    COMADJ = "Commission Adjustments"
    DEPWDRAW = "Deposits/Withdrawals"
    DIVIDEND = "Dividends"
    OTHERFEES = "Other Fees"
    PMTINLIEU = "Payment In Lieu Of Dividends"
    WHTAX = "Withholding Tax"


# xml on left, ofx on right
ofx_type_map = {
    "BUY": "buystock",
    "SELL": "sellstock",
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
            self.price_cost_both_zero_handler = self.price_cost_both_zero_handler_booktrades

    def deep_identify(self, file):
        try:
            if self.config.get("account_number", None):
                # account number specific matching
                return any(
                    elem["accountId"] == self.config["account_number"]
                    for elem in self.get_xpath_elements(
                        "/FlexQueryResponse/FlexStatements/FlexStatement/AccountInformation"
                    )
                )
            else:
                # base check: simply ensure this looks like a valid IBKR Flex Query file
                return list(self.get_xpath_elements("/FlexQueryResponse"))[0] is not None
        except IndexError:
            logger.error("The configured account number does not match the statement.")
            return False

    def set_currency(self):
        self.currency = next(
            item["currency"]
            for item in self.get_xpath_elements(
                "/FlexQueryResponse/FlexStatements/FlexStatement/AccountInformation"
            )
            if item["accountId"] == self.config["account_number"]
        )

    # fixup dates
    def convert_date(self, d):
        d = d.split(" ")[0]
        return datetime.datetime.strptime(d, self.date_format)

    def get_target_acct_custom(self, transaction, ticker=None):
        if transaction.memo == IbkrCashTxnType.WHTAX:
            return self.config["whtax"] if self.config.get("whtax") else None
        return None

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
            "type_additional": xml_data["transactionType"],
            "units": D(xml_data["quantity"]),
            "unit_price": D(xml_data["tradePrice"]),
            "commission": -1 * D(xml_data["ibCommission"]),
            "total": D(xml_data["netCash"]),
            "cost": D(xml_data.get("cost")),
            "fifoPnlRealized": D(xml_data.get("fifoPnlRealized")),
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
            "currency": xml_data["currency"],
        }

        if xml_data["type"] == "Dividends":
            ofx_dict["type"] = "dividends"
            ofx_dict["total"] = ofx_dict["amount"]

        return DictToObject(ofx_dict)

    def get_transactions(self):
        account_id = self.config["account_number"]
        base_path = f"/FlexQueryResponse/FlexStatements/FlexStatement[@accountId='{account_id}']"

        yield from self.get_xpath_elements(
            f"{base_path}/Trades/Trade",
            xml_interpreter=self.xml_trade_interpreter,
        )
        yield from self.get_xpath_elements(
            f"{base_path}/CashTransactions/CashTransaction",
            xml_interpreter=self.xml_cash_interpreter,
        )
        yield from self.get_xpath_elements(
            f"{base_path}/Transfers/Transfer",
            xml_interpreter=self.xml_transfer_interpreter,
        )

    def get_balance_assertion_date(self):
        account_id = self.config["account_number"]
        base_path = f"/FlexQueryResponse/FlexStatements/FlexStatement[@accountId='{account_id}']"

        ac = list(self.get_xpath_elements(f"{base_path}/CashReport/CashReportCurrency"))[0]
        return self.convert_date(ac["toDate"]).date()

    def get_available_cash(self, settlement_fund_balance=0):
        """Assumes there's only one cash currency.
        TODO: get investments transaction builder to accept date from get_available_cash
        """
        account_id = self.config["account_number"]
        base_path = f"/FlexQueryResponse/FlexStatements/FlexStatement[@accountId='{account_id}']"

        ac = list(self.get_xpath_elements(f"{base_path}/CashReport/CashReportCurrency"))[0]
        return D(ac["slbNetCash"])

    def get_balance_positions(self):
        account_id = self.config["account_number"]
        base_path = f"/FlexQueryResponse/FlexStatements/FlexStatement[@accountId='{account_id}']"

        for pos in self.get_xpath_elements(f"{base_path}/OpenPositions/OpenPosition"):
            balance = {
                "security": pos["isin"],
                "units": D(pos["position"]),
            }
            yield DictToObject(balance)

    def price_cost_both_zero_handler_booktrades(self, entry, ot):
        """If price and cost are both zero, we assume this is an options expiration"""
        data.create_simple_posting(
            entry, self.config["cash_account"], ot.cost - ot.fifoPnlRealized, self.currency
        )

        # TODO: can't do the following here since entry is not passed by reference
        # entry = entry._replace(narration='Assumed Box Trade Resolution (Options Expiry)')
