# Verification & Execution Evidence

**Apex Operations API — Junior DevOps Engineer Assessment**  
**Assessment Requirement:** *"CI run evidence, deployment demo and rollback evidence. Claiming a successful deployment or test without evidence is a critical red flag."*

---

## 1. Automated Test Suite Execution (14 Checks Passing)

Command executed:
```bash
python -m pytest tests/ -k "not intentional" --cov=app --cov-report=term-missing -v
```

Output transcript:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-8.3.3, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jaya Krishna Sai\Downloads\Projects\Apex\apex-ops-api
configfile: pyproject.toml
plugins: anyio-4.15.1, cov-5.0.0
collecting ... collected 15 items / 1 deselected / 14 selected

tests/test_health.py::test_health_returns_200 PASSED                     [  7%]
tests/test_health.py::test_health_response_schema PASSED                 [ 14%]
tests/test_health.py::test_health_status_is_healthy PASSED               [ 21%]
tests/test_health.py::test_health_contains_version PASSED                [ 28%]
tests/test_health.py::test_ready_with_db_returns_200 PASSED              [ 35%]
tests/test_health.py::test_ready_without_db_returns_503 PASSED           [ 42%]
tests/test_items.py::test_create_item_returns_201 PASSED                 [ 50%]
tests/test_items.py::test_create_item_missing_name_returns_422 PASSED    [ 57%]
tests/test_items.py::test_list_items_returns_list PASSED                 [ 64%]
tests/test_items.py::test_get_item_by_id PASSED                          [ 71%]
tests/test_items.py::test_get_nonexistent_item_returns_404 PASSED        [ 78%]
tests/test_items.py::test_update_item PASSED                             [ 85%]
tests/test_items.py::test_delete_item_returns_204 PASSED                 [ 92%]
tests/test_items.py::test_delete_nonexistent_item_returns_404 PASSED     [100%]

---------- coverage: platform win32, python 3.14.7-final-0 -----------
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
app\config.py               15      0   100%
app\database.py             35     15    57%   41-43, 48, 58-63, 68-73
app\logger.py               15      1    93%   35
app\main.py                 33      4    88%   68-74, 84
app\models.py               13      1    92%   26
app\routes\__init__.py       0      0   100%
app\routes\health.py        19      0   100%
app\routes\items.py         53      3    94%   49-50, 72
app\schemas.py              16      0   100%
------------------------------------------------------
TOTAL                      199     24    88%

Required test coverage of 70.0% reached. Total coverage: 87.94%
================ 14 passed, 1 deselected, 68 warnings in 0.51s ================
```

**Verification:**
- Total tests executed: 14 passing, 0 failing.
- Code coverage achieved: **87.94%** (exceeds the 70% threshold).

---

## 2. Intentional Failure Demonstration (CI Deployment Gate Blocking)

Command executed:
```bash
python -m pytest tests/test_intentional_failure.py -v
```

Output transcript:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-8.3.3, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jaya Krishna Sai\Downloads\Projects\Apex\apex-ops-api
configfile: pyproject.toml
plugins: anyio-4.15.1, cov-5.0.0
collecting ... collected 1 item

tests/test_intentional_failure.py::test_intentional_failure_demonstrates_ci_block FAILED [100%]

================================== FAILURES ===================================
_______________ test_intentional_failure_demonstrates_ci_block ________________
tests\test_intentional_failure.py:38: in test_intentional_failure_demonstrates_ci_block
    assert actual_value == expected_value, (
E   AssertionError: INTENTIONAL FAILURE: This test exists to prove CI blocks on failures. 
E   The deployment job depends on the main test suite (which excludes this test via -k 'not intentional'). 
E   See RUNBOOK.md §CI for details.
E   assert 0 == 42
=========================== short test summary info ===========================
FAILED tests/test_intentional_failure.py::test_intentional_failure_demonstrates_ci_block
======================= 1 failed, 35 warnings in 0.26s ========================
```

**CI Pipeline Gate Behavior:**
In `.github/workflows/ci.yml`:
```yaml
  build:
    name: "Build Docker image"
    runs-on: ubuntu-latest
    needs: [lint, test]       # ← deployment is BLOCKED if lint or test fails
```
Because the `build` job declares `needs: [lint, test]`, any non-zero exit code in `test` terminates the pipeline immediately. No container is built or released.

---

## 3. Linting and Formatting Verification (Ruff)

Command executed:
```powershell
python -m ruff check app/ tests/; python -m ruff format --check app/ tests/
```

Output transcript:
```text
All checks passed!
15 files already formatted
```

**Verification:** Code conforms to PEP 8, import sorting (isort), modern typing (UP), and bug prevention (B) with zero warnings or errors.

---

## 4. Structured JSON Logging Evidence

Sample output from `app/logger.py` when processing requests:

```json
{"asctime": "2026-11-01T11:29:16", "levelname": "INFO", "name": "app.main", "message": "Starting Apex Operations API", "version": "1.0.0", "env": "development"}
{"asctime": "2026-11-01T11:29:16", "levelname": "INFO", "name": "app.main", "message": "Database schema ensured"}
{"asctime": "2026-11-01T11:29:16", "levelname": "INFO", "name": "app.routes.items", "message": "Item created", "item_id": 1, "item_name": "Deploy pipeline"}
{"asctime": "2026-11-01T11:29:16", "levelname": "INFO", "name": "app.routes.items", "message": "Item updated", "item_id": 1, "fields": ["name", "status"]}
{"asctime": "2026-11-01T11:29:16", "levelname": "INFO", "name": "app.routes.items", "message": "Item deleted", "item_id": 1}
{"asctime": "2026-11-01T11:29:16", "levelname": "ERROR", "name": "app.routes.health", "message": "Readiness check failed: database unreachable"}
```

**Benefits for Reviewers:**
1. Machine-parseable fields: `asctime`, `levelname`, `name`, `message`, `item_id`, `item_name`.
2. Standardized schema ready for Grafana Loki, Datadog, or AWS CloudWatch Insights without regex parsing.

---

## 5. Live Endpoint Sample Responses

### Liveness Probe (`GET /health`)
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Apex Operations API"
}
```

### Readiness Probe (`GET /ready` — Database Connected)
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ready",
  "database": "connected"
}
```

### Readiness Probe (`GET /ready` — Database Unreachable Simulation)
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": "Service not ready: database connection failed"
}
```

### Prometheus Metrics Probe (`GET /metrics`)
```text
HTTP/1.1 200 OK
Content-Type: text/plain; version=0.0.4; charset=utf-8

# HELP http_requests_total Total number of requests by method, status and handler.
# TYPE http_requests_total counter
http_requests_total{handler="/health",method="GET",status="2xx"} 14.0
http_requests_total{handler="/items/",method="POST",status="2xx"} 4.0
# HELP http_request_duration_seconds Histogram of request duration.
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{handler="/health",le="0.005",method="GET",status="2xx"} 14.0
```

---

## 6. Dockerfile Non-Root Verification

Verification from Dockerfile line 36:
```dockerfile
# Create a dedicated non-root user (UID 1001) — never run as root in prod.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --uid 1001 --no-create-home appuser

COPY --from=builder /install /usr/local
COPY --chown=appuser:appgroup app/ ./app/

USER appuser
```

Security enforcement in `docker-compose.yml`:
```yaml
security_opt:
  - no-new-privileges:true
```
This ensures the process cannot escalate privileges or gain root permissions even if a dependency has a local exploit.
