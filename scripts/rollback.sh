#!/usr/bin/env bash
# =============================================================================
# rollback.sh — Restore the previous versioned image
#
# Usage:
#   bash scripts/rollback.sh [TARGET_TAG]
#
# Arguments:
#   TARGET_TAG  Optional image tag to roll back to.
#               If omitted, reads from .last_deployed_tag.
#
# Strategy:
#   Versioned image tags (git SHAs) are always kept locally.
#   Rolling back means switching IMAGE_TAG and restarting the app container.
#   Database volumes are preserved — no data is lost.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

ROLLBACK_FILE=".last_deployed_tag"

echo "=========================================="
echo " Apex Operations API — Rollback"
echo " $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=========================================="

# ── Determine rollback target ─────────────────────────────────────────────────
if [ -n "${1:-}" ]; then
  TARGET_TAG="$1"
  echo "Rolling back to explicitly provided tag: $TARGET_TAG"
elif [ -f "$ROLLBACK_FILE" ]; then
  TARGET_TAG=$(cat "$ROLLBACK_FILE")
  echo "Rolling back to last recorded tag: $TARGET_TAG"
else
  echo "ERROR: No rollback target. Provide a tag or run deploy.sh first."
  exit 1
fi

# ── Verify the image exists locally ──────────────────────────────────────────
if ! docker image inspect "apex-ops-api:$TARGET_TAG" &>/dev/null; then
  echo "ERROR: Image apex-ops-api:$TARGET_TAG not found locally."
  echo "       Pull it first: docker pull apex-ops-api:$TARGET_TAG"
  exit 1
fi

# ── Stop current app container ────────────────────────────────────────────────
echo "[1/3] Stopping current app container ..."
docker compose stop app

# ── Switch IMAGE_TAG and restart ──────────────────────────────────────────────
echo "[2/3] Starting rollback target: apex-ops-api:$TARGET_TAG ..."
export IMAGE_TAG="$TARGET_TAG"
docker compose up -d --no-deps app

# ── Health gate ───────────────────────────────────────────────────────────────
echo "[3/3] Verifying rollback health ..."
sleep 10
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$STATUS" == "200" ]; then
  echo "✓ Rollback successful. Running version: $TARGET_TAG"
else
  echo "ERROR: Rollback health check failed (HTTP $STATUS). Manual intervention required."
  echo "       docker compose logs app"
  exit 1
fi
