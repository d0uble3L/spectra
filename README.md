# SPECTRA

**Security Platform for Expert-level Correlation, Triage, and Risk Analysis**

SPECTRA is an AI-powered CLI that transforms raw security scanner output into
actionable intelligence — ranked findings, executive summaries, attack chain
analysis, and concrete remediation steps. Powered by Claude.

---

## Features

- **Auto-detects** Trivy, Semgrep, and generic scanner formats
- **AI analysis** via Claude — de-duplication, severity calibration, attack chain identification
- **Two output formats** — rich Markdown reports and structured JSON
- **Prompt caching** — the analyst system prompt is cached after the first call (~90% cheaper on repeats)
- **CI/CD-native** — GitHub Actions workflows for both code (Semgrep) and container (Trivy) scanning, with AI-generated PR comments
- **Docker-ready** — mount your scan files, get reports back

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/d0uble3L/spectra.git
cd spectra
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Add your Anthropic API key to .env
```

### 3. Analyze

```bash
# Analyze a Trivy container scan
spectra analyze tests/samples/trivy_sample.json

# Analyze a Semgrep SAST report → save as JSON
spectra analyze tests/samples/semgrep_sample.json --format json --output reports/out

# Pipe any scanner output
cat nessus_report.txt | spectra analyze --scanner generic

# Both formats + show token usage
spectra analyze trivy.json --format both --output reports/run1 --usage
```

---

## Usage

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

## CI/CD Integration

SPECTRA ships with two GitHub Actions workflows that scan every push and pull
request, then post the AI analysis directly as a PR comment.

### Workflows

| Workflow | File | Trigger | Scanner | What it scans |
|----------|------|---------|---------|---------------|
| Code Security | `code-security.yml` | push / PR | Semgrep | Source code (SAST) |
| Container Security | `container-security.yml` | push / PR (Dockerfile or deps changed) | Trivy | Built container image |

Both workflows:
1. Run the scanner and capture JSON output
2. Upload SARIF results to the **GitHub Security tab**
3. Feed JSON output to Spectra for AI-powered triage
4. **Post the Spectra report as a PR comment** (on pull requests)
5. Upload the Markdown report as a workflow artifact

### Setup

Add your Anthropic API key as a GitHub Actions secret:

```
Settings → Secrets and variables → Actions → New repository secret
Name:  ANTHROPIC_API_KEY
Value: sk-ant-...
```

That's it — the next push or PR will trigger both scans automatically.

### Local scanning with Make

```bash
# Run Semgrep SAST + Spectra (requires: pip install semgrep)
make scan-code

# Build image, run Trivy + Spectra (requires: trivy)
make scan-container

# Both back-to-back
make scan-all
```

Reports land in `reports/` as both `.md` and `.json`.

---

## Docker

```bash
# Build
docker compose build

# Run analysis (scans/ and reports/ are mounted as volumes)
docker compose run --rm analyze scans/trivy.json --format both --output /app/reports/out

# Or use the interactive service
docker compose run --rm spectra analyze scans/semgrep.json
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
│   ├── code-security.yml        # Semgrep SAST → Spectra → PR comment
│   └── container-security.yml  # Trivy image scan → Spectra → PR comment
├── spectra/
│   ├── analyzer.py              # Claude API integration + prompt caching
│   ├── cli.py                   # Typer CLI
│   ├── models.py                # Pydantic output schema
│   ├── parsers/                 # Scanner normalizers (Trivy, Semgrep, generic)
│   └── reporters/               # Markdown + JSON output
├── tests/samples/               # Sample scan files for testing
├── scans/                       # Mount your scanner output here
├── reports/                     # Generated reports land here
├── Makefile                     # Developer shortcuts
├── Dockerfile
└── docker-compose.yml
```

---

## Roadmap

- [x] Trivy container scan support
- [x] Semgrep SAST support
- [x] Prompt caching (~90% cost reduction on repeat runs)
- [x] CI/CD GitHub Actions integration with PR comments
- [x] Docker support
- [ ] REST API (FastAPI) for programmatic integration
- [ ] Web UI for analysts
- [ ] Multi-scanner batch processing
- [ ] Jira / ServiceNow ticket creation
- [ ] Trend analysis and risk scoring over time

---

## Requirements

- Python 3.9+
- Anthropic API key ([get one here](https://console.anthropic.com/))
