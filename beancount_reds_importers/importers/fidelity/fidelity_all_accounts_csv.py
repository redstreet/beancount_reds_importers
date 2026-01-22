"""Fidelity All Accounts .csv importer.

!!! This is WIP and not yet ready for general use !!!

"""
import math
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
        self.use_inferred_price = self.config.get(
            # calculate price to 4 decimal places rather than using csv price
            "use_inferred_price",
            False,
        )
        self.add_precision = self.config.get("add_precision", False)  # add some decimal precision to quantity and value fields if none is present
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
        }
        if self.use_inferred_price:
            self.header_map["inferred_price"] = "unit_price"
        else:
            self.header_map["Price"] = "unit_price"
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

        def add_precision(value):
            # add decimal places if none are present because
            # beancount treats values with no decimal places
            # as infinitely precise
            if "." not in value:
                return value + ".00"

            return value

        def compute_inferred_price(row):
            if row["Quantity"] is None or row["Quantity"].strip() == "":
                # can''t do anything if quantity is empty
                return ""

            qty = float(row["Quantity"])
            amt = float(row["Amount"])
            acc = float(row["Accrued Interest"] if row["Accrued Interest"] else 0)
            comm = float(row["Commission"] if row["Commission"] else 0)
            fees = float(row["Fees"] if row["Fees"] else 0)

            # quantity effectively zero → return empty string
            if math.isclose(qty, 0, rel_tol=1e-9, abs_tol=1e-9):
                return ""

            # base price calculation...subtract out accrued interest, fees, and commissions
            # fidelity csv prices are always positive, so base (the numerator here) must
            # be positive
            base = abs(amt) - abs(acc if acc else 0) - abs(comm if comm else 0) - abs(fees if fees else 0)

            # inferred price...fidelity csv prices are always positive
            # amount or quantity can be negatgive
            price = round(abs(base) / abs(qty), 4)

            # validate that the inferred price rounds to what fidelity stated
            # the price to be.  In some cases there will be no price even though one
            # can be inferred...these seem to be things like 1:1 reorgs or stock splits
            # in either case these will need to be handled manually (and they cannot be
            # properly created w/o the inferred price either)
            if row["Price"] and not math.isclose(round(price, 2), float(row["Price"]), rel_tol=1e-9, abs_tol=1e-9):
                return row["Price"]

            return str(price)

        # add an inferred price column b/c csv prices are only to two decimals
        rdr = rdr.addfield("inferred_price", compute_inferred_price)

        rdr = rdr.addfield("total", lambda x: x["Amount"])
        rdr = rdr.addfield("tradeDate", lambda x: x["Run Date"])
        if self.add_precision:
            for f in ["Amount", "Quantity", "total"]:
                rdr = rdr.convert(f, add_precision)

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
