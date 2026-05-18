from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from spectra.analyzer import analyze
from spectra.models import AnalysisReport
from spectra.parsers import detect_and_normalize
from spectra.reporters import render_markdown

app = FastAPI(
    title="SPECTRA API",
    description="AI-Powered Security Intelligence Platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory report store — keyed by report ID
_reports: dict[str, dict] = {}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


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
    _reports[report_id] = {
        "id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "filename": file.filename or "unknown",
        "scanner_type": report.scanner_type,
        "risk_level": report.risk_level,
        "overall_risk_score": report.overall_risk_score,
        "report": report.model_dump(mode="json"),
        "markdown": render_markdown(report),
    }

    return {"id": report_id, "report": report}


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/api/reports")
async def list_reports():
    return [
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


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    entry = _reports.get(report_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Report not found.")
    return entry


# ── Static frontend (production build) ───────────────────────────────────────

_dist = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
else:
    # No built frontend — redirect root to interactive API docs
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/api/docs")
