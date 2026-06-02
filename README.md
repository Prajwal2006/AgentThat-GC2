# AgentThat

**Tagline:** Build. Share. Adopt. Scale.

AgentThat is an enterprise-grade multi-tenant SaaS platform that helps non-technical employees build, share, deploy, govern, and improve AI agents and multi-agent workflows.

## Repository Layout

- `docs/agentthat-foundation.md` — Phases 1–7 and 15 (PRD, architecture, DB, APIs, UX, stories, sprints, diagrams)
- `openapi/agentthat-api.yaml` — API contract baseline
- `backend/` — FastAPI reference service for health and tenant readiness
- `backend/tests/` — Targeted tests for the backend baseline
- `frontend/` — Next.js + React + TypeScript frontend baseline for core product modules
- `infra/terraform/` — Azure-first Terraform starter
- `infra/k8s/` — Kubernetes baseline deployment manifests
- `.github/workflows/ci.yml` — CI pipeline for backend checks

## Quickstart (Backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

## Quickstart (Frontend)

```bash
cd frontend
npm install
npm run dev
```

Optional production checks:

```bash
npm run lint
npm run build
npm run start
```

## Scope

This baseline provides production-oriented architecture artifacts plus runnable backend and frontend foundations that can be expanded into full module implementations for Copilot, Builder, Marketplace, LMS, and Observability.
