# SPECTRA

**AI-powered vulnerability intelligence that turns scanner noise into ranked, actionable findings your team can act on today.**

▸ CYBERSECURITYOS · OPEN SOURCE

📖 [Official Documentation](https://www.cybersecurityos.net/docs/spectra/) &nbsp;·&nbsp; 📝 [Read the Post](https://www.cybersecurityos.net/posts/os-weekly/spectra-overview-claude-ai-security/) &nbsp;·&nbsp; ⭐ [GitHub](https://github.com/d0uble3L/spectra)

---

## The Problem

| | |
|---|---|
| **131** new CVEs / day | **~2%** are ever exploited |
| **< 5 days** median time to exploit | **4.8M** security workforce gap |

Traditional vulnerability management tools score severity in isolation — not whether the exploit path is reachable in your environment, not what attackers are actively using, not what your CISO needs to hear.

**Score Inflation** — 28% of Q1 2025 exploited vulnerabilities had only medium CVSS scores. Teams prioritizing by score alone are systematically looking in the wrong direction.

**Triage Overload** — With 131 new CVEs per day and a 4.8 million person workforce gap, manual triage isn't just slow — it's burning analyst time on findings that will never be exploited.

**Exploit Velocity** — Median time from CVE disclosure to active exploitation dropped from 745 days in 2020 to under 5 days today. Manual triage wasn't built for this speed.

---

## What SPECTRA Does

SPECTRA sits downstream of your existing scanners — Trivy, Semgrep, Nessus — and applies Claude AI to produce intelligence your team can immediately act on.

| Capability | Description |
|---|---|
| **Ranked Findings** | Vulnerabilities prioritized by real-world exploitability, not theoretical CVSS scores |
| **Attack Chain Analysis** | Connects related vulnerabilities into exploitable paths across your scanner's separate findings |
| **Executive Summaries** | Leadership-ready briefings generated automatically — no manual translation required |
| **Actionable Remediation** | Not "patch this CVE" — but how, where, and why, specific to your stack |
| **Scanner Agnostic** | Trivy, Semgrep, Nessus, any JSON scanner output — plugs into what you already have |
| **Dual Output** | Markdown and JSON — ready for dashboards, ticketing systems, or Slack bots |

---

## Quick Start

Running in under 60 seconds. Python 3.9+. No cloud account. No SaaS onboarding.

```bash
# Clone and install
git clone https://github.com/d0uble3L/spectra
cd spectra && pip install -e .

# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key

# Run against your scanner output
spectra analyze trivy.json
```

```
▸ Loading scan results... 47 findings
▸ Analyzing attack chains...
▸ Ranking by real-world severity...
▸ Generating executive summary...

✓ Analysis complete
  Critical: 3 · High: 11 · Medium: 22 · Low: 11
  Output: spectra-report.md + spectra-report.json

# 3 critical paths worth your attention today.
# The other 44? Documented. Deprioritized. Defensible.
```

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

## Use Cases

**Vulnerability Management** — Stop drowning in scanner output. SPECTRA ranks what matters, chains what connects, and produces the prioritized remediation plan your team needs — not a spreadsheet of CVEs sorted by CVSS.

**DevSecOps Pipeline** — Plug SPECTRA into your CI/CD pipeline and get actionable security context on every build — without flooding developers with noise that kills velocity and trust.

**Red Team Reporting** — Transform raw engagement findings into chained attack narratives that actually land with leadership. Connect your findings into the story that drives remediation investment.

**GRC & Compliance Reporting** — Generate board-ready risk summaries and compliance evidence automatically. Map findings to controls. Produce the artifacts your auditors need without the manual overhead.

---

## Web UI

```bash
pip install -e ".[api]"

# Terminal 1 — FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — React dev server
cd web && npm install && npm run dev
```

Open **http://localhost:3000** for the analyst dashboard or **http://localhost:8000/api/docs** for the API explorer.

---

## CI/CD Integration

SPECTRA ships with two GitHub Actions workflows that scan every push and pull request, then post AI analysis directly as a PR comment.

| Workflow | Scanner | What it scans |
|----------|---------|---------------|
| `sast` | Semgrep | Source code (SAST) |
| `container-scan` | Trivy | Built container image |

```
Settings → Secrets and variables → Actions → New repository secret
Name:  ANTHROPIC_API_KEY
Value: sk-ant-...
```

```bash
make scan-code       # Semgrep + Spectra locally
make scan-container  # Trivy + Spectra locally
make scan-all        # both back-to-back
```

---

## Docker

```bash
# CLI analysis
docker compose run --rm analyze scans/trivy.json --format both --output /app/reports/out

# Web UI + API
docker compose up api   # → http://localhost:8000
```

---

## GitHub Releases

```bash
git tag v1.0.0 && git push --tags
# → Release created automatically with changelog
```

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload scan file → AI report |
| `GET` | `/api/reports` | List past reports |
| `GET` | `/api/reports/{id}` | Fetch a report |
| `GET` | `/api/docs` | Interactive Swagger UI |

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
│   ├── parsers/              # Scanner normalizers
│   └── reporters/            # Markdown + JSON output
├── tests/samples/            # Sample scan files for testing
├── Makefile                  # Developer shortcuts
└── Dockerfile                # Hardened: non-root user, patched build tools
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
- [ ] Persistent report storage
- [ ] Jira / ServiceNow ticket creation
- [ ] Trend analysis and risk scoring over time

---

## Requirements

- Python 3.9+
- Node 18+ (Web UI only)
- Anthropic API key ([get one here](https://console.anthropic.com/))

---

## Documentation

Full documentation, setup guides, and API reference:

**https://www.cybersecurityos.net/docs/spectra/**

---

*Open source. No vendor lock-in. Runs in your environment. Powered by Claude.*

**[CYBERSECURITYOS](https://www.cybersecurityos.net) · [GITHUB](https://github.com/d0uble3L/spectra) · [READ THE POST](https://www.cybersecurityos.net/posts/os-weekly/spectra-overview-claude-ai-security/)**
