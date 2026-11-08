"""Accounting assertions independent of institution-specific statement layouts."""

import itertools
from datetime import date, datetime
from types import SimpleNamespace

import petl as etl
import pytest
from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.number import D

from beancount_reds_importers.libreader import reader
from beancount_reds_importers.libtransactionbuilder import (
    banking,
    common,
    investments,
    paycheck,
    transactionbuilder,
)

DAY = date(2025, 1, 2)
TIME = datetime(2025, 1, 2)


def transaction(**overrides):
    values = dict(
        type="buystock",
        date=TIME,
        tradeDate=TIME,
        memo="Trade",
        payee="Store",
        security="ABC",
        units=D("2"),
        unit_price=D("10"),
        total=D("-20"),
        amount=D("-20"),
    )
    return SimpleNamespace(**(values | overrides))


def entry():
    return data.Transaction({}, DAY, "*", None, "Test", frozenset(), frozenset(), [])


class InvestmentImporter(reader.Reader, investments.Importer):
    """Supply normalized reader output without relying on a bank's file format."""

    def initialize_reader(self, file):
        self.reader_ready = True
        self.currency = "USD"

    def read_file(self, file):
        pass

    def get_transactions(self):
        return iter(self.transactions)

    def get_balance_positions(self):
        return iter(self.positions)

    def get_balance_assertion_date(self):
        return DAY

    def get_available_cash(self, settlement_fund_balance=0):
        return self.cash - settlement_fund_balance if self.cash is not None else None

    def date(self, file):
        return TIME

    def get_ticker_info(self, security_id):
        return self.get_ticker_info_from_id(security_id)


@pytest.fixture
def investment():
    importer = InvestmentImporter(
        {
            "main_account": "Assets:Broker:{source401k}:{ticker}",
            "cash_account": "Assets:Broker:{currency}",
            "transfer": "Assets:Transfers",
            "dividends": "Income:Dividends:{ticker}",
            "interest": "Income:Interest",
            "cg": "Income:Gains:{ticker}",
            "capgainsd_lt": "Income:Long:{ticker}",
            "capgainsd_st": "Income:Short:{ticker}",
            "fees": "Expenses:Fees",
            "rounding_error": "Equity:Rounding",
            "fund_info": {
                "money_market": ["MMF"],
                "fund_data": [
                    ("ABC", "US123", "Example Fund"),
                    ("MMF", "US456", "Cash Fund"),
                ],
            },
        }
    )
    importer.transactions = []
    importer.positions = []
    importer.cash = None
    importer.initialize("statement")
    return importer


@pytest.mark.parametrize("kind", ["buymf", "buystock", "buyother", "buydebt", "reinvest"])
def test_purchase_cost_and_counterposting(investment, kind):
    investment.transactions = [transaction(type=kind, security="US123")]
    result = investment.extract("statement")[0]
    holding, counter = result.postings
    assert holding.units == Amount(D("2"), "ABC")
    assert holding.cost.number == D("10")
    assert holding.cost.currency == "USD"
    assert holding.price is None
    assert counter.units == Amount(D("-20"), "USD")
    assert counter.account == (
        "Income:Dividends:ABC" if kind == "reinvest" else "Assets:Broker:USD"
    )
    assert result.date == DAY


@pytest.mark.parametrize("kind", ["sellmf", "sellstock", "sellother"])
def test_sale_preserves_unresolved_lots_and_gain(investment, kind):
    result = investment.generate_trade_entry(
        transaction(type=kind, security="US123", total=D("20")),
        "statement",
        itertools.count(),
    )
    holding, gain, cash = result.postings
    assert holding.units == Amount(D("-2"), "ABC")
    assert holding.price == Amount(D("10"), "USD")
    assert holding.cost.number_per is None
    assert gain.account == "Income:Gains:ABC" and gain.units is None
    assert cash.units == Amount(D("20"), "USD")
    assert "todo" in result.meta


@pytest.mark.parametrize(
    "total,price,rounding",
    [
        ("20", "10", None),
        ("-20.01", "10", "0.01"),
        ("-20", "0", None),
    ],
)
def test_purchase_price_fallback_sign_and_rounding(investment, total, price, rounding):
    result = investment.generate_trade_entry(
        transaction(security="US123", total=D(total), unit_price=D(price)),
        "statement",
        itertools.count(),
    )
    assert result.postings[0].cost.number == D("10")
    assert result.postings[1].units.number < 0
    assert len(result.postings) == (3 if rounding else 2)
    if rounding:
        assert result.postings[2].account == "Equity:Rounding"
        assert result.postings[2].units.number == D(rounding)


def test_money_market_uses_price_and_settlement_metadata(investment):
    result = investment.generate_trade_entry(
        transaction(
            security="US456",
            settleDate=datetime(2025, 1, 3),
        ),
        "statement",
        itertools.count(),
    )
    assert result.postings[0].cost is None
    assert result.postings[0].price == Amount(D("10"), "USD")
    assert result.meta["settlement_date"] == "2025-01-03"


@pytest.mark.parametrize(
    "kind,target",
    [
        ("dividends", "Income:Dividends:ABC"),
        ("income", "Income:Interest"),
        ("capgainsd_lt", "Income:Long:ABC"),
        ("capgainsd_st", "Income:Short:ABC"),
        ("fee", "Expenses:Fees"),
    ],
)
def test_cash_income_and_expense_postings(investment, kind, target):
    result = investment.generate_transfer_entry(
        transaction(type=kind, security="US123", total=D("5")),
        "statement",
        itertools.count(),
    )
    assert [(p.account, p.units.number) for p in result.postings] == [
        ("Assets:Broker:USD", D("5")),
        (target, D("-5")),
    ]


@pytest.mark.parametrize(
    "kind", ["credit", "debit", "dep", "cash", "other", "payment", "check", "xfer"]
)
def test_cash_transfers_and_optional_target(investment, kind):
    ot = transaction(type=kind, security="", currency="EUR", amount=D("-12"), tradeDate=None)
    result = investment.generate_transfer_entry(ot, "statement", itertools.count())
    assert result.date == DAY
    assert result.postings[0].units == Amount(D("-12"), "EUR")
    if kind in ("payment", "check", "xfer"):
        assert len(result.postings) == 1
    else:
        assert result.postings[1].units == Amount(D("12"), "EUR")


def test_in_kind_transfer_and_source_account(investment):
    result = investment.generate_transfer_entry(
        transaction(
            type="transfer",
            security="US123",
            inv401ksource="PRETAX",
        ),
        "statement",
        itertools.count(),
    )
    assert result.postings[0].account == "Assets:Broker:Pretax:ABC"
    assert result.postings[0].units == Amount(D("2"), "ABC")
    assert result.postings[1].units == Amount(D("-2"), "ABC")


def test_fees_commissions_and_skip_hook(investment, monkeypatch):
    investment.transactions = [transaction(security="US123", fees=D("1"), commission=D("2"))]
    result = investment.extract("statement")[0]
    assert [p.units.number for p in result.postings[2:]] == [D("1"), D("2")]
    monkeypatch.setattr(investment, "skip_transaction", lambda ot: True)
    assert investment.extract("statement") == []


def test_balances_prices_and_cash_exclude_settlement_fund(investment):
    investment.positions = [
        SimpleNamespace(security="US456", units=D("50"), unit_price=D("1"), date=TIME)
    ]
    investment.cash = D("70")
    balance, price, cash = investment.extract("statement")
    assert isinstance(balance, data.Balance)
    assert balance.amount == Amount(D("50"), "MMF")
    assert balance.date == DAY
    assert isinstance(price, data.Price) and price.amount == Amount(D("1"), "USD")
    assert cash.account == "Assets:Broker:USD" and cash.amount == Amount(D("20"), "USD")


def test_balance_fallback_dates(investment, monkeypatch):
    monkeypatch.setattr(investment, "get_balance_assertion_date", lambda: None)
    investment.positions = [SimpleNamespace(security="US123", units=D("2"), date=TIME)]
    investment.cash = D("3")
    assert [e.date for e in investment.extract("statement")] == [DAY, DAY]
    monkeypatch.setattr(investment, "date", lambda file: None)
    assert len(investment.extract("statement")) == 1


def test_security_lookup_and_missing_configuration(investment, capsys):
    assert investment.get_ticker_info_from_id("123") == ("ABC", "Example Fund")
    assert investment.get_ticker_info_from_id(None)[0] == "NOTICKER"
    investment.transactions = [transaction(security="MISSING"), transaction(security="")]
    with pytest.raises(SystemExit):
        investment.get_ticker_info_from_id("MISSING")
    assert "MISSING" in capsys.readouterr().err
    with pytest.raises(KeyError, match="not set"):
        investment.get_acct("absent", None, "ABC")


def test_target_override_and_dividend_income(investment, monkeypatch):
    ot = transaction(type="income", income_type="DIV")
    assert investment.get_target_acct(ot, "ABC") == "Income:Dividends:{ticker}"
    monkeypatch.setattr(investment, "get_target_acct_custom", lambda ot, ticker: "Income:Custom")
    assert investment.get_target_acct(ot, "ABC") == "Income:Custom"


class BankImporter(reader.Reader, banking.Importer):
    def initialize_reader(self, file):
        self.currency = "USD"

    def read_file(self, file):
        pass

    def get_transactions(self):
        return iter(self.transactions)

    def get_balance_statement(self, file=None):
        return [None, banking.Balance(DAY, D("100"), "USD")]


def test_banking_amounts_foreign_currency_and_reuse():
    importer = BankImporter({"main_account": "Assets:Bank", "target_account": "Expenses:Food"})
    importer.transactions = [
        transaction(),
        transaction(foreign_amount=D("1.2"), foreign_currency="EUR"),
    ]
    results = importer.extract("first")
    assert results[0].postings[0].units == Amount(D("-20"), "USD")
    assert results[0].postings[1].units is None
    assert results[0].payee == "Trade" and results[0].narration == "Store"
    assert results[1].postings[0].price == Amount(D("1.2"), "EUR")
    assert results[2].amount == Amount(D("100"), "USD")
    importer.transactions = [transaction(amount=D("8"), currency="CAD")]
    assert importer.extract("second")[0].postings[0].units == Amount(D("8"), "CAD")
    assert importer.match_account_number("001234", "1234")


@pytest.mark.parametrize(
    "account,amount,expected",
    [
        ("Income:Salary", "5", "-5"),
        ("Equity:Opening", "5", "-5"),
        ("Liabilities:Tax", "5", "-5"),
        ("Expenses:Tax", "-5", "5"),
        ("Assets:Bank", "-5", "5"),
        ("Assets:Bank", "0", "0"),
    ],
)
def test_paycheck_account_signs(account, amount, expected):
    assert paycheck.flip_if_needed(D(amount), account) == D(expected)


class PaycheckImporter(reader.Reader, paycheck.Importer):
    pass


@pytest.mark.parametrize("sort_postings", [True, False])
def test_paycheck_balanced_postings_and_unknown_sections(sort_postings, capsys):
    importer = PaycheckImporter(
        {
            "currency": "USD",
            "sort_postings": sort_postings,
            "show_unconfigured": True,
            "paycheck_template": {
                "Pay": {
                    "Salary": "Income:Salary",
                    "Deposit": "Assets:Bank",
                    "Match": ["Income:Match", "Assets:Retirement"],
                }
            },
        }
    )
    importer.alltables = {
        "Pay": etl.wrap(
            [
                ["description", "amount"],
                ["Salary", "100"],
                ["Deposit", "100"],
                ["Match", "10"],
                ["Salary zero", "0"],
                ["Unmapped", "5"],
            ]
        ),
        "Unknown Section": etl.wrap([["description", "amount"], ["Other", "1"]]),
    }
    result = importer.build_postings(entry())
    assert sum(p.units.number for p in result.postings) == 0
    assert len(result.postings) == 4
    assert result.postings[0].account == ("Assets:Bank" if sort_postings else "Income:Salary")
    assert "Unmapped" in capsys.readouterr().out


def test_paycheck_unbalanced_and_workday_columns():
    importer = PaycheckImporter(
        {"currency": "USD", "paycheck_template": {"Pay": {"Salary": "Income:Salary"}}}
    )
    importer.alltables = {
        "Pay": etl.wrap([["bank", "amount_in_pay_group_currency"], ["Salary", "100"]])
    }
    result = importer.build_postings(entry())
    assert [(p.account, p.units.number) for p in result.postings] == [
        ("Income:Salary", D("-100")),
        ("TOTAL:NONZERO", D("-100")),
    ]


def test_config_substitution_metadata_and_customization_defaults():
    builder = transactionbuilder.TransactionBuilder()
    builder.config = {"main_account": "Assets:Broker:{ticker}:{currency}", "option": True}
    builder.set_config_variables({"ticker": "{ticker}", "currency": "USD"})
    assert builder.config["main_account"] == "Assets:Broker:{ticker}:USD"
    assert builder.build_metadata("file") == {"filing_account": "Assets:Broker:USD"}
    builder.config["emit_filing_account_metadata"] = False
    assert builder.build_metadata("file") == {}
    assert builder.custom_entry_mods([1]) == [1]
    assert not builder.skip_transaction(None)
    assert not builder.get_tags() and not builder.get_links()


def test_zero_price_requires_explicit_handler(capsys):
    with pytest.raises(common.PriceCostBothZeroException):
        common.create_simple_posting_with_price(entry(), "Assets:Broker", "1", "ABC", 0, "USD")
    assert "WARNING" in capsys.readouterr().out
    handled = []
    posting = common.create_simple_posting_with_cost(
        None,
        "Assets:Broker",
        "1",
        "ABC",
        0,
        "USD",
        price_cost_both_zero_handler=lambda entry, ot: handled.append(ot),
        ot="tiny",
    )
    assert handled == ["tiny"] and posting.units == Amount(D("1"), "ABC")
