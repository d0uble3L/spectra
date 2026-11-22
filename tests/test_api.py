"""Smoke tests for the FastAPI app — no Anthropic API calls required."""
import importlib
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from api import main as api_main

    importlib.reload(api_main)
    api_main._reports.clear()
    for i in range(3):
        api_main._reports[f"id-{i}"] = {
            "id": f"id-{i}",
            "created_at": f"2024-01-0{i + 1}T00:00:00+00:00",
            "filename": f"scan-{i}.json",
            "scanner_type": "trivy",
            "risk_level": "HIGH",
            "overall_risk_score": 50 + i,
            "report": {},
            "markdown": "",
        }
    return TestClient(api_main.app)


def test_list_reports_default_pagination(client):
    res = client.get("/api/reports")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 3
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert [r["id"] for r in body["items"]] == ["id-2", "id-1", "id-0"]


def test_list_reports_limit_and_offset(client):
    res = client.get("/api/reports?limit=1&offset=1")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 3
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert [r["id"] for r in body["items"]] == ["id-1"]


def test_delete_report(client):
    res = client.delete("/api/reports/id-0")
    assert res.status_code == 204

    res = client.get("/api/reports/id-0")
    assert res.status_code == 404

    res = client.get("/api/reports")
    assert res.json()["total"] == 2


def test_delete_missing_report(client):
    res = client.delete("/api/reports/does-not-exist")
    assert res.status_code == 404


def test_analyze_snyk_upload(client, monkeypatch):
    from api import main as api_main
    from spectra.models import AnalysisReport

    report = AnalysisReport(
        executive_summary="No significant risks.",
        overall_risk_score=0,
        risk_level="LOW",
        scanner_type="Snyk Open Source",
    )
    captured = {}

    def fake_analyze(content, model):
        captured["content"] = content
        return report, {}

    monkeypatch.setattr(api_main, "analyze", fake_analyze)
    scan = {
        "ok": False,
        "dependencyCount": 1,
        "vulnerabilities": [{
            "id": "SNYK-JS-EXAMPLE-123",
            "severity": "high",
            "packageName": "example-package",
            "version": "1.0.0",
        }],
    }

    res = client.post(
        "/api/analyze",
        data={"scanner": "snyk"},
        files={"file": ("snyk.json", json.dumps(scan), "application/json")},
    )

    assert res.status_code == 200
    assert "SNYK-JS-EXAMPLE-123" in captured["content"]


def test_cors_defaults_to_local_frontend_origins(client):
    allowed = client.get("/api/reports", headers={"Origin": "http://localhost:3000"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" not in allowed.headers

    denied = client.get("/api/reports", headers={"Origin": "https://example.com"})
    assert "access-control-allow-origin" not in denied.headers


def test_cors_restricts_to_configured_origins(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://allowed.example.com")
    from api import main as api_main

    importlib.reload(api_main)
    client = TestClient(api_main.app)

    res = client.get("/api/reports", headers={"Origin": "https://allowed.example.com"})
    assert res.headers["access-control-allow-origin"] == "https://allowed.example.com"
    assert "access-control-allow-credentials" not in res.headers

    res = client.get("/api/reports", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in res.headers


def test_cors_rejects_wildcard_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(ValueError, match="explicit origins"):
        from api import main as api_main

        importlib.reload(api_main)
