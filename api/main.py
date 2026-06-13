from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from spectra import __version__
from spectra.analyzer import analyze
from spectra.models import AnalysisReport
from spectra.parsers import detect_and_normalize
from spectra.reporters import render_markdown

app = FastAPI(
    title="SPECTRA API",
    description="AI-Powered Security Intelligence Platform",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Comma-separated list of allowed origins, e.g. "https://app.example.com,https://admin.example.com"
# Defaults to "*" for local development.
_cors_origins = os.environ.get("CORS_ORIGINS", "*")
_allow_origins = ["*"] if _cors_origins.strip() == "*" else [
    origin.strip() for origin in _cors_origins.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    file: UploadFile = File(...),
    scanner: str = Form("auto"),
    model: str = Form("claude-opus-4-7"),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        normalized = detect_and_normalize(content, hint=scanner)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Parse error: {exc}") from exc

    try:
        report, _usage = await run_in_threadpool(analyze, normalized, model=model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    report_id = str(uuid.uuid4())
    filename = Path(file.filename).name if file.filename else "unknown"
    entry = {
        "id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "filename": filename,
        "scanner_type": report.scanner_type,
        "risk_level": report.risk_level,
        "overall_risk_score": report.overall_risk_score,
        "report": report.model_dump(mode="json"),
        "markdown": render_markdown(report),
    }
    async with _reports_lock:
        _reports[report_id] = entry

    return {"id": report_id, "report": report}


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/api/reports")
async def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
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
async def get_report(report_id: str):
    async with _reports_lock:
        entry = _reports.get(report_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Report not found.")
    return entry


@app.delete("/api/reports/{report_id}", status_code=204)
async def delete_report(report_id: str):
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
