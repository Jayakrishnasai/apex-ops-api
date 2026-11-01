# System Architecture & CI/CD Pipeline

**Apex Operations API — Architecture & Flow Specifications**

---

## 1. System Overview & Runtime Topology

The local runtime stack is orchestrated via Docker Compose, isolated inside a private bridge network (`apex_net`).

```mermaid
graph TB
    subgraph Host["Host Environment (Developer / Reviewer)"]
        Browser["Web Browser / Swagger UI<br/>http://localhost:8000/docs"]
        PrometheusUI["Prometheus Dashboard<br/>http://localhost:9090"]
        Client["HTTP Client / curl / pytest"]
    end

    subgraph DockerNet["Docker Bridge Network (apex_net)"]
        subgraph AppContainer["App Container: apex-ops-api (UID 1001)"]
            FastAPI["FastAPI 0.115"]
            Liveness["/health (Liveness)"]
            Readiness["/ready (Readiness)"]
            Metrics["/metrics (Prometheus)"]
            JSONLogs["Structured JSON Logger<br/>(stdout)"]
            CRUD["/items (CRUD Routes)"]
        end

        subgraph DBContainer["PostgreSQL 16 Container"]
            PG["PostgreSQL Daemon<br/>Internal Port 5432"]
            PGHealth["pg_isready Healthcheck"]
        end

        subgraph PromContainer["Prometheus v2.54.1 Container"]
            PromServer["Prometheus Engine"]
            Alerts["Alert Rules Evaluation"]
        end
    end

    subgraph Persistence["Host Volume Storage"]
        PGVolume[("postgres_data volume")]
        PromVolume[("prometheus_data volume")]
    end

    Client -->|HTTP 8000| FastAPI
    Browser -->|HTTP 8000| FastAPI
    PrometheusUI -->|HTTP 9090| PromServer
    FastAPI -->|TCP 5432| PG
    PromServer -->|Scrapes /metrics| Metrics
    PG -->|Persists data| PGVolume
    PromServer -->|Persists TSDB| PromVolume
```

---

## 2. CI/CD Pipeline Flow & Deployment Gate

The GitHub Actions workflow enforces test-driven delivery and vulnerability scanning prior to any container build.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer / Git Push
    participant GHA as GitHub Actions
    participant Lint as Job 1: Lint (Ruff)
    participant Test as Job 2: Test (Pytest)
    participant Build as Job 3: Build & Scan (Docker + Trivy)
    participant Compose as Docker Compose Runtime

    Dev->>GHA: Push commit / Open PR
    activate GHA

    GHA->>Lint: Run Ruff Check & Format Check
    activate Lint
    alt Lint Violation
        Lint-->>GHA: Fail (Exit 1)
        GHA-->>Dev: Pipeline BLOCKED: Style / Syntax Error
    else Lint Passed
        Lint-->>GHA: Success
    end
    deactivate Lint

    GHA->>Test: Run Main Test Suite (14 Checks)
    activate Test
    Note over Test: Excludes intentional failure test via -k "not intentional"
    alt Any Real Test Fails
        Test-->>GHA: Fail (Exit 1)
        GHA-->>Dev: Pipeline BLOCKED: Regression / Broken Contract
    else 14 Checks Pass (88% Coverage)
        Test-->>GHA: Success
        Test->>Test: Run intentional failure demo (logs FAILED evidence)
    end
    deactivate Test

    GHA->>Build: Build Multi-stage Image (Non-root UID 1001)
    activate Build
    Build->>Build: Trivy Security Vulnerability Scan (CVEs)
    Build-->>GHA: Success: Image tagged with git SHA
    deactivate Build

    GHA->>Compose: Deploy via deploy.sh / deploy.ps1
    activate Compose
    Compose->>Compose: Rolling update of app container
    Compose->>Compose: Poll /health until HTTP 200
    Compose-->>Dev: Deployment Healthy & Verified
    deactivate Compose
    deactivate GHA
```

---

## 3. Safe Release & Rollback Strategy

```mermaid
stateDiagram-v2
    [*] --> Idle: App running v1 (image: apex-ops-api:v1)
    Idle --> Deploying: Execute deploy.sh v2
    Deploying --> BuildV2: Build & Tag image v2
    BuildV2 --> RecordTag: Save v1 tag to .last_deployed_tag
    RecordTag --> RollingRestart: Restart app container with image:v2
    RollingRestart --> HealthCheck: Poll /health (15 attempts x 5s)
    
    HealthCheck --> Verified: HTTP 200 Received
    Verified --> Idle: Release successful (v2 active)

    HealthCheck --> Failed: Timeout or HTTP 5xx
    Failed --> AutoRollback: Automatically execute rollback.sh
    AutoRollback --> SwitchTag: Read previous tag from .last_deployed_tag
    SwitchTag --> RestartV1: Restart container with image:v1
    RestartV1 --> HealthCheckV1: Poll /health on v1
    HealthCheckV1 --> Restored: Service Restored (Zero Data Loss)
    Restored --> Idle
```

---

## 4. Key Architectural Attributes

| Attribute | Implementation | Production Rationale |
|---|---|---|
| **Separation of Probes** | `/health` (liveness: no external calls) vs `/ready` (readiness: DB probe) | Prevents cascading restart loops if DB is transiently slow or rebooting |
| **Least Privilege Container** | Custom UID 1001 (`appuser`), non-root, `no-new-privileges: true` | Eliminates container breakout and host compromise vectors |
| **Clean Multi-Stage Build** | Stage 1 `builder` (gcc, headers) → Stage 2 `runtime` (slim Python) | Shrinks attack surface by discarding compilers and headers |
| **Structured Observability** | JSON logs on stdout + Prometheus `/metrics` endpoint | Seamless ingestion into Loki/Datadog/CloudWatch and Prometheus/Grafana |
| **Storage Isolation** | Named volumes `postgres_data` and `prometheus_data` | Preserves transactional database state across container updates and rollbacks |
