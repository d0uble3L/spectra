"""Smoke tests for parsers — no API calls required."""
import json
from pathlib import Path

import pytest

from spectra.parsers import generic, semgrep, snyk, trivy
from spectra.parsers.auto import detect_and_normalize

SAMPLES = Path(__file__).parent / "samples"


def test_trivy_auto_detect():
    raw = (SAMPLES / "trivy_sample.json").read_text()
    result = detect_and_normalize(raw, hint="auto")
    assert "TRIVY" in result
    assert "CVE-2022-37434" in result
    assert "CRITICAL" in result


def test_semgrep_auto_detect():
    raw = (SAMPLES / "semgrep_sample.json").read_text()
    result = detect_and_normalize(raw, hint="auto")
    assert "SEMGREP" in result
    assert "sql-injection" in result.lower() or "SQL" in result


def test_trivy_explicit():
    raw = (SAMPLES / "trivy_sample.json").read_text()
    result = detect_and_normalize(raw, hint="trivy")
    assert "TRIVY" in result


def test_semgrep_explicit():
    raw = (SAMPLES / "semgrep_sample.json").read_text()
    result = detect_and_normalize(raw, hint="semgrep")
    assert "SEMGREP" in result


def test_generic_fallback():
    raw = "This is a pentest report. Found admin:admin credentials."
    result = detect_and_normalize(raw, hint="auto")
    assert "generic" in result.lower() or "admin:admin" in result


def test_generic_hint():
    raw = "Some scanner output"
    result = detect_and_normalize(raw, hint="generic")
    assert "generic" in result.lower()


def test_snyk_open_source_auto_detect():
    raw = json.dumps({
        "ok": False,
        "dependencyCount": 1,
        "displayTargetFile": "package-lock.json",
        "vulnerabilities": [{
            "id": "SNYK-JS-EXAMPLE-123",
            "title": "Example dependency issue",
            "severity": "high",
            "packageName": "example-package",
            "version": "1.0.0",
            "fixedIn": ["1.0.1"],
            "cvssScore": 7.5,
            "identifiers": {"CVE": ["CVE-2025-1234"]},
        }],
    })

    result = detect_and_normalize(raw)

    assert "SNYK SECURITY SCAN" in result
    assert "SNYK-JS-EXAMPLE-123" in result
    assert "example-package 1.0.0" in result
    assert "CVE-2025-1234" in result
    assert "Fixed in : 1.0.1" in result


def test_snyk_container_explicit():
    raw = json.dumps({
        "ok": False,
        "docker": {"baseImage": "python:3.12"},
        "vulnerabilities": [{"id": "SNYK-OS-EXAMPLE-123", "severity": "critical"}],
    })

    result = detect_and_normalize(raw, hint="snyk")

    assert "Snyk Container" in result
    assert "python:3.12" in result
    assert "[CRITICAL] SNYK-OS-EXAMPLE-123" in result


def test_snyk_iac_auto_detect():
    raw = json.dumps({
        "infrastructureAsCodeIssues": [{
            "id": "SNYK-CC-EXAMPLE-123",
            "impact": "high",
            "title": "Public storage bucket",
            "path": "main.tf",
            "lineNumber": 12,
            "resourceName": "bucket.example",
            "msg": "The bucket allows public access.",
        }],
    })

    result = detect_and_normalize(raw)

    assert "Snyk IaC" in result
    assert "[HIGH] SNYK-CC-EXAMPLE-123" in result
    assert "main.tf:12" in result
    assert "bucket.example" in result


def test_snyk_code_sarif_auto_detect():
    raw = json.dumps({
        "runs": [{
            "tool": {
                "driver": {
                    "name": "Snyk Code",
                    "rules": [{
                        "id": "javascript/SQL_INJECTION",
                        "shortDescription": {"text": "SQL injection"},
                        "helpUri": "https://example.test/rule",
                    }],
                },
            },
            "results": [{
                "ruleId": "javascript/SQL_INJECTION",
                "level": "error",
                "message": {"text": "Untrusted input reaches a SQL query."},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": "src/app.js"},
                        "region": {"startLine": 42},
                    },
                }],
            }],
        }],
    })

    result = detect_and_normalize(raw)

    assert "Snyk Code" in result
    assert "[HIGH] javascript/SQL_INJECTION" in result
    assert "src/app.js:42" in result
    assert "Untrusted input" in result


def test_snyk_auto_detect_requires_snyk_shape():
    raw = json.dumps({"vulnerabilities": [{"id": "OTHER-123"}]})

    assert not snyk.is_snyk(json.loads(raw))
    assert "generic" in detect_and_normalize(raw).lower()
