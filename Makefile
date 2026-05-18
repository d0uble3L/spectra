.PHONY: install install-api test lint scan-code scan-container scan-all dev api-dev web-dev clean

# ── Setup ─────────────────────────────────────────────────────────────────────

install:
	pip install -e ".[dev]"

install-api:
	pip install -e ".[api,dev]"

# ── Quality ───────────────────────────────────────────────────────────────────

test:
	pytest tests/ -v

lint:
	ruff check spectra/ tests/

# ── Local scanning ────────────────────────────────────────────────────────────

# Run Semgrep SAST → Spectra report (requires: pip install semgrep)
scan-code:
	@mkdir -p reports
	semgrep --config auto --json --output semgrep.json .
	spectra analyze semgrep.json --format both --output reports/code-security --usage

# Build image then run Trivy container scan → Spectra report (requires: trivy)
scan-container:
	@mkdir -p reports
	docker build -t spectra:local .
	trivy image --format json --output trivy.json spectra:local
	spectra analyze trivy.json --format both --output reports/container-security --usage

# Run both scans back-to-back
scan-all: scan-code scan-container

# ── Dev servers ───────────────────────────────────────────────────────────────

# Start FastAPI backend (requires: make install-api)
api-dev:
	uvicorn api.main:app --reload --port 8000

# Start React frontend dev server (requires: cd web && npm install)
web-dev:
	cd web && npm run dev

# Start both concurrently (requires: npm install -g concurrently)
dev:
	concurrently "make api-dev" "make web-dev"

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	rm -f semgrep.json semgrep.sarif trivy.json trivy.sarif
	rm -rf reports/code-security* reports/container-security* web/dist
