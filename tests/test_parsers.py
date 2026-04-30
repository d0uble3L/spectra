"""Smoke tests for parsers — no API calls required."""
import json
from pathlib import Path

import pytest

from spectra.parsers.auto import detect_and_normalize
from spectra.parsers import trivy, semgrep, generic

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
