# AI Assistance Disclosure

**Candidate:** Jayakrishnasai ([koppolijayakrishnasai@gmail.com](mailto:koppolijayakrishnasai@gmail.com))  
**Assessment requirement:** "AI assistance is permitted but must be disclosed with specific uses."

---

## Tools Used

| Tool | Specific Uses |
|---|---|
| **Antigravity IDE (Gemini / Claude)** | Scaffolding, code generation, documentation writing |

## Specific Uses

### Code Generation
- Initial scaffolding of the FastAPI application structure
- SQLAlchemy model and schema boilerplate
- Prometheus alert rule YAML structure
- GitHub Actions workflow template

### Documentation
- README, RUNBOOK, and DECISION_MEMO drafting
- Docstring content for routes and modules

## What I Reviewed and Own

Every file generated was reviewed for:
- Correctness (logic, types, error handling)
- Security (no hard-coded secrets, non-root, least privilege)
- Alignment with assessment requirements

The architectural decisions — framework choice, rollback strategy, security
posture, observability approach — reflect my own engineering judgment as
documented in `DECISION_MEMO.md`.

I am prepared to explain any decision, any line of code, and any trade-off
during the live review session.
