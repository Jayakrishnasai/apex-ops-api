# Apex Operations API

A production-grade REST API built with **FastAPI + PostgreSQL**, containerised with Docker, and delivered with a full CI/CD pipeline.

**Candidate:** Jayakrishnasai ([koppolijayakrishnasai@gmail.com](mailto:koppolijayakrishnasai@gmail.com))  
**Assessment:** Junior DevOps Engineer Assessment — Apex Operations  
**Date:** November 2026

---

## Quick Start (< 5 minutes)

### Prerequisites
- Docker Desktop ≥ 24 (includes Compose v2)
- Python 3.12+ (for running tests locally)
- Git
- `curl` (for health checks)

### 1 — Clone and configure

```bash
git clone <repo-url> apex-ops-api
cd apex-ops-api

cp .env.example .env
# Edit .env and set a strong DB_PASSWORD
```

### 2 — Run the full stack

```bash
docker compose up --build -d
```

This starts:
| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Interactive docs | http://localhost:8000/docs |
| Prometheus metrics | http://localhost:8000/metrics |
| Prometheus UI | http://localhost:9090 |

### 3 — Verify it works

```bash
# Liveness
curl http://localhost:8000/health

# Readiness (checks DB)
curl http://localhost:8000/ready

# Create an item
curl -s -X POST http://localhost:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Deploy pipeline","description":"Set up CD","status":"active"}' | python -m json.tool

# List items
curl http://localhost:8000/items/
```

---

## Running Tests Locally

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run main test suite (14 checks — all pass)
pytest tests/ -k "not intentional" -v

# Run the intentional failure test (demonstrates CI blocking)
pytest tests/test_intentional_failure.py -v

# Run with coverage
pytest tests/ -k "not intentional" --cov=app --cov-report=term-missing
```

---

## Deployment

```bash
# Deploy (builds image tagged with git SHA, waits for health check)
bash scripts/deploy.sh

# Deploy a specific version
bash scripts/deploy.sh v1.2.0

# Rollback to previous version
bash scripts/rollback.sh

# Rollback to a specific tag
bash scripts/rollback.sh abc1234
```

---

## Project Structure

```
apex-ops-api/
├── app/
│   ├── config.py          # Pydantic-settings (env-var driven)
│   ├── database.py        # SQLAlchemy engine + session factory
│   ├── logger.py          # Structured JSON logging
│   ├── main.py            # FastAPI app + lifespan + Prometheus
│   ├── models.py          # ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   └── routes/
│       ├── health.py      # /health, /ready
│       └── items.py       # /items CRUD
├── tests/
│   ├── conftest.py        # SQLite fixtures, TestClient
│   ├── test_health.py     # Checks 1-6
│   ├── test_items.py      # Checks 7-14
│   └── test_intentional_failure.py  # CI blocking demo
├── monitoring/
│   ├── prometheus.yml     # Scrape config
│   └── alert_rules.yml    # 4 alert rules
├── scripts/
│   ├── deploy.sh          # Build → tag → health gate → deploy
│   └── rollback.sh        # Restore previous versioned image
├── .github/workflows/
│   └── ci.yml             # Lint → Test → Build (blocked on failure)
├── Dockerfile             # Multi-stage, non-root (UID 1001)
├── docker-compose.yml     # App + DB + Prometheus + named volumes
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .env.example
├── RUNBOOK.md
├── DECISION_MEMO.md
└── AI_DISCLOSURE.md
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (checks DB) |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | Interactive Swagger UI |
| POST | `/items/` | Create item |
| GET | `/items/` | List items (paginated) |
| GET | `/items/{id}` | Get item by ID |
| PUT | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Delete item |

---

## CI/CD Pipeline

```
Push to main/PR
      ↓
  [Lint] ruff check + ruff format
      ↓ (blocks if any lint error)
  [Test] 14 checks + intentional failure demo
      ↓ (blocks build if any real test fails)
  [Build] Docker multi-stage build + Trivy vulnerability scan
```

---

## Security Highlights

- **No hard-coded secrets** — all credentials via environment variables
- **Non-root container** — `appuser` UID 1001, `no-new-privileges`
- **Multi-stage build** — no build tools (gcc, pip) in the runtime image
- **Image scanning** — Trivy runs in CI on every build
- **`.env` git-ignored** — `.env.example` is the only committed template
- See [DECISION_MEMO.md](./DECISION_MEMO.md) for full security notes

---

## Assessment Checklist

- [x] Dockerfile with health/readiness endpoints and non-root execution
- [x] CI workflow: lint, test, build, block on failure
- [x] Docker Compose with app + PostgreSQL + persistent volumes
- [x] Safe release & rollback (versioned images, `rollback.sh`)
- [x] Observability: structured logs, health checks, Prometheus metrics, alert rules
- [x] Security: secrets handling, least privilege, image scanning, cloud path
- [x] ≥ 6 automated checks (14 total) + 1 intentional failure
- [x] Runbook, decision memo, AI disclosure
