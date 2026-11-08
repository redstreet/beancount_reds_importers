"""Exercise format and normalization boundaries with small synthetic inputs."""

import json
from datetime import date, datetime
from types import SimpleNamespace

import openpyxl
import petl as etl
import pytest
from beancount.core.number import D
from lxml import etree

from beancount_reds_importers.libreader import (
    csv_multitable_reader,
    csvreader,
    jsonreader,
    ofxreader,
    pdfreader,
    reader,
    schwabjsonreader,
    tsvreader,
    xlsreader,
    xlsx_multitable_reader,
    xlsxreader,
    xmlreader,
)
from beancount_reds_importers.libtransactionbuilder import banking


class CsvImporter(csvreader.Importer, banking.Importer):
    def custom_init(self):
        super().custom_init()
        self.filename_pattern_def = ".*"
        self.header_identifier = "Date"
        self.date_format = "%Y-%m-%d"
        self.header_map = {"Date": "date", "Amount": "amount", "Payee": "payee"}
        self.transaction_type_map = {"Purchase": "debit"}
        self.skip_transaction_types = {"ignore"}


@pytest.fixture
def csv_importer():
    result = CsvImporter({"main_account": "Assets:Bank", "currency": "USD"})
    result.custom_init()
    return result


def test_csv_identification_extraction_and_new_file(csv_importer, tmp_path):
    first = tmp_path / "first.csv"
    first.write_text('Date,Amount,Payee\n2025-01-02,"$1,234.50",Store\n')
    assert csv_importer.identify(str(first))
    assert not csv_importer.identify(str(first.with_suffix(".pdf")))
    assert csv_importer.date(str(first)) == date(2025, 1, 2)
    assert list(csv_importer.get_transactions())[0].amount == D("1234.50")
    second = tmp_path / "second.csv"
    second.write_text("Date,Amount,Payee\n2025-02-03,-5,Another\n")
    assert csv_importer.date(str(second)) == date(2025, 2, 3)
    assert list(csv_importer.get_transactions())[0].amount == D("-5")
    assert csv_importer.account(str(second)) == "Assets:Bank"
    assert csv_importer.get_balance_assertion_date() == date(2025, 2, 4)
    assert csv_importer.filename(r"C:\statements\second.csv") == "second.csv"


def test_csv_empty_and_wrong_header(csv_importer, tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("Date,Amount,Payee\n")
    assert csv_importer.date(str(path)) is None
    assert csv_importer.get_max_transaction_date() is None
    wrong = tmp_path / "wrong.csv"
    wrong.write_text("Unrelated\n")
    assert not csv_importer.identify(str(wrong))
    csv_importer.config["filename_pattern"] = "other.*"
    assert not csv_importer.identify(str(path))


def test_csv_currency_date_and_type_normalization(csv_importer):
    table = etl.wrap(
        [
            ["date", "tradeDate", "type", "amount", "units", "memo"],
            [" 2025-01-02 ", "2025-01-03", "Purchase", "-$1,234.56", "2.5", "Text"],
        ]
    )
    row = list(csv_importer.convert_columns(table).namedtuples())[0]
    assert row.type == "debit" and row.amount == D("-1234.56") and row.units == D("2.5")
    assert row.date == datetime(2025, 1, 2) and row.tradeDate == datetime(2025, 1, 3)
    assert row.memo == "Text"
    del csv_importer.date_format
    assert list(
        csv_importer.convert_columns(
            etl.wrap(
                [
                    ["date"],
                    ["2025-01-02T12:00:00"],
                ]
            )
        ).namedtuples()
    )[0].date == datetime(2025, 1, 2, 12)


def test_csv_malformed_conversion_fails_loudly(csv_importer):
    # petl captures conversion errors by default. Assertion ensures it cannot
    # silently turn malformed input into a valid dated transaction.
    table = csv_importer.convert_columns(etl.wrap([["date"], ["not a date"]]))
    assert list(table.namedtuples())[0].date is None


def test_csv_headers_footers_comments_and_rows(csv_importer, tmp_path):
    path = tmp_path / "statement.csv"
    path.write_text(
        "Preamble\nDate,Amount,Payee\n#comment\n2025-01-02,1,Skip\n2025-01-03,2,Keep\nFooter\n"
    )
    csv_importer.column_labels_line = "Date,Amount,Payee"
    csv_importer.skip_tail_rows = 1
    csv_importer.skip_comments = "#"
    csv_importer.skip_data_rows = 1
    csv_importer.initialize(str(path))
    csv_importer.read_file(str(path))
    assert [r.payee for r in csv_importer.get_transactions()] == ["Keep"]
    assert csv_importer.get_row_by_label(str(path), "Date")[1] == "Amount"


def test_csv_table_boundaries_and_missing_headers(csv_importer):
    table = etl.wrap([["Preamble"], ["date", "amount"], ["2025-01-02", "1"], ["", ""], ["Footer"]])
    assert list(csv_importer.extract_table_with_header(table, ["DATE", "AMOUNT"])) == [
        ("date", "amount"),
        ("2025-01-02", "1"),
    ]
    assert next(iter(csv_importer.skip_until_row_contains(table, "date").data())) == (
        "2025-01-02",
        "1",
    )
    with pytest.raises(SystemExit):
        csv_importer.skip_until_main_table(table, ["absent"])
    with pytest.raises(SystemExit):
        csv_importer.skip_until_row_contains(table, "absent")
    fixed = csv_importer.fix_column_names(etl.wrap([["1 Amount", "Fees & Tax"], [1, 2]]))
    assert fixed.header() == ("_1_Amount", "Fees___Tax")


def test_csv_skip_types_and_trade_dates(csv_importer):
    csv_importer.rdr = etl.wrap(
        [
            ["type", "date", "tradeDate"],
            ["ignore", datetime(2030, 1, 1), datetime(2030, 1, 1)],
            ["debit", datetime(2025, 1, 2), datetime(2025, 1, 3)],
        ]
    )
    assert len(list(csv_importer.get_transactions())) == 1
    assert csv_importer.get_max_transaction_date() == date(2025, 1, 3)


class OfxImporter(ofxreader.Importer, banking.Importer):
    pass


@pytest.fixture
def ofx_importer():
    result = OfxImporter({"main_account": "Assets:Bank", "account_number": "123"})
    result.currency = "USD"
    result.ofx_account = SimpleNamespace(
        statement=SimpleNamespace(
            end_date=datetime(2025, 1, 10),
            balance_date=datetime(2025, 1, 12),
            available_balance_date=datetime(2025, 1, 11),
            balance=D("10"),
            available_cash=D("25"),
            transactions=[SimpleNamespace(date=datetime(2025, 1, 9))],
        )
    )
    return result


@pytest.mark.parametrize(
    "policy,expected",
    [
        ("smart", date(2025, 1, 11)),
        ("ofx_date", date(2025, 1, 11)),
        ("last_transaction", date(2025, 1, 10)),
    ],
)
def test_ofx_balance_date_policies(ofx_importer, policy, expected):
    ofx_importer.config["balance_assertion_date_type"] = policy
    assert ofx_importer.get_balance_assertion_date() == expected


def test_ofx_smart_dates_empty_positions_and_available_cash(ofx_importer):
    ofx_importer.config["balance_assertion_date_fudge"] = 0
    assert ofx_importer.get_smart_date() == date(2025, 1, 12)
    assert ofx_importer.get_available_cash(D("5")) == D("20")
    assert list(ofx_importer.get_balance_positions()) == []
    assert list(ofx_importer.get_balance_statement())[0].amount == D("10")
    statement = ofx_importer.ofx_account.statement
    statement.transactions = []
    statement.end_date = None
    assert ofx_importer.get_max_transaction_date() is None
    assert ofx_importer.get_smart_date() is None
    assert ofx_importer.get_balance_assertion_date() is None
    assert list(ofx_importer.get_balance_statement()) == []
    del statement.balance
    del statement.available_cash
    assert list(ofx_importer.get_balance_statement()) == []
    assert ofx_importer.get_available_cash() is None
    assert ofx_importer.date("unused") is None


def test_ofx_malformed_input_does_not_identify(ofx_importer, tmp_path):
    file = tmp_path / "broken.ofx"
    file.write_text("<OFX></OFX>")
    ofx_importer.initialize_reader(str(file))
    assert not ofx_importer.reader_ready
    assert ofx_importer.match_account_number("123", "123")
    assert not ofx_importer.match_account_number("00123", "123")


class JsonImporter(jsonreader.Importer, banking.Importer):
    def deep_identify(self, file):
        return self.json_data.get("account") == "123"


class XmlImporter(xmlreader.Importer, banking.Importer):
    pass


@pytest.mark.parametrize("kind", ["json", "xml"])
def test_structured_readers_transactions_currency_and_reuse(kind, tmp_path):
    if kind == "json":
        importer = JsonImporter({"currency": "EUR"})
        content = json.dumps(
            {"account": "123", "Transactions": {"Transaction": [{"amount": "2"}]}}
        )
    else:
        importer = XmlImporter({"currency": "EUR"})
        content = '<Transactions><Transaction amount="2"/></Transactions>'
    file = tmp_path / f"statement.{kind}"
    file.write_text(content)
    importer.initialize_reader(str(file))
    assert importer.reader_ready and importer.currency == "EUR"
    assert list(importer.get_transactions()) == [{"amount": "2"}]
    assert importer.date(str(file)) is None
    importer.read_file(str(file))
    if kind == "json":
        assert list(importer.get_json_elements("missing.path")) == []
        assert list(
            importer.get_json_elements("Transactions.Transaction", lambda v: int(v["amount"]))
        ) == [2]
    else:
        assert list(
            importer.get_xpath_elements("/Transactions/Transaction", lambda v: int(v["amount"]))
        ) == [2]
    second = tmp_path / f"other.{kind}"
    second.write_text(content.replace('"2"', '"3"'))
    importer.initialize_reader(str(second))
    assert list(importer.get_transactions()) == [{"amount": "3"}]


@pytest.mark.parametrize(
    "kind,error", [("json", json.JSONDecodeError), ("xml", etree.XMLSyntaxError)]
)
def test_structured_readers_reject_invalid_documents(kind, error, tmp_path):
    importer = JsonImporter({}) if kind == "json" else XmlImporter({})
    file = tmp_path / f"broken.{kind}"
    file.write_text("not a document")
    with pytest.raises(error):
        importer.initialize_reader(str(file))


class ExcelImporter(xlsreader.Importer, banking.Importer):
    pass


class XlsxImporter(xlsxreader.Importer, banking.Importer):
    pass


@pytest.mark.parametrize("precision,expected", [(0, "13"), (2, "12.55"), (8, "12.54500000")])
def test_excel_quantizes_half_up(precision, expected):
    importer = ExcelImporter({})
    importer.currency_precision = precision
    result = importer.convert_columns(etl.wrap([["amount", "other"], ["12.545", "unchanged"]]))
    row = list(result.namedtuples())[0]
    assert row.amount == D(expected) and row.other == "unchanged"


@pytest.mark.parametrize(
    "fmt,precision",
    [
        ("General", None),
        ("", None),
        ("0", 0),
        ("$#,##0.00", 2),
        ("0.00000000", 8),
        ("yyyy-mm-dd", None),
    ],
)
def test_excel_format_precision(fmt, precision):
    assert XlsxImporter({}).get_precision_from_format(fmt) == precision


def test_xlsx_real_workbook_format_metadata_and_fallback(tmp_path):
    file = tmp_path / "amounts.xlsx"
    wb = openpyxl.Workbook()
    wb.active.append(["amount", "note"])
    wb.active.append([1.2345, "first"])
    wb.active.append([2.3456, "second"])
    for row in (2, 3):
        wb.active.cell(row, 1).number_format = "0.000"
    wb.save(file)
    importer = XlsxImporter({})
    table = importer.read_raw(str(file))
    assert importer.get_precision_for_field(table, "amount") == 3
    assert importer.get_precision_for_field(table, "missing") == 2
    assert importer.get_precision_for_field(etl.wrap([["amount"], [1]]), "amount") == 2
    importer.header_identifier = "amount.*"
    importer.initialize_reader(str(file))
    assert importer.reader_ready


class MultiImporter(csv_multitable_reader.Importer, banking.Importer):
    def prepare_tables(self):
        pass


def test_csv_multiple_tables_and_footer(tmp_path):
    file = tmp_path / "tables.csv"
    file.write_text(
        "Preamble\nEarnings\ndescription,amount\nSalary,100\nTaxes\ndescription,amount\nFederal,20\nEnd\n"
    )
    importer = MultiImporter({})
    importer.file_read_done = False
    importer.skip_head_rows = 1
    importer.skip_tail_rows = 1
    importer.read_file(str(file))
    assert set(importer.alltables) == {"Earnings", "Taxes"}
    assert list(importer.alltables["Earnings"].namedtuples())[0].amount == "100"
    importer.read_file("not-read-again")
    assert list(importer.get_transactions()) == []
    assert importer.get_available_cash() is None


class XlsxMultiImporter(xlsx_multitable_reader.Importer, banking.Importer):
    pass


def test_xlsx_multiple_table_titles_and_raw_values(tmp_path):
    file = tmp_path / "tables.xlsx"
    wb = openpyxl.Workbook()
    for row in [["Earnings"], ["description", "amount"], ["Salary", 100]]:
        wb.active.append(row)
    wb.save(file)
    importer = XlsxMultiImporter({})
    importer.initialize_reader(str(file))
    assert importer.reader_ready and not importer.file_read_done
    assert importer.is_section_title(["Earnings", None, ""])
    assert not importer.is_section_title(["description", "amount"])
    assert list(importer.read_raw(str(file)))[2] == ("Salary", "100")


class TsvImporter(tsvreader.Importer, banking.Importer):
    pass


def test_tsv_columns(tmp_path):
    file = tmp_path / "table.tsv"
    file.write_text("date\tamount\n2025-01-02\t5\n")
    assert list(TsvImporter({}).read_raw(str(file)))[1] == ("2025-01-02", "5")


class PdfImporter(pdfreader.Importer, banking.Importer):
    pass


def test_pdf_crop_table_continuation_and_missing_section():
    importer = PdfImporter({})
    importer.pdf_table_extraction_crop = (10, 20, 30, 40)
    assert importer.get_adjusted_crop(0, SimpleNamespace(width=600, height=800)) == (
        10,
        20,
        570,
        760,
    )
    importer.pdf_page_break_top = 50
    tables = [
        {"section": "", "bbox": (0, 100, 100, 200), "table": [["amount"], ["1"]]},
        {"section": "", "bbox": (0, 10, 100, 100), "table": [["amount"], ["2"]]},
    ]
    result = importer.find_and_fix_broken_tables(tables)
    assert len(result) == 1 and result[0]["table"] == [["amount"], ["1"], ["2"]]
    importer.alltables = {}
    importer.transaction_table_section = "missing"
    with pytest.raises(KeyError, match="Table section 'missing'"):
        list(importer.get_transactions())


def test_reader_defaults_and_unimplemented_transactions():
    base = reader.Reader()
    base.config = {"currency": "CAD"}
    base.set_currency()
    assert base.currency == "CAD"
    assert base.get_balance_statement() == [] and base.get_balance_positions() == []
    assert base.get_balance_assertion_date() is None and base.get_available_cash() is None
    with pytest.raises(NotImplementedError, match="get_transactions"):
        base.get_transactions()


class SchwabJsonImporter(schwabjsonreader.Importer, banking.Importer):
    def get_transactions(self):
        return iter([SimpleNamespace(date=datetime(2025, 1, 2))])


def test_legacy_schwab_json_reader(tmp_path):
    file = tmp_path / "schwab.json"
    file.write_text('{"BrokerageTransactions": []}')
    importer = SchwabJsonImporter({})
    assert importer.date(str(file)) == date(2025, 1, 2)
    assert importer.rdr == {"BrokerageTransactions": []}
    assert importer.get_balance_assertion_date() is None
