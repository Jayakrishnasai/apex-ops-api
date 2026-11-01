# Live Demo Walkthrough Guide

**Candidate:** Jayakrishnasai ([koppolijayakrishnasai@gmail.com](mailto:koppolijayakrishnasai@gmail.com))  
**Purpose:** Step-by-step instructions and talking points for the 30–45 minute technical review meeting.

---

## ⏱️ 5-Minute Live Demo Structure

```
[Minute 0-1]  GitHub Repository & Passing CI Actions Pipeline
[Minute 1-2]  Automated Tests (14 checks, 88% coverage) & Intentional Failure Block
[Minute 2-4]  Live API Execution, Endpoints (/docs, /health, /ready, /metrics) & JSON Logs
[Minute 4-5]  Failure Investigation Simulation & Zero-Downtime Rollback Demo
```

---

## Step 1: Show GitHub Repository & CI Pipeline

### In your browser:
1. Open: [https://github.com/Jayakrishnasai/apex-ops-api](https://github.com/Jayakrishnasai/apex-ops-api)
2. Open Actions tab: [https://github.com/Jayakrishnasai/apex-ops-api/actions](https://github.com/Jayakrishnasai/apex-ops-api/actions)

### What to say:
> *"Here is the repository and our GitHub Actions CI pipeline. Every commit automatically triggers three sequential jobs: Ruff linting and formatting check, pytest test execution with coverage reporting, and a Docker multi-stage build that includes a Trivy vulnerability scan. As you can see, our pipeline is green."*

---

## Step 2: Show Automated Tests & CI Deployment Gate

### In your terminal:
```powershell
cd "c:\Users\Jaya Krishna Sai\Downloads\Projects\Apex\apex-ops-api"

# 1. Run the passing test suite
python -m pytest tests/ -k "not intentional" --cov=app --cov-report=term-missing -v
```

### What to say:
> *"We have 14 automated checks testing liveness, readiness, schema validation, and full CRUD operations with 88% test coverage, surpassing the 70% requirement."*

### Next, demonstrate the intentional failure:
```powershell
python -m pytest tests/test_intentional_failure.py -v
```

### What to say:
> *"To fulfill the requirement for demonstrating CI blocking on failure, we included `test_intentional_failure.py`. In GitHub Actions, the build job explicitly declares `needs: [lint, test]`, so any failing test immediately blocks container building and deployment."*

---

## Step 3: Run the API & Show Observability

### Start the application:
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Endpoints to open in browser:
1. **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - Click `POST /items/` $\to$ **Try it out** $\to$ Execute.
2. **Liveness Probe:** [http://localhost:8000/health](http://localhost:8000/health)
   - Output: `{"status": "healthy", "version": "1.0.0", "service": "Apex Operations API"}`
3. **Readiness Probe:** [http://localhost:8000/ready](http://localhost:8000/ready)
   - Output: `{"status": "ready", "database": "connected"}`
4. **Prometheus Metrics:** [http://localhost:8000/metrics](http://localhost:8000/metrics)
   - Shows live HTTP request counters and latency histograms.

### What to say:
> *"Notice the architectural separation of concerns: `/health` is a pure liveness probe with zero external calls to prevent cascading restart loops. `/ready` checks database reachability. All logs in the terminal are emitted as structured JSON objects for seamless ingestion into Loki or CloudWatch."*

---

## Step 4: Failure Investigation Demo

### What to demonstrate:
1. Stop the database container or simulate a connection cut:
   - Request to `/ready` immediately returns `503 Service Unavailable`.
   - Structured error log emitted: `"Readiness check failed: database unreachable"`.
2. Restore database:
   - Request to `/ready` returns `200 OK` with `{"status": "ready", "database": "connected"}`.

### What to say:
> *"This demonstrates our incident triage scenario from RUNBOOK.md §4. When the database becomes unreachable, `/ready` immediately returns 503, preventing traffic routing while `/health` stays alive so the orchestrator doesn't endlessly crash-loop."*

---

## Step 5: Rollback Mechanism

### In your terminal:
```bash
# Linux / macOS
bash scripts/rollback.sh

# Windows PowerShell
.\scripts\rollback.ps1
```

### What to say:
> *"For safe release and rollback, each deploy builds an image tagged with the git commit SHA and updates `.last_deployed_tag`. If a release fails health checks or an incident occurs, running `rollback.sh` points the container back to the previous known-good tag with a rolling restart. Because PostgreSQL uses a named persistent volume (`postgres_data`), rollback causes zero transactional data loss."*

---

## 🎯 Defense Q&A Sheet

| Question | Strong Answer |
|---|---|
| **Why FastAPI over Flask?** | *"FastAPI gives us automatic OpenAPI docs at `/docs`, type safety with Pydantic v2, and native async support without external plugins."* |
| **Why not run container as root?** | *"Running containers as root is a major security hazard. The Dockerfile creates a dedicated user `appuser` with UID 1001. In `docker-compose.yml`, we also enforce `security_opt: [no-new-privileges:true]`."* |
| **How are secrets managed?** | *"Zero secrets are committed to Git. `.env` is git-ignored, `.env.example` provides a template, and values are injected at runtime via Pydantic settings."* |
| **What would you improve with more time?** | *"I would add Alembic database migrations, JWT authentication, and deploy to GCP Cloud Run for scale-to-zero serverless cost efficiency."* |
