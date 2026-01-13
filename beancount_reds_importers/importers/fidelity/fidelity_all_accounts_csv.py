"""Fidelity All Accounts .csv importer.

!!! This is WIP and not yet ready for general use !!!

"""

import re
from datetime import datetime

from beangulp import cache

from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments


class Importer(csvreader.Importer, investments.Importer):
    IMPORTER_NAME = "Fidelity All Accounts CSV"

    def custom_init(self):
        self.max_rounding_error = 0.04
        self.file_encoding = "utf-8-sig"
        self.filename_pattern_def = "Accounts_History.*"
        self.header_identifier = "^Run Date,Account,Account Number,Action,Symbol.*"
        self.column_labels_line = "Run Date,Account,Account Number,Action,Symbol,Description,Type,Exchange Quantity,Exchange Currency,Currency,Price,Quantity,Exchange Rate,Commission,Fees,Accrued Interest,Amount,Settlement Date"
        self.get_ticker_info = self.get_ticker_info_from_id
        self.date_format = "%m/%d/%Y"
        self.funds_db_txt = "funds_by_ticker"

        # fmt: off
        self.header_map = {
            "Account Number": "account_number",
            "Run Date": "date",
            "Action": "memo",
            "Symbol": "security",
            "Quantity": "units",
            "Accrued Interest": "accrued_interest",
            "Amount": "amount",
            "Settlement Date": "settleDate",
            "Fees": "fees",
            "Commission": "commission",
            "Price": "unit_price",
        }
        self.transaction_type_map = {
            # NOTE: the keys here should all be upper case
            "REINVESTMENT": "buymf",
            "REDEMPTION FROM": "sellmf",
            "DIVIDEND RECEIVED": "dividends",
            "DIVIDENDS": "dividends",
            "TRANSFERRED FROM": "cash",
            "YOU BOUGHT": "buystock",
            "YOU SOLD": "sellstock",
            "REDEMPTION PAYOUT": "sellother",
            "DIRECT DEPOSIT": "dep",
            "TRANSFERRED TO": "xfer",
            "MUNI EXEMPT": "income",
            "INTEREST EARNED": "income",
            "FEE CHARGED": "fee",
            "ADVISOR FEE": "fee",
            "FOREIGN TAX": "fee",
            "ADJ FOREIGN": "fee",
            "BUY CANCEL": "fee",  # longer text here is BUY CANCEL TAX PAID as of May-05-2025...
            "DIVIDEND ADJUSTMENT": "fee",  # longer text here is FOREIGN TAX PAID as of May-05-2025...
            "BILL PAYMENT": "payment",
            "DEBIT CARD": "payment",
            "CHECK PAID": "payment",
            "DIRECT DEBIT": "payment",
            "ELECTRONIC FUNDS": "payment",
            "CHECK RECEIVED": "dep",
            "CASH ADVANCE": "debit",
            "SHORT-TERM CAP": "capgainsd_st",
            "LONG-TERM CAP": "capgainsd_lt",
            "PARTIC CONTR": "dep",
            "WIRE TRANSFER": "dep",
            "CONTRIBUTED TO": "sellstock",
            "IN LIEU": "dep",
            "CASH CONTRIBUTION": "dep",
            "ROLLOVER CASH": "dep",
            "TRANSFER OF": "dep",
            "PART CONTRIB": "dep",
            "ROLLOVER SHARES": "buystock",  # rollover from closed account...almost certainly needs to be edited manually
            "CONVERSION AS": "buymf",  # conversion of mutual fund class...almost certainly needs to be edited manually
            "EXCHANGE OUT": "sellmf",
            "EXCHANGE IN": "buymf",
            "EXCHANGED TO": "buymf",
            "CHANGE ON": "capgainsd_lt",
            "WITHDRAWALS": "sellmf",
            "CO CONTR": "dep",
            "DIVIDEND": "reinvest",
            "CONTRIBUTIONS": "buystock",
            "TRANSFER": "xfer",
            "PURCHASE INTO": "buystock",
        }
        # fmt: on

    def get_max_transaction_date(self):
        try:
            # NOTE: this is the same as the code in csvreader.py, but the exception does not
            # generate an error...for the fidelity csv transaction file there are no balance
            # assertions, so not being able to generate them is not an error.  This will occur for any
            # account in the import file that has no transactions

            date = max(
                ot.tradeDate if hasattr(ot, "tradeDate") else ot.date
                for ot in self.get_transactions()
            ).date()
        except Exception:
            date = datetime.today().date()

        return date

    def deep_identify(self, file):
        return re.search(self.header_identifier, cache.get_file(file).head(), flags=re.MULTILINE)

    def skip_transaction(self, ot):
        if ot.account_number != self.config["account_number"]:
            return True
        return ot.type in ["MERGER MER", "ADJUST FEE", "DISTRIBUTION", "JOURNALED JNL"]
        # this sort of transaction must be handled manually
        # ADJUST FEE sounds like a fee, but has been used for a 1:1 reorg
        # DISTRIBUTION is for splits

    def prepare_table(self, rdr):
        if "" in rdr.fieldnames():
            rdr = rdr.cutout("")  # clean up last column

        rdr = rdr.addfield("total", lambda x: x["Amount"])
        rdr = rdr.addfield("tradeDate", lambda x: x["Run Date"])

        # the REINVESTMENT action will include a fund symbol as the 2nd word,
        # so only use the first word for mapping
        # DISTRIBUTION which is used for splits will also include a symbol as
        # 2nd word
        rdr = rdr.capture(
            "Action",
            "(DISTRIBUTION|REINVESTMENT|\\S+(?:\\s+\\S+)?)",
            ["type"],
            include_original=True,
        )
        rdr = rdr.convert("type", 'upper')

        return rdr
