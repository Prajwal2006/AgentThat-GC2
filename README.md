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
## Windows PowerShell:
## .\.venv\Scripts\Activate.ps1
## macOS/Linux:
## source .venv/bin/activate
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

## Environment Setup

1. Copy [backend/.env.example](backend/.env.example) to [backend/.env](backend/.env) and fill Azure OpenAI values:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`

2. Copy [frontend/.env.example](frontend/.env.example) to [frontend/.env](frontend/.env):
- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`

3. Start backend and frontend in separate terminals:

```bash
# terminal 1
cd backend
python -m uvicorn app.main:app --reload

# terminal 2
cd frontend
npm run dev
```

When Azure values are configured, the Builder page uses live Azure OpenAI for prompt improvement and solution generation. If values are missing, deterministic fallback logic keeps the app usable.

Optional production checks:

```bash
npm run lint
npm run build
npm run start
```

## Scope

This baseline provides production-oriented architecture artifacts plus runnable backend and frontend foundations that can be expanded into full module implementations for Copilot, Builder, Marketplace, LMS, and Observability.
