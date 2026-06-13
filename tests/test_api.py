"""Smoke tests for the FastAPI app — no Anthropic API calls required."""
import importlib

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


def test_cors_defaults_to_wildcard(client):
    res = client.get("/api/reports", headers={"Origin": "https://example.com"})
    assert res.headers["access-control-allow-origin"] == "*"


def test_cors_restricts_to_configured_origins(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://allowed.example.com")
    from api import main as api_main

    importlib.reload(api_main)
    client = TestClient(api_main.app)

    res = client.get("/api/reports", headers={"Origin": "https://allowed.example.com"})
    assert res.headers["access-control-allow-origin"] == "https://allowed.example.com"

    res = client.get("/api/reports", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in res.headers
