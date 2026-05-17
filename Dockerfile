FROM python:3.11-slim

LABEL maintainer="SPECTRA Security"
LABEL description="SPECTRA — AI-Powered Security Intelligence Platform"

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .
RUN pip install --no-cache-dir -e .

# Create scan/report directories
RUN mkdir -p /app/scans /app/reports

VOLUME ["/app/scans", "/app/reports"]

ENTRYPOINT ["spectra"]
CMD ["--help"]
