# ── Stage 1: build ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies
COPY scraper/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY scraper/ ./scraper/

# Persistent volumes for markdown output and SQLite delta DB
VOLUME ["/app/articles", "/app/data"]

# ── Entry point ───────────────────────────────────────────────────────────────
# Default: run the full pipeline (no test mode)
# Override with: docker run ... python scraper/main.py --test
WORKDIR /app/scraper
CMD ["python", "main.py"]
