# SPECTRA

**Security Platform for Expert-level Correlation, Triage, and Risk Analysis**

SPECTRA is an AI-powered CLI and web platform that transforms raw security scanner output into
actionable intelligence — ranked findings, executive summaries, attack chain
analysis, and concrete remediation steps. Powered by Claude.

---

## Features

- **Auto-detects** Trivy, Semgrep, and generic scanner formats
- **AI analysis** via Claude — de-duplication, severity calibration, attack chain identification
- **Two output formats** — rich Markdown reports and structured JSON
- **Prompt caching** — the analyst system prompt is cached after the first call (~90% cheaper on repeats)
- **Web UI** — dark-themed analyst dashboard with drag-and-drop upload, findings table, and report history
- **REST API** — FastAPI backend for programmatic integration and CI/CD pipelines
- **CI/CD-native** — GitHub Actions workflows for both code (Semgrep) and container (Trivy) scanning, with AI-generated PR comments
- **Docker-ready** — mount your scan files, get reports back

---

## Quick Start

### CLI

```bash
git clone https://github.com/d0uble3L/spectra.git
cd spectra
pip install -e .
cp .env.example .env   # add your Anthropic API key

# Analyze a Trivy container scan
spectra analyze tests/samples/trivy_sample.json

# Analyze a Semgrep SAST report → save as JSON
spectra analyze tests/samples/semgrep_sample.json --format json --output reports/out

# Both formats + show token usage
spectra analyze trivy.json --format both --output reports/run1 --usage
```

### Web UI

```bash
pip install -e ".[api]"

# Terminal 1 — FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — React dev server (proxies /api → :8000)
cd web && npm install && npm run dev
```

Open **http://localhost:3000** for the analyst dashboard, or **http://localhost:8000/api/docs** for the interactive API explorer.

---

## CLI Usage

```
spectra analyze [OPTIONS] [INPUT_FILE]

Arguments:
  INPUT_FILE    Scanner output file (omit to read from stdin)

Options:
  -s, --scanner   Scanner format: auto, trivy, semgrep, generic  [default: auto]
  -f, --format    Output format: markdown, json, both             [default: markdown]
  -o, --output    Write output to file
  -m, --model     Claude model to use                             [default: claude-opus-4-7]
  -t, --think     Stream Claude's reasoning (verbose)
  -u, --usage     Print token usage after analysis
```

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload scan file → AI report |
| `GET` | `/api/reports` | List past reports |
| `GET` | `/api/reports/{id}` | Fetch a report |
| `GET` | `/health` | Health check |
| `GET` | `/api/docs` | Interactive Swagger UI |

```bash
# Quick smoke test
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@tests/samples/trivy_sample.json" \
  -F "scanner=auto"
```

---

## CI/CD Integration

SPECTRA ships with two GitHub Actions workflows that scan every push and pull
request, then post the AI analysis directly as a PR comment.

### Workflows

| Workflow | Trigger | Scanner | What it scans |
|----------|---------|---------|---------------|
| `sast` | push / PR | Semgrep | Source code (SAST) |
| `container-scan` | push / PR (Dockerfile or deps changed) | Trivy | Built container image |

Both workflows post a Spectra AI report as a PR comment and upload a Markdown artifact.

### Setup

Add your Anthropic API key as a GitHub Actions secret:

```
Settings → Secrets and variables → Actions → New repository secret
Name:  ANTHROPIC_API_KEY
Value: sk-ant-...
```

### Local scanning with Make

```bash
make scan-code       # Semgrep + Spectra (requires: pip install semgrep)
make scan-container  # Trivy + Spectra (requires: trivy)
make scan-all        # both back-to-back
```

---

## GitHub Releases

Push a version tag to cut a release with auto-generated changelog:

```bash
git tag v1.0.0
git push --tags
```

Pre-release tags (`-alpha`, `-beta`, `-rc`) are automatically marked as pre-release on GitHub.

---

## Docker

```bash
# CLI analysis
docker compose run --rm analyze scans/trivy.json --format both --output /app/reports/out

# Web UI + API server
docker compose up api   # → http://localhost:8000
```

---

## Supported Scanners

| Scanner | Format | Auto-detect |
|---------|--------|:-----------:|
| Trivy | JSON | ✅ |
| Semgrep | JSON | ✅ |
| Nessus / OpenVAS | Text | via `--scanner generic` |
| Burp Suite | Text export | via `--scanner generic` |
| Pentest notes | Plain text | via `--scanner generic` |

---

## Project Structure

```
spectra/
├── .github/workflows/
│   ├── sast.yml              # Semgrep SAST → Spectra → PR comment
│   ├── container-scan.yml    # Trivy image scan → Spectra → PR comment
│   └── release.yml           # Auto GitHub Release on version tags
├── api/
│   └── main.py               # FastAPI REST API
├── web/
│   └── src/                  # React analyst dashboard (Vite + Tailwind)
├── spectra/
│   ├── analyzer.py           # Claude API integration + prompt caching
│   ├── cli.py                # Typer CLI
│   ├── models.py             # Pydantic output schema
│   ├── parsers/              # Scanner normalizers (Trivy, Semgrep, generic)
│   └── reporters/            # Markdown + JSON output
├── tests/samples/            # Sample scan files for testing
├── Makefile                  # Developer shortcuts
├── Dockerfile                # Hardened: non-root user, patched build tools
└── docker-compose.yml
```

---

## Roadmap

- [x] Trivy container scan support
- [x] Semgrep SAST support
- [x] Prompt caching (~90% cost reduction on repeat runs)
- [x] CI/CD GitHub Actions integration with PR comments
- [x] Docker support (non-root, hardened image)
- [x] REST API (FastAPI)
- [x] Web UI analyst dashboard (React + Vite)
- [x] GitHub Releases workflow
- [ ] Multi-scanner batch processing
- [ ] Persistent report storage (PostgreSQL / SQLite)
- [ ] Jira / ServiceNow ticket creation
- [ ] Trend analysis and risk scoring over time

---

## Requirements

- Python 3.9+
- Node 18+ (Web UI only)
- Anthropic API key ([get one here](https://console.anthropic.com/))
