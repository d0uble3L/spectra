from __future__ import annotations

import asyncio
import os
import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from spectra import __version__
from spectra.analyzer import DEFAULT_MODEL, analyze
from spectra.parsers import detect_and_normalize
from spectra.reporters import render_markdown


def _positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return parsed


_api_auth_token = os.getenv("SPECTRA_API_TOKEN")
_max_upload_bytes = _positive_int_env("SPECTRA_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
_max_reports = _positive_int_env("SPECTRA_MAX_REPORTS", 100)

app = FastAPI(
    title="SPECTRA API",
    description="AI-Powered Security Intelligence Platform",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Comma-separated list of allowed origins. Defaults to the local Vite dev server.
_cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
_allow_origins = [
    origin.strip() for origin in _cors_origins.split(",") if origin.strip()
]
if "*" in _allow_origins:
    raise ValueError("CORS_ORIGINS must list explicit origins; wildcard origins are not allowed.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


def require_api_auth(
    x_spectra_api_token: str | None = Header(default=None, alias="X-Spectra-API-Token"),
):
    if _api_auth_token is None:
        return
    if x_spectra_api_token is None or not secrets.compare_digest(
        x_spectra_api_token,
        _api_auth_token,
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing API token.")


# In-memory report store — keyed by report ID
_reports: dict[str, dict] = {}
_reports_lock = asyncio.Lock()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__}


# ── Analysis ──────────────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze_scan(
    file: UploadFile = File(...),  # noqa: B008
    scanner: str = Form("auto"),
    model: str | None = Form(None),
    _authorized: None = Depends(require_api_auth),
):
    model = model or os.getenv("SPECTRA_MODEL") or DEFAULT_MODEL
    content_bytes = await file.read(_max_upload_bytes + 1)
    if len(content_bytes) > _max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds {_max_upload_bytes} bytes.",
        )
    content = content_bytes.decode("utf-8", errors="replace")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        normalized = detect_and_normalize(content, hint=scanner)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Parse error: {exc}") from exc

    try:
        report, _usage = await run_in_threadpool(analyze, normalized, model=model)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Check server logs for details.",
        ) from exc

    report_id = str(uuid.uuid4())
    filename = Path(file.filename).name if file.filename else "unknown"
    entry = {
        "id": report_id,
        "created_at": datetime.now(UTC).isoformat(),
        "filename": filename,
        "scanner_type": report.scanner_type,
        "risk_level": report.risk_level,
        "overall_risk_score": report.overall_risk_score,
        "report": report.model_dump(mode="json"),
        "markdown": render_markdown(report),
    }
    async with _reports_lock:
        _reports[report_id] = entry
        if len(_reports) > _max_reports:
            oldest_id = min(
                _reports,
                key=lambda existing_id: _reports[existing_id]["created_at"],
            )
            del _reports[oldest_id]

    return {"id": report_id, "report": report}


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/api/reports")
async def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _authorized: None = Depends(require_api_auth),
):
    async with _reports_lock:
        summaries = [
            {
                "id": v["id"],
                "created_at": v["created_at"],
                "filename": v["filename"],
                "scanner_type": v["scanner_type"],
                "risk_level": v["risk_level"],
                "overall_risk_score": v["overall_risk_score"],
            }
            for v in sorted(_reports.values(), key=lambda x: x["created_at"], reverse=True)
        ]

    return {
        "items": summaries[offset : offset + limit],
        "total": len(summaries),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/reports/{report_id}")
async def get_report(
    report_id: str,
    _authorized: None = Depends(require_api_auth),
):
    async with _reports_lock:
        entry = _reports.get(report_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Report not found.")
    return entry


@app.delete("/api/reports/{report_id}", status_code=204)
async def delete_report(
    report_id: str,
    _authorized: None = Depends(require_api_auth),
):
    async with _reports_lock:
        if report_id not in _reports:
            raise HTTPException(status_code=404, detail="Report not found.")
        del _reports[report_id]


# ── Static frontend (production build) ───────────────────────────────────────

_dist = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
else:
    # No built frontend — redirect root to interactive API docs
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/api/docs")
