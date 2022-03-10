""" Fidelity Net Benefits csv importer. """
""" This importer is intended to cover 'brokerage-style'
    Fidelity CSV files which includes Brokerage,
    Checking, and HSA accounts.

    Does NOT support Fidelity 401k CSV files. """

from beancount_reds_importers.libreader import csv_multitable_reader
from beancount_reds_importers.libreader import csvreader
from beancount_reds_importers.libtransactionbuilder import investments
from enum import Enum, unique

import re
import petl as etl
from beancount.core import data
from beancount.core.number import D
import datetime


class Importer(investments.Importer, csv_multitable_reader.Importer):
    class TransferDedupeStyle(Enum):
        COMMENT_INCOMING_TRANSACTIONS = 1
        COMMENT_OUTGOING_TRANSACTIONS = 2
        COMMENT_ALL_TRANSACTIONS = 3
        COMMENT_NO_TRANSACTIONS = 4

    def custom_init(self):
        assert "account_number" in self.config
        header_preamble = r"\n\n\nBrokerage\n\n"
        self.header_section_title = "Run Date,Action,Symbol,Security Description,Security Type,Quantity,Price ($),Commission ($),Fees ($),Accrued Interest ($),Amount ($),Settlement Date"
        header_lines = header_preamble + re.escape(self.header_section_title)

        self.filename_identifier_substring = (
            "History_for_Account_" + self.config["account_number"]
        )
        self.header_identifier = self.config.get("custom_header", header_lines)

        self.date_format = "%m/%d/%Y"
        self.funds_db_txt = "funds_by_ticker"
        self.get_ticker_info = self.get_ticker_info_custom
        # [(ticker, id, long_name), ...]
        self.transfer_info_accounts = self.config["transfer_info"]["transfer_accounts"]
        self.transfer_info_accounts_by_name = {
            name: (acct, dedupeStyle)
            for name, acct, dedupeStyle in self.transfer_info_accounts
        }

        self.includes_balances = False
        self.includes_commodities = True
        self.includes_accounts = True
        self.skip_head_rows = 5  # skip lines before header
        self.skip_section_rows = 0
        self.skip_tail_rows = 11

        self.max_rounding_error = 0.005

        self.header_map = {
            "Run Date": "date",
            "Action": "type",
            "Symbol": "security",
            "Security Description": "security_description",
            "Security Type": "security_type",
            "Quantity": "units",
            "Price ($)": "unit_price",
            "Commission ($)": "commission",
            "Fees ($)": "fees",
            "Accrued Interest ($)": "accrued_interest",
            "Amount ($)": "total",
            "Settlement Date": "settleDate",
            "tradeDate": "tradeDate",  # Inserted column
            "amount": "amount",  # Inserted column
            "memo": "memo",  # Inserted column
            "transfer_account": "transfer_account",  # Inserted column
        }

    def file_date(self, file):
        # Extract the statement date from the download date on
        # last line of file
        # e.g. 'Date downloaded" 12/31/2021, 9:11 AM'

        with open(file.name) as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            line_head = '"Date downloaded" '
            line_head_len = len(line_head)
            # find place after date ", 9:11 AM"
            tail_match = re.search(r", ", last_line)
            assert tail_match is not None
            line_tail_pos = tail_match.span()[0]
            line_date = last_line[line_head_len:line_tail_pos]
            return datetime.datetime.strptime(line_date, "%m/%d/%Y").date()

    def __build_transaction_bond_metadata(self, file, counter, ot=None):
        metadata = {}
        memo = getattr(ot, "memo", None)
        security_description = getattr(ot, "security_description", None)
        accrued_interest = getattr(ot, "accrued_interest", None)
        is_bought_action = self.__is_bought_action(memo)
        if is_bought_action and self.__is_treasury_bill_zero_coupon(
            security_description
        ):
            # Assume zero-coupon treasury bills
            # shouldn't carry accrued interest
            assert accrued_interest is None

        elif is_bought_action and self.__is_treasury_note(security_description):

            # Sometimes there may be an accrued interest,
            # we generally ignore it and leave it as extra metadata
            # because it doesn't reflect in the actual transaction.
            #
            # From Fidelity:
            # (https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/Account-Statement-FAQs.pdf)
            # Accrued Interest includes the accumulated interest on
            # the fixed income securities in your portfolio,
            # as displayed in the Holdings section of each account,
            # from the last coupon date to the statement date,
            # that has not been paid by the issuer.
            # Accrued Interest is limited to bonds denominated in USD.
            #
            # From treasury direct:
            # (https://www.treasurydirect.gov/indiv/research/indepth/tnotes/res_tnote_rates.htm)
            # Sometimes when you buy a Note, you are charged accrued interest,
            # which is the interest the security earned in the current interest
            # period before you took possession of the security. If you are
            # charged accrued interest, we pay it back to you as part of your
            # next semiannual interest payment
            if accrued_interest is None:
                accrued_interest = D(0.0)

            metadata["bond-accrued-interest"] = accrued_interest

        return metadata

    def __build_transaction_transfer_metadata(self, file, counter, ot=None):
        metadata = {}
        memo = getattr(ot, "memo", None)
        DUPLICATE_META = "__duplicate__"

        # hardcoded metadata (known duplicate transactions)
        if self.__is_electronic_fund_received_action(memo):
            metadata[DUPLICATE_META] = True
            return metadata

        # configured account dedupe metadata
        transfer_account = getattr(ot, "transfer_account", None)
        if (transfer_account is None) or (
            transfer_account not in self.transfer_info_accounts_by_name
        ):
            return metadata

        account, dedupeStyle = self.transfer_info_accounts_by_name[transfer_account]
        if dedupeStyle == Importer.TransferDedupeStyle.COMMENT_ALL_TRANSACTIONS:
            metadata[DUPLICATE_META] = True
        elif self.__is_transfer_in_action(memo) and (
            dedupeStyle == Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS
        ):
            metadata[DUPLICATE_META] = True
        elif self.__is_transfer_out_action(memo) and (
            dedupeStyle == Importer.TransferDedupeStyle.COMMENT_OUTGOING_TRANSACTIONS
        ):
            metadata[DUPLICATE_META] = True
        elif self.__is_direct_deposit_action(memo) and (
            dedupeStyle == Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS
        ):
            metadata[DUPLICATE_META] = True
        elif self.__is_hsa_transfer_in_contribution_action(memo) and (
            dedupeStyle == Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS
        ):
            metadata[DUPLICATE_META] = True
        elif self.__is_acat_transfer_in_action(memo) and (
            dedupeStyle == Importer.TransferDedupeStyle.COMMENT_INCOMING_TRANSACTIONS
        ):
            metadata[DUPLICATE_META] = True

        return metadata

    def build_transaction_metadata(self, file, counter, ot=None, metadata={}):
        metadata_ = data.new_metadata(file.name, counter)
        metadata_custom = {}

        metadata_custom = (
            metadata_custom
            | self.__build_transaction_bond_metadata(file, counter, ot)
            | self.__build_transaction_transfer_metadata(file, counter, ot)
        )
        return metadata_ | metadata | metadata_custom

    def __bond_length_from_dates(self, transaction_date, bond_expiration_date):
        term_period_delta = bond_expiration_date - transaction_date
        term_period_delta_weeks = term_period_delta.days / 7

        weeks_in_year = 52
        weeks_in_6mo = weeks_in_year / 2

        # expecting terms in 6mo divisibles
        assert ((int(term_period_delta_weeks) + 1) % weeks_in_6mo) <= 2

        term_months = int((term_period_delta_weeks + 1) / weeks_in_6mo) * 6
        return term_months

    def __build_commodity_bond_metadata(self, file, counter, commodity=None):
        metadata = {}
        security_description = getattr(commodity, "security_description", None)
        security = getattr(commodity, "security", None)
        date = getattr(commodity, "date", None)
        unit_price = getattr(commodity, "unit_price", None)
        if self.__is_treasury_bill_zero_coupon(security_description):

            # cusip, account_cusip, account_income_cusip = self.treasury_accounts(
            # symbol)

            bond_quote = unit_price * 100
            bond_date_mask_len = len("UNITED STATES TREAS BILLS ZERO CPN 0.00000% ")
            bond_exp_date_str = security_description[bond_date_mask_len:]
            bond_exp_date = datetime.datetime.strptime(bond_exp_date_str, "%m/%d/%Y")
            trade_date = date

            term_months = self.__bond_length_from_dates(trade_date, bond_exp_date)

            #
            # zero coupon bond yield eqn
            # (from https://www.investopedia.com/university/advancedbond/advancedbond3.asp)
            # --------
            # yield = (future value / purchase price)^(1/n) - 1
            # where n = years left until maturity
            #
            # for a 6-month bill, we can calculate term yield by doing
            # term-yield = ((100 / Bond Quote Price)^(1/1) - 1) * 100
            # then, annual-yield = term-yield * 2
            #
            # ( (100 / 98.8423)^(1/1) - 1 ) * 100 * 2 => 2.34251934647
            #
            #
            term_yield = (pow((100 / bond_quote), (D(1.0) / D(1.0))) - 1) * 100

            if term_months <= 12:
                bond_type = "USTBond - Short-Term"
            if term_months > 12:
                raise Exception("Unexpected term length for tbill asset class")

            bond_type += " - "
            if term_months == 6:
                annual_yield = term_yield * 2
                bond_type += "US Treasury Bill 6mo"
            elif term_months == 12:
                annual_yield = term_yield
                bond_type += "US Treasury Bill 1yr"
            else:
                raise Exception("Unsupported term length for annual yield calculation")

            metadata["name"] = "US Treasury Bill Zero Coupon - " + security
            metadata["bond-type"] = bond_type
            metadata["bond-term-yield"] = round(term_yield, 6)
            metadata["bond-annual-yield"] = round(annual_yield, 6)
            metadata["bond-exp-date"] = bond_exp_date
            metadata["bond-term-months"] = D(term_months)

        elif self.__is_treasury_note(security_description):

            bond_quote = unit_price * 100
            bond_date_mask_pattern = r"UNITED STATES TREAS NTS NOTE \d\.\d*% "
            bond_date_mask_len = re.match(
                bond_date_mask_pattern, security_description
            ).end(0)
            bond_exp_date_str = security_description[bond_date_mask_len:]
            bond_exp_date = datetime.datetime.strptime(bond_exp_date_str, "%m/%d/%Y")
            trade_date = date

            term_months = self.__bond_length_from_dates(trade_date, bond_exp_date)

            if term_months <= 12:
                bond_type = "USTBond - Short-Term"
            if (term_months > 12) and (term_months < 240):
                bond_type = "USTBond - Medium-Term"
            if term_months >= 240:
                bond_type = "USTBond - Long-Term"

            bond_type += " - "
            if term_months == 12:
                bond_type += "US Treasury Note 1yr"
            elif term_months == 24:
                bond_type += "US Treasury Note 2yr"
            elif term_months == 36:
                bond_type += "US Treasury Note 3yr"
            elif term_months == 60:
                bond_type += "US Treasury Note 5yr"
            elif term_months == 120:
                bond_type += "US Treasury Note 10yr"
            elif term_months == 240:
                bond_type += "US Treasury Note 20yr"
            elif term_months == 360:
                bond_type += "US Treasury Note 30yr"
            else:
                raise Exception("Unsupported term length for annual yield calculation")

            # The rate printed on the statement is the 'coupon' rate,
            # not the expected yield or the yield to maturity.
            # See a PDF trade confirmation for more info.
            coupon_rate_pattern = re.compile(r"\d\.\d*%")
            coupon_rate_search_result = coupon_rate_pattern.search(security_description)
            if coupon_rate_search_result:
                coupon_rate_stated_pct_str = coupon_rate_search_result.group(0)
                coupon_rate_stated_pct = D(coupon_rate_stated_pct_str[:-1])
            else:
                coupon_rate_stated_pct_str = None
                coupon_rate_stated_pct = None

            # currently expecting a coupon rate for treasury notes
            assert coupon_rate_stated_pct_str is not None
            assert coupon_rate_stated_pct is not None

            metadata["name"] = "US Treasury Note - " + security
            metadata["bond-coupon-rate"] = coupon_rate_stated_pct
            metadata["bond-exp-date"] = bond_exp_date
            metadata["bond-term-months"] = D(term_months)
            metadata["bond-type"] = bond_type

        return metadata

    def build_commodity_metadata(self, file, counter, commodity=None, metadata={}):
        metadata_ = data.new_metadata(file.name, counter)
        metadata_custom = {}

        metadata_custom = metadata_custom | self.__build_commodity_bond_metadata(
            file, counter, commodity
        )
        return metadata_ | metadata | metadata_custom

    def __is_bought_action(self, type_):
        return re.match(r"YOU\sBOUGHT", type_) is not None

    def __is_sold_action(self, type_):
        return re.match(r"YOU\sSOLD", type_) is not None

    def __is_redemption_payout_action(self, type_):
        return re.match(r"REDEMPTION PAYOUT", type_) is not None

    def __is_fidelityrewards_cashback_action(self, type_):
        return re.match(r"DIRECT\s*DEPOSIT ELAN CARDSVCRedemption", type_) is not None

    def __is_transfer_in_action(self, type_):
        """fidelity to fidelity account incoming transfer"""
        return (
            re.match(r"TRANSFERRED FROM\s*VS .\d\d-\d\d\d\d\d\d-\d", type_) is not None
        )

    def __is_transfer_out_action(self, type_):
        """fidelity to fidelity account outgoing transfer"""
        return re.match(r"TRANSFERRED TO\s*VS .\d\d-\d\d\d\d\d\d-\d", type_) is not None

    def __is_direct_deposit_action(self, type_):
        # Generally transfer from external bank
        return re.match(r"DIRECT\s*DEPOSIT", type_) is not None

    def __is_check_received_action(self, type_):
        return (
            # fidelity brokerage type_
            (type_ == "CHECK RECEIVED (Cash)")
            # fidelity checking type_
            or (re.match(r"CHECK\s*RECEIVED", type_) is not None)
        )

    def __is_direct_debit_action(self, type_):
        # Generally any debit payment
        # (e.g. paying tax, credit card, other account transfers)
        return re.match(r"DIRECT\s*DEBIT", type_) is not None

    def __is_electronic_fund_received_action(self, type_):
        return (type_ == "Electronic Funds Transfer Received") or (
            type_ == "Electronic Funds Transfer Received (Cash)"
        )

    def __is_asset_interest_action(self, type_):
        # NOTE: previously this has been a specific
        # *bond* interest type_ that also checked
        # if self.__is_treasury_note was true from security description
        return (
            re.match(r"INTEREST as of \d\d\/\d\d\/\d\d\d\d", type_) is not None
        ) or (re.match(r"INTEREST UNITED STATES TREAS", type_) is not None)

    def __is_dividend_received_action(self, type_):
        return re.match(r"DIVIDEND RECEIVED", type_) is not None

    def __is_reinvestment_action(self, type_):
        return re.match(r"REINVESTMENT", type_) is not None

    def __is_acat_transfer_in_action(self, type_):
        return type_ == "TRANSFER OF ASSETS   ACAT RECEIVE"

    def __is_hsa_transfer_in_contribution_action(self, type_):
        return re.match(r"PARTIC CONTR CURRENT", type_) is not None

    def __is_hsa_debit(self, type_):
        return re.match(r"NORMAL DISTR PARTIAL DEBIT", type_) is not None

    def convert_transaction_types(self, rdr):
        def transaction_type_map_(type_, row):
            return self.transaction_type_map(type_, row)

        return rdr.convert("type", transaction_type_map_, pass_row=True)

    def transaction_type_map(self, type_, row):
        """Parse type_ strings to find appropriate type"""
        if self.__is_fidelityrewards_cashback_action(type_):
            return "income"
        elif self.__is_bought_action(type_):
            # TODO determine if more info needed to
            # handle specific bond, stock, other buys
            return "buystock"
        elif self.__is_sold_action(type_):
            # TODO determine if more info needed to
            # handle specific bond, stock, other buys
            return "sellstock"
        elif re.match(r"IN LIEU OF FRX SHARE LEU PAYOUT", type_):
            # Special scenario cashout - generally do manually
            return "income"
        elif re.match(r"REVERSE SPLIT R/S", type_):
            # stock split - do manually
            return "sellother"
        elif re.match(r"MERGER", type_):
            # merger - do manually
            return "transfer"
        elif self.__is_redemption_payout_action(type_):
            # TODO determine if more info needed to
            # handle specific bond sale
            return "sellstock"
        elif re.match(r"INTEREST EARNED", type_):
            # Checking interest - typically ticker QHFDQ
            # Brokerage interest - typically ticker QICNQ
            return "income"
        elif re.match(r"CASH ADVANCE.*", type_):
            return "debit"
        elif self.__is_transfer_in_action(type_):
            # Positive (incoming) entry from acct
            # NOTE: assuming cash only
            return "cash"
        elif self.__is_transfer_out_action(type_):
            # Negative entry from acct
            # NOTE: assuming cash only
            return "cash"
        elif self.__is_direct_deposit_action(type_):
            return "dep"
        elif self.__is_check_received_action(type_):
            return "dep"
        elif re.match(r"Check Paid", type_):
            return "debit"
        elif self.__is_direct_debit_action(type_):
            return "debit"
        elif re.match(r"DEBIT\s*CARD PURCHASE", type_):
            return "debit"
        elif self.__is_electronic_fund_received_action(type_):
            # NOTE: assuming cash only
            return "cash"
        elif self.__is_asset_interest_action(type_):
            return "income"
        elif re.match(r"SHORT-TERM CAP GAIN", type_):
            # usually a dividend
            return "capgains_st"
        elif re.match(r"LONG-TERM CAP GAIN", type_):
            # usually a dividend
            return "capgains_lt"
        elif self.__is_dividend_received_action(type_):
            # Typical stock dividend
            # TODO?: To ignore if money market position (treat as interest)
            return "dividends"
        elif self.__is_reinvestment_action(type_):
            # NOTE: amount will be negative
            # TODO: should count as interest if core cash position
            return "buystock"
        elif re.match(r"TRANSFER OF ASSETS.*ACAT RES.CREDIT", type_):
            # usually a small sub-$1 credit
            return "income"
        elif self.__is_acat_transfer_in_action(type_):
            # Incoming transaction from an external non-fidelity account.
            if (row["security"] is None) and (
                row["security_description"] == "No Description"
            ):
                # Either cash transfer
                # or possibly an ACAT transfer fee expense
                # TODO: consider marking as 'Expenses:ACATransferFees' if < $1
                return "cash"
            else:
                # Share transfer in other cases
                return "transfer"
        elif self.__is_hsa_transfer_in_contribution_action(type_):
            return "dep"
        elif self.__is_hsa_debit(type_):
            return "debit"
        else:
            raise Exception("Fidelity CSV: Unknown transaction type: " + type_)

    def get_ticker_info_custom(self, security_id):
        """get raw cusip if ticker isn't available"""
        ticker_info = ()
        assert self.includes_commodities is True

        commodities_by_security = etl.dictlookup(
            self.alltables["commodities"], "security"
        )
        if security_id in commodities_by_security:
            commodity_info = commodities_by_security[security_id][0]
            ticker = commodity_info["security"]
            ticker_long_name = commodity_info["security_description"]
            # NOTE: ticker_long name isn't the same name as in
            #      commodity metadata but isn't currently
            #      utilized anyway.
            ticker_info = ticker, ticker_long_name
        else:
            ticker_info = self.get_ticker_info_from_id(security_id)

        return ticker_info

    def get_target_acct_custom(self, transaction, ticker=None):
        """Get target accounts as configured for transfers,
        and fidelity-specific card / income accounts"""
        # TODO: consider adding 'known expense' matching
        #       (e.g. 'DIRECT               DEBIT IRS           USATAXPYMT')

        transfer_account = getattr(transaction, "transfer_account", None)
        memo = getattr(transaction, "memo", None)
        security_description = getattr(transaction, "security_description", None)
        security = getattr(transaction, "security", None)

        if (
            transaction.type in (self.transfer_unit_types + self.transfer_amount_types)
            and transfer_account is not None
        ):
            transfer_info_account = self.transfer_info_accounts_by_name.get(
                transfer_account, None
            )
            if transfer_info_account is None:
                return self.config["transfer"]
            else:
                account, dedupe_style = transfer_info_account
                return account
        elif transaction.type == "income" and self.__is_fidelityrewards_cashback_action(
            memo
        ):
            return self.config["income_elan_fidelityrewards_cashback"]
        elif (
            transaction.type == "income"
            and self.__is_asset_interest_action(memo)
            and self.__is_treasury_note(security_description)
            and self.includes_accounts
        ):
            # direct bond interest income from
            # commodity-leaf style accounts
            return self.commodity_leaf(self.config["interest"], security)
        else:
            return self.target_account_map.get(transaction.type, None)

        return None

    def skip_transactions(self, ot):
        memo = getattr(ot, "memo", None)
        security = getattr(ot, "security", None)

        if memo is None:
            return False
        elif re.match(r"EXCHANGED TO SPAXX", memo):
            # Skip exchange entry, assuming empty and nothing to do here
            assert ot.total is None
            assert ot.units is None
            return True
        elif self.__is_dividend_received_action(memo) and (
            security in self.money_market_funds
        ):
            # Skip money market dividend received actions
            # assuming a reinvest action will happen anyway
            return True
        else:
            return False

    # validate_cusip based on https://github.com/reedndnb/cusip-utils
    # See also https://en.wikipedia.org/wiki/CUSIP#Check_digit_pseudocode
    def __validate_cusip(self, cusip):
        cusip = re.sub(r"\s+", "", cusip)

        if len(cusip) != 9:
            return {
                "is_valid": False,
                "reason": "Cusip not correct length. Input: %s" % cusip,
            }

        checksum_digit = cusip[8]
        if not checksum_digit.isdigit():
            return {"is_valid": False, "reason": "Checksum digit must be number!"}

        cusip = cusip[:8]

        sum = 0
        for i in range(8):
            v = 0
            c = cusip[i]
            if c.isdigit():
                v = int(c)
            elif c.isalpha():
                # ordinal value of letter, eg. A = 1, B = 2
                p = ord(c) - 64  # ord("A") = 65, so p = 1
                v = p + 9
            elif c == "*":
                v = 36
            elif c == "@":
                v = 37
            elif c == "#":
                v = 38
            if (i + 1) % 2 == 0:
                v = v * 2

            sum = sum + int(v / 10) + v % 10

        checksum = (10 - (sum % 10)) % 10

        if checksum != int(checksum_digit):
            return {"is_valid": False, "reason": "Invalid checksum"}

        return {"is_valid": True}

    def __prepare_raw_cusip_ticker(self, ticker):
        v = self.__validate_cusip(ticker)
        if v["is_valid"]:
            # prepend any tickers which are cusips
            cusip_prepend = getattr(self.config, "cusip_ticker_prepend", "CUSIP")
            return cusip_prepend + ticker
        else:
            return ticker

    def __transfer_account_from_action(self, action):
        """Parse and return fidelity transfer account"""
        transferin_type_preamble = r"TRANSFERRED FROM\s*VS "
        transferout_type_preamble = r"TRANSFERRED TO\s*VS "
        hsa_transferin_type_preamble = r"PARTIC CONTR CURRENT\s*VS "
        transfer_type_account = r".\d\d-\d\d\d\d\d\d-\d"

        def get_transfer_account(action_, transfer_type_preamble):
            match = re.match(transfer_type_preamble, action_)
            acct_start = match.span()[1]
            account = (
                action_[acct_start : (acct_start + 3)]
                + action_[(acct_start + 4) : (acct_start + 10)]
            )
            return account

        directdeposit_type_preamble = r"DIRECT\s*DEPOSIT "
        directdebit_type_preamble = r"DIRECT\s*DEBIT "

        # Direct deposit account name is the rest of Action string
        # WITHOUT space + parenthesized commodity (e.g. ' (Cash)' or ' (AAPL)')
        def get_direct_transact_account(action_, type_preamble):
            preamble_match = re.match(type_preamble, action_)
            post_match = re.search(r" \(.*\)", action_)
            acct_start = preamble_match.span()[1]

            if post_match is None:
                account = action_[acct_start:]
            else:
                acct_stop = post_match.span()[0]
                account = action_[acct_start:acct_stop]
            return account

        if re.match(transferin_type_preamble + transfer_type_account, action):
            return get_transfer_account(action, transferin_type_preamble)
        elif re.match(transferout_type_preamble + transfer_type_account, action):
            return get_transfer_account(action, transferout_type_preamble)
        elif re.search(hsa_transferin_type_preamble + transfer_type_account, action):
            return get_transfer_account(action, hsa_transferin_type_preamble)
        elif re.match(directdeposit_type_preamble, action):
            return get_direct_transact_account(action, directdeposit_type_preamble)
        elif re.match(directdebit_type_preamble, action):
            return get_direct_transact_account(action, directdebit_type_preamble)
        else:
            return None

    def __is_treasury_note(self, security_description):
        match = re.match(
            r"UNITED STATES TREAS NTS NOTE \d\.\d*% \d\d/\d\d/\d\d\d\d",
            security_description,
        )
        if match is None:
            match = re.match(
                r"UNITED STATES TREAS SER BG-\d\d\d\d \d\.\d*% \d\d/\d\d/\d\d\d\d NTS NOTE",
                security_description,
            )
        return match

    def __is_treasury_bill_zero_coupon(self, security_description):
        return re.match(
            r"UNITED STATES TREAS BILLS ZERO CPN 0\.00000% \d\d/\d\d/\d\d\d\d",
            security_description,
        )

    def __convert_par_bond_price(self, price, row):
        """parse out bond data from action and
        insert data for account open/close, commodity,
        and all associated metadata"""
        memo = getattr(row, "memo", None)
        is_bought_action = self.__is_bought_action(memo)
        security_description = getattr(row, "security_description", None)

        def bond_par_price_to_real_price(par_price):
            return par_price / D(100.0)

        if is_bought_action and (
            self.__is_treasury_bill_zero_coupon(security_description)
            or self.__is_treasury_note(security_description)
        ):
            return bond_par_price_to_real_price(price)
        else:
            return price

    def __associate_transaction_values(self, rdr):
        def is_total_to_amount_migration(row):
            if (
                self.transaction_type_map(row["type"], row)
                in self.transfer_amount_types
            ):
                return True
            else:
                return False

        def migrate_total(val, row, func):
            if func:
                return row.total
            else:
                return val

        rdr = rdr.convert(
            "amount",
            lambda a, r: migrate_total(a, r, is_total_to_amount_migration(r)),
            pass_row=True,
        )
        rdr = rdr.convert(
            "total", lambda t: None, where=lambda r: is_total_to_amount_migration(r)
        )

        return rdr

    def prepare_transactions_raw_columns(self, rdr):
        def remove_first_space(t):
            """remove first space"""
            assert t[0] == " "
            return t[1:]

        def blank_sanitize(t):
            if t == "":
                return None
            else:
                return t

        # Setup & remap header columns first
        rdr = rdr.convert("Action", remove_first_space)
        rdr = rdr.addfield("memo", lambda x: x["Action"])
        rdr = rdr.convert("Run Date", remove_first_space)
        rdr = rdr.addfield("tradeDate", lambda x: x["Run Date"])
        rdr = rdr.addfield(
            "transfer_account", lambda x: self.__transfer_account_from_action(x["memo"])
        )
        rdr = rdr.addfield("amount", None)
        rdr = etl.rename(rdr, self.header_map)
        header_keys = list(self.header_map.values())

        # Convert values
        rdr = rdr.convert("security_description", remove_first_space)
        rdr = rdr.convert("security", remove_first_space)
        rdr = rdr.convert(dict(zip(header_keys, [blank_sanitize] * len(header_keys))))

        rdr = self.__associate_transaction_values(rdr)
        rdr = rdr.convert("security", lambda s: self.__prepare_raw_cusip_ticker(s))

        constraints_ = [
            dict(
                # Only support cash security types for now.
                name="security_type_cash_only_supported",
                field="security_type",
                assertion=(lambda s: s == "Cash"),
            ),
        ]
        etl.validate(rdr, constraints=constraints_, header=tuple(header_keys))

        # Convert strings to numbers
        rdr = self.convert_transaction_columns(rdr)

        # Post-number conversion, convert bond prices.
        rdr = rdr.convert(
            "unit_price",
            lambda p, row: self.__convert_par_bond_price(p, row),
            pass_row=True,
        )

        return rdr

    def prepare_commodities_raw_columns(self, rdr):
        """commodities table based on incoming
        prepared transactions table"""

        # Filter down to only bond purchase transactions
        # TODO: consider filtering to any raw CUSIP purchase
        rdr = etl.select(
            rdr,
            lambda c: (
                self.__is_bought_action(c["memo"])
                and (
                    self.__is_treasury_bill_zero_coupon(c["security_description"])
                    or self.__is_treasury_note(c["security_description"])
                )
            ),
        )

        # retain other column information for preparing bond metadata
        return rdr

    def prepare_accounts_raw_columns(self, rdr):
        """accounts table based on incoming
        prepared transactions table"""

        # includes_accounts is primarily for
        # creating commodity-based accounts
        assert self.use_commodity_leaf is True

        # filter down to only bond purchases and redemptions
        # TODO: consider filtering to any raw CUSIP purchase
        rdr = etl.select(
            rdr,
            lambda a: (
                self.__is_bought_action(a["memo"])
                or self.__is_redemption_payout_action(a["memo"])
            )
            and (
                self.__is_treasury_bill_zero_coupon(a["security_description"])
                or self.__is_treasury_note(a["security_description"])
            ),
        )

        def event_type(t, row):
            if self.__is_bought_action(row.memo):
                return "open"
            elif self.__is_redemption_payout_action(row.memo):
                return "close"
            else:
                raise "error - unknown account open/close event"

        rdr = rdr.convert("type", event_type, pass_row=True)

        def bond_accountrow(row_):
            yield [
                row_.date,
                row_.type,
                self.commodity_leaf(self.config["main_account"], row_.security),
            ]
            yield [
                row_.date,
                row_.type,
                self.commodity_leaf(self.config["interest"], row_.security),
            ]
            yield [
                row_.date,
                row_.type,
                self.commodity_leaf(self.config["capgains_st"], row_.security),
            ]
            yield [
                row_.date,
                row_.type,
                self.commodity_leaf(self.config["capgains_lt"], row_.security),
            ]

        rdr = etl.rowmapmany(rdr, bond_accountrow, header=["date", "type", "name"])

        return rdr

    def convert_transaction_columns(self, rdr):
        return csvreader.Importer.convert_columns(self, rdr)

    def is_section_title(self, row):
        header_section_row = tuple(self.header_section_title.split(","))
        return row == header_section_row

    def prepare_tables(self):
        """prepare transactions table
        then create derived tables from
        transactions table for
        commodity & account entries"""

        # Incoming table should be just transactions
        assert len(self.alltables) == 1

        # rename section appropriately
        section = list(self.alltables.keys())[0]
        self.alltables["transactions"] = self.alltables.pop(section)

        # Process transaction table
        t = self.alltables["transactions"]
        t = self.prepare_transactions_raw_columns(t)
        self.alltables["transactions"] = t

        # Create commodities table
        if self.includes_commodities:
            c = self.alltables["transactions"]
            c = self.prepare_commodities_raw_columns(c)
            self.alltables["commodities"] = c

        # Create accounts table
        if self.includes_accounts:
            a = self.alltables["transactions"]
            a = self.prepare_accounts_raw_columns(a)
            self.alltables["accounts"] = a

    def get_transactions(self):
        for transaction in self.alltables["transactions"].namedtuples():
            yield transaction

    def get_commodities(self):
        for commodity in self.alltables["commodities"].namedtuples():
            yield commodity

    def get_accounts(self):
        for account in self.alltables["accounts"].namedtuples():
            yield account
