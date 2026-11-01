# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder
#   Installs Python dependencies into /install so the runtime image stays lean.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-time OS deps (gcc needed for psycopg2 C extension)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime
#   Minimal image — no build tools, no root user.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime OS deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user (UID 1001) — never run as root in prod.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --uid 1001 --no-create-home appuser

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source — owned by appuser, not root
COPY --chown=appuser:appgroup app/ ./app/

# Switch to non-root user before any EXPOSE or CMD
USER appuser

EXPOSE 8000

# Docker HEALTHCHECK — the container is considered healthy only when /health
# returns 200. Docker Compose condition: service_healthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use uvicorn; disable access log (structured logs handle request traces)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
