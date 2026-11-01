#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Build, tag and start the Apex Operations API stack
#
# Usage:
#   bash scripts/deploy.sh [VERSION]
#
# Arguments:
#   VERSION  Optional image tag (default: git short SHA)
#
# Requirements:
#   - Docker & Docker Compose
#   - .env file with DB_PASSWORD set (see .env.example)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# ── Determine image tag ───────────────────────────────────────────────────────
VERSION="${1:-$(git rev-parse --short HEAD 2>/dev/null || echo "local")}"
export IMAGE_TAG="$VERSION"

echo "=========================================="
echo " Apex Operations API — Deploy"
echo " Version: $IMAGE_TAG"
echo " $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=========================================="

# ── Pre-flight checks ─────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo "ERROR: .env file not found. Copy .env.example and fill in secrets."
  exit 1
fi

if ! docker info &>/dev/null; then
  echo "ERROR: Docker daemon is not running."
  exit 1
fi

# ── Build image ───────────────────────────────────────────────────────────────
echo ""
echo "[1/4] Building Docker image apex-ops-api:$IMAGE_TAG ..."
docker build \
  --target runtime \
  --tag "apex-ops-api:$IMAGE_TAG" \
  --tag "apex-ops-api:latest" \
  .

echo "[1/4] Build complete."

# ── Record the previous tag for potential rollback ────────────────────────────
ROLLBACK_FILE=".last_deployed_tag"
if [ -f "$ROLLBACK_FILE" ]; then
  PREVIOUS_TAG=$(cat "$ROLLBACK_FILE")
  echo "[2/4] Previous tag recorded for rollback: $PREVIOUS_TAG"
fi
echo "$IMAGE_TAG" > "$ROLLBACK_FILE"

# ── Pull dependent images ─────────────────────────────────────────────────────
echo "[2/4] Pulling dependency images (postgres, prometheus) ..."
docker compose pull db prometheus 2>/dev/null || true

# ── Start / update stack ──────────────────────────────────────────────────────
echo "[3/4] Starting stack (zero-downtime rolling update for app service) ..."
docker compose up -d --no-deps --build app
docker compose up -d db prometheus

# ── Health gate ───────────────────────────────────────────────────────────────
echo "[4/4] Waiting for health check to pass ..."
MAX_RETRIES=15
RETRY_INTERVAL=5
for i in $(seq 1 $MAX_RETRIES); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
  if [ "$STATUS" == "200" ]; then
    echo "✓ Health check passed (HTTP $STATUS) after $((i * RETRY_INTERVAL))s"
    break
  fi
  echo "  Attempt $i/$MAX_RETRIES — got HTTP $STATUS, retrying in ${RETRY_INTERVAL}s ..."
  sleep "$RETRY_INTERVAL"
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "ERROR: Health check failed after $((MAX_RETRIES * RETRY_INTERVAL))s. Triggering rollback ..."
    bash "$SCRIPT_DIR/rollback.sh"
    exit 1
  fi
done

echo ""
echo "✓ Deployment complete."
echo "  API:        http://localhost:8000"
echo "  Docs:       http://localhost:8000/docs"
echo "  Metrics:    http://localhost:8000/metrics"
echo "  Prometheus: http://localhost:9090"
