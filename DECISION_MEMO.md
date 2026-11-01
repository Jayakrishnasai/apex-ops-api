# Decision Memo — Apex Operations API

**Candidate:** Jayakrishnasai ([koppolijayakrishnasai@gmail.com](mailto:koppolijayakrishnasai@gmail.com))  
**Role:** Junior DevOps Engineer Assessment — Apex Operations  
**Date:** 2026-11-01

---

## 1. Assumptions

- The "Apex Operations API" is an internal tool (not public-facing) for tracking
  operational work items. A simple CRUD service is appropriate.
- Assessment runs fully local; no paid cloud resources are used.
- Synthetic data only — no real users, credentials, or production systems accessed.
- Python 3.12 / FastAPI is the primary language: chosen for rapid development,
  excellent async support, and first-class Pydantic validation.

---

## 2. Key Decisions & Trade-offs

### API Framework — FastAPI vs Flask vs Django
**Chose FastAPI.** FastAPI generates OpenAPI docs automatically (critical for
reviewability), has Pydantic v2 validation built-in, and ships with async support.
Flask would have been lighter but requires more manual wiring. Django is overkill
for a single-resource API.

### Database — PostgreSQL vs SQLite
**Production stack uses PostgreSQL.** It's the correct choice for a real-world
API (concurrent writers, JSONB, proper types). Tests use an in-memory **SQLite**
override via a conftest fixture so tests run without a running container.

### ORM — SQLAlchemy vs raw SQL
**Chose SQLAlchemy 2.0 (mapped_column API).** Provides type-safe models, easy
migration path to Alembic, and avoids SQL injection risk inherent in hand-crafted
queries. Trade-off: slightly more boilerplate than raw SQL.

### Migrations — Base.metadata.create_all vs Alembic
**Used `create_all` for this assessment.** In production I would use **Alembic**
for versioned, reviewable migrations that can be applied without downtime. For a
48-hour assessment with a fixed schema, `create_all` is acceptable.

### Logging — python-json-logger
Every log line is a JSON object. This means zero additional config for ingestion
into Loki, CloudWatch Logs, or Datadog — any aggregator that understands JSON can
parse it without a custom pipeline.

### Metrics — prometheus-fastapi-instrumentator
Auto-instruments every route with `http_requests_total`, `http_request_duration_seconds`,
and `http_requests_inprogress`. A more advanced setup would add custom business
metrics (e.g., `items_created_total`). Given the time box, standard HTTP metrics
are sufficient to populate the alert rules.

### Rollback strategy — versioned image tags
Images are tagged with the git short SHA at build time. Rollback is as simple as
`docker compose up -d` with `IMAGE_TAG=<previous_sha>`. Trade-off: requires
keeping old images on disk (acceptable for local; a registry + retention policy
handles this in production).

---

## 3. Security Decisions

| Decision | Rationale |
|---|---|
| Non-root user (UID 1001) | Even inside a container, running as root violates least-privilege |
| Multi-stage Dockerfile | Removes gcc, pip, and build headers from the runtime image |
| Secrets via env vars | 12-factor app principle; `.env` is git-ignored |
| `no-new-privileges` security_opt | Prevents privilege escalation via setuid binaries |
| Trivy scan in CI | Catches known CVEs in base image and Python deps before any build is used |
| `.env.example` as template | Reviewers can see required variables without seeing real values |

---

## 4. What I Would Improve With More Time

1. **Alembic migrations** — replace `create_all` with versioned migration files
2. **Authentication** — add JWT bearer token auth (OAuth2PasswordBearer)
3. **Rate limiting** — add `slowapi` middleware to prevent abuse
4. **End-to-end tests** — use `docker compose -f docker-compose.test.yml` with
   a real PostgreSQL for integration tests alongside the SQLite unit tests
5. **Secrets manager** — integrate AWS Secrets Manager or HashiCorp Vault
   instead of relying on a `.env` file
6. **Cloud hosting path** — deploy to **GCP Cloud Run** (serverless, pay-per-use,
   no idle cost): push image to Artifact Registry → deploy with `gcloud run deploy`
7. **Graceful shutdown** — add SIGTERM handling to drain in-flight requests
8. **CI publishing** — push signed images to GHCR with `cosign` on every merge to main

---

## 5. Cost-Aware Cloud Hosting Path

For a low-traffic internal tool, the most cost-efficient path is:

| Option | Est. monthly cost | Notes |
|---|---|---|
| GCP Cloud Run | ~$0–5 | Scale-to-zero; pay only per request |
| AWS ECS Fargate | ~$5–15 | Always-on minimum task |
| GCP GKE Autopilot | ~$15+ | Overkill for a single service |
| Self-hosted VPS | ~$5 | Requires manual patching and uptime management |

**Recommendation:** Cloud Run — zero idle cost, built-in HTTPS, connects to
Cloud SQL (PostgreSQL) via the Cloud SQL Auth Proxy, and deploys with a single
`gcloud run deploy` command.
