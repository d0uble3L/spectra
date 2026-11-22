"""Tests for invoking Snyk through the Spectra CLI without external services."""
import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from spectra import cli


@pytest.mark.parametrize(
    ("product", "target", "subcommand", "scan_result"),
    [
        (
            "code",
            "src",
            ["code", "test", "--json", "src"],
            {"runs": [{"tool": {"driver": {"name": "Snyk Code"}}, "results": []}]},
        ),
        (
            "container",
            "example:latest",
            ["container", "test", "--json", "example:latest"],
            {"docker": {"baseImage": "python:3.12"}, "vulnerabilities": []},
        ),
        (
            "iac",
            "infra",
            ["iac", "test", "--json", "infra"],
            {"infrastructureAsCodeIssues": []},
        ),
    ],
)
def test_scan_uses_snyk_product_command(
    monkeypatch,
    product,
    target,
    subcommand,
    scan_result,
):
    calls = {}

    def fake_run(command, **kwargs):
        calls["command"] = command
        return SimpleNamespace(returncode=0, stdout=json.dumps(scan_result), stderr="")

    monkeypatch.setattr(cli.shutil, "which", lambda _: "/usr/local/bin/snyk")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(cli, "analyze", lambda *args, **kwargs: (object(), {}))
    monkeypatch.setattr(cli, "render_json", lambda _report: "{}")

    result = CliRunner().invoke(
        cli.app,
        ["scan", "snyk", "--product", product, "--target", target, "--format", "json"],
    )

    assert result.exit_code == 0, result.output
    assert calls["command"] == ["/usr/local/bin/snyk", *subcommand]


def test_scan_runs_open_source_and_accepts_findings(monkeypatch, tmp_path):
    scan = {
        "ok": False,
        "dependencyCount": 1,
        "vulnerabilities": [{"id": "SNYK-JS-EXAMPLE-123", "severity": "high"}],
    }
    calls = {}

    def fake_run(command, **kwargs):
        calls["command"] = command
        calls["kwargs"] = kwargs
        return SimpleNamespace(returncode=1, stdout=json.dumps(scan), stderr="")

    monkeypatch.setattr(cli.shutil, "which", lambda _: "/usr/local/bin/snyk")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(cli, "analyze", lambda *args, **kwargs: (object(), {}))
    monkeypatch.setattr(cli, "render_json", lambda _report: "{}")

    result = CliRunner().invoke(
        cli.app,
        [
            "scan",
            "snyk",
            "--product",
            "open-source",
            "--target",
            str(tmp_path),
            "--snyk-arg=--all-projects",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls["command"] == [
        "/usr/local/bin/snyk",
        "test",
        "--json",
        "--all-projects",
    ]
    assert calls["kwargs"]["cwd"] == tmp_path


def test_scan_reports_missing_snyk_cli(monkeypatch):
    monkeypatch.setattr(cli.shutil, "which", lambda _: None)

    result = CliRunner().invoke(
        cli.app,
        ["scan", "snyk", "--product", "code"],
    )

    assert result.exit_code == 1
    assert "Snyk CLI not found" in result.output
