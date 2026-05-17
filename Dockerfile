FROM python:3.11-slim

LABEL maintainer="SPECTRA Security"
LABEL description="SPECTRA — AI-Powered Security Intelligence Platform"

WORKDIR /app

# Create non-root user before any file ownership is set
RUN groupadd --system --gid 1001 spectra \
    && useradd --system --uid 1001 --gid spectra --no-create-home spectra

# Upgrade pip, wheel, and setuptools to patched versions (CVE-2026-6357,
# CVE-2025-8869, CVE-2026-3219, CVE-2026-24049) before installing deps
RUN pip install --no-cache-dir --upgrade \
    "pip>=26.1" \
    "wheel>=0.46.2" \
    "setuptools>=78.0" \
    "jaraco.context>=6.1.0"

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source, install, and fix ownership in one layer
COPY . .
RUN pip install --no-cache-dir -e . \
    && mkdir -p /app/scans /app/reports \
    && chown -R spectra:spectra /app

VOLUME ["/app/scans", "/app/reports"]

USER spectra

ENTRYPOINT ["spectra"]
CMD ["--help"]
