"""Offline checks of installed utility behavior and download orchestration."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from click.testing import CliRunner

from beancount_reds_importers.importers.ibkr import flexquery_download
from beancount_reds_importers.util import bean_download, ofx_summarize


@pytest.fixture
def download_config(tmp_path):
    file = tmp_path / "download.cfg"
    file.write_text(
        "[bank]\ntype=bank\ncmd=download-bank\n[card]\ntype=card\ndisplay=Visit the card website\n"
    )
    return file


def test_list_institutions_alias_and_filters(download_config):
    runner = CliRunner()
    result = runner.invoke(bean_download.cli, ["list", "-c", str(download_config), "--sort"])
    assert result.exit_code == 0
    assert "bank (1)" in result.output and "card (1)" in result.output
    config = bean_download.readConfigFile(str(download_config))
    assert bean_download.get_sites(config.sections(), "bank", config) == ["bank"]
    ctx = SimpleNamespace(params={"config_file": str(download_config)})
    assert bean_download.complete_sites(ctx, None, "ba") == ["bank"]
    assert bean_download.complete_site_types(ctx, None, "ca") == ["card"]


@pytest.mark.parametrize(
    "returncode,summary", [(0, "2/2 sites succeeded"), (1, "1/2 sites failed")]
)
def test_download_commands_are_mocked(download_config, monkeypatch, returncode, summary):
    process = SimpleNamespace(
        returncode=returncode, communicate=AsyncMock(return_value=(b"", b""))
    )
    create = AsyncMock(return_value=process)
    monkeypatch.setattr(bean_download.asyncio, "create_subprocess_shell", create)
    result = CliRunner().invoke(bean_download.cli, ["download", "-c", str(download_config)])
    assert result.exit_code == 0
    assert summary in result.output and "Visit the card website" in result.output
    create.assert_awaited_once()
    assert create.call_args.args == ("download-bank",)


def test_download_dry_run_and_missing_site(download_config, monkeypatch):
    create = AsyncMock()
    monkeypatch.setattr(bean_download.asyncio, "create_subprocess_shell", create)
    monkeypatch.setattr(bean_download.asyncio, "sleep", AsyncMock())
    runner = CliRunner()
    result = runner.invoke(
        bean_download.cli,
        ["download", "-c", str(download_config), "--dry-run", "-t", "bank", "--verbose"],
    )
    assert result.exit_code == 0 and "1/1 sites succeeded" in result.output
    create.assert_not_awaited()
    result = runner.invoke(
        bean_download.cli, ["download", "-c", str(download_config), "-i", "missing"]
    )
    assert result.exit_code == 0 and "Couldn't find missing" in result.output


def test_download_template_is_packaged():
    result = CliRunner().invoke(bean_download.cli, ["config-template"])
    assert result.exit_code == 0 and "[" in result.output


def test_ibkr_download_retries_pending_statement(monkeypatch):
    monkeypatch.setattr(
        flexquery_download.requests,
        "post",
        lambda *a, **kw: SimpleNamespace(
            status_code=200,
            text="<ReferenceCode>123</ReferenceCode>",
        ),
    )
    responses = iter(["Statement generation in progress", "<FlexQueryResponse />"])
    monkeypatch.setattr(
        flexquery_download.requests,
        "get",
        lambda *a, **kw: SimpleNamespace(
            status_code=200,
            text=next(responses),
        ),
    )
    monkeypatch.setattr(flexquery_download.time, "sleep", lambda seconds: None)
    result = CliRunner().invoke(flexquery_download.flexquery_download, ["fake-token", "456"])
    assert result.exit_code == 0 and "<FlexQueryResponse />" in result.output


def test_ibkr_unexpected_response_reports_failure(monkeypatch):
    monkeypatch.setattr(
        flexquery_download.requests,
        "post",
        lambda *a, **kw: SimpleNamespace(
            status_code=200,
            text="<Error>Invalid query</Error>",
        ),
    )
    result = CliRunner().invoke(flexquery_download.flexquery_download, ["fake-token", "456"])
    assert result.exit_code == 1 and "couldn't parse" in result.output


@pytest.mark.parametrize(
    "stats_only,code,output", [(True, 0, "0"), (False, 1, "Zero byte input file")]
)
def test_ofx_empty_file_behavior(tmp_path, stats_only, code, output):
    file = tmp_path / "empty.ofx"
    file.touch()
    args = [str(file)] + (["--stats-only"] if stats_only else [])
    result = CliRunner().invoke(ofx_summarize.summarize, args)
    assert result.exit_code == code and output in result.output
