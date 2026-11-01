# Runbook — Apex Operations API

> **Audience:** On-call engineers  
> **Last updated:** 2026-11-01

---

## 1. Deploy

```bash
# Standard deploy (auto-tags with git SHA)
bash scripts/deploy.sh

# Deploy a specific tag
bash scripts/deploy.sh v1.2.3
```

**What the script does:**
1. Builds `apex-ops-api:<sha>` and re-tags it as `latest`
2. Saves the previous tag to `.last_deployed_tag` for rollback
3. Runs `docker compose up -d --no-deps app` (rolling restart, DB untouched)
4. Polls `GET /health` every 5 s for up to 75 s
5. Auto-triggers `rollback.sh` if health never passes

**Expected output:**
```
✓ Health check passed (HTTP 200) after 10s
✓ Deployment complete.
  API: http://localhost:8000
```

---

## 2. Rollback

```bash
# Rollback to the previously deployed version
bash scripts/rollback.sh

# Rollback to a specific known-good version
bash scripts/rollback.sh abc1234
```

**Strategy:** Images are tagged with git SHAs and kept locally. Rolling back means restarting the app container with the old image tag. The database volume is never touched.

**Rollback time target:** < 60 seconds from command to healthy.

---

## 3. Incident Response

### Step 1 — Detect

```bash
# Is the API up?
curl http://localhost:8000/health

# Is the database connected?
curl http://localhost:8000/ready

# Check live container status
docker compose ps

# Tail structured JSON logs
docker compose logs -f app | python -m json.tool
```

### Step 2 — Triage

| Symptom | Likely cause | Action |
|---|---|---|
| `/health` returns 503 | App crashed | `docker compose restart app` |
| `/ready` returns 503 | DB unreachable | `docker compose restart db` |
| HTTP 500 on item routes | App bug / bad data | Check logs; rollback if recent deploy |
| App container keeps restarting | OOM or bad config | `docker compose logs app --tail=50` |
| Slow responses | DB contention or memory pressure | Check Prometheus p95 latency alert |

### Step 3 — Remediate

```bash
# Restart app only (no data loss)
docker compose restart app

# View last 100 log lines
docker compose logs app --tail=100

# Connect to database for manual inspection
docker compose exec db psql -U apex -d apex_db

# Full stack teardown (data preserved via named volumes)
docker compose down
docker compose up -d
```

### Step 4 — Rollback if needed

```bash
bash scripts/rollback.sh
```

### Step 5 — Post-incident

1. Record the incident timeline, root cause, and resolution
2. Open a ticket with log excerpts and screenshots as evidence
3. Add a regression test if a code bug was the cause
4. Update alert thresholds if the alert fired too late/early

---

## 4. Failure Investigation Demo

**Scenario:** simulate a 503 readiness failure.

```bash
# Stop the database container
docker compose stop db

# Readiness probe should now return 503
curl -v http://localhost:8000/ready
# Expected: HTTP/1.1 503 Service Unavailable

# Logs will show:
# {"levelname": "ERROR", "name": "app.routes.health",
#  "message": "Readiness check failed: database unreachable"}

# Restore the database
docker compose start db

# Verify recovery (may take ~10s)
curl http://localhost:8000/ready
# Expected: {"status": "ready", "database": "connected"}
```

---

## 5. Troubleshooting

| Problem | Command |
|---|---|
| Port 8000 already in use | `lsof -i :8000` → kill or change port |
| `.env` not found | `cp .env.example .env` and fill in `DB_PASSWORD` |
| DB volume corrupted | `docker compose down -v && docker compose up -d` (**data loss!**) |
| Image build fails | `docker build --no-cache .` |
| Tests fail locally | `pip install -r requirements-dev.txt` |
| ruff lint errors | `ruff check --fix app/ tests/` |

---

## 6. Health Endpoints

| Endpoint | Purpose | Expected response |
|---|---|---|
| `GET /health` | Liveness | `200 {"status":"healthy"}` |
| `GET /ready` | Readiness | `200 {"status":"ready","database":"connected"}` |
| `GET /metrics` | Prometheus scrape | `200 text/plain` |

---

## 7. Key Files

| File | Purpose |
|---|---|
| `.env` | Runtime secrets (git-ignored) |
| `.last_deployed_tag` | Previous image tag for rollback |
| `docker-compose.yml` | Stack definition |
| `monitoring/alert_rules.yml` | Prometheus alert thresholds |
