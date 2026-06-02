# AgentThat Frontend

Next.js 16 + TypeScript + Tailwind UI for AgentThat core modules:

- Dashboard
- Builder (manual + AI generation)
- Workflows
- Marketplace
- Analytics
- Learning
- Settings

## Local Setup

1. Install dependencies:

```bash
npm install
```

2. Configure environment:

```bash
cp .env.example .env
```

3. Ensure [frontend/.env](.env) has backend URL:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

4. Start dev server:

```bash
npm run dev
```

## Backend Integration

The frontend is fully wired to backend API endpoints in [frontend/src/lib/api.ts](src/lib/api.ts):

- `GET /v1/platform/overview`
- `POST /v1/agents`
- `POST /v1/ai/improve-prompt`
- `POST /v1/solutions/generate`
- `POST /v1/solutions/deploy`
- `GET/POST /v1/workflows`
- `POST /v1/workflows/{id}/control`
- `GET /v1/marketplace`
- `POST /v1/marketplace/{id}/install`
- `GET /v1/learning`
- `POST /v1/learning/courses/{id}/start`
- `POST /v1/learning/courses/{id}/complete`
- `GET/PUT /v1/settings/profile`
- `GET/PUT /v1/settings/notifications`
- `GET/POST /v1/team/members`
- `GET /v1/ai/status`

If backend is unavailable, pages keep working with local fallback data for a resilient UX.
