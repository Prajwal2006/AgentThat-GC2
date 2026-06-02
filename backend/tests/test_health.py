from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "agentthat-backend"}


def test_tenant_health_returns_tenant_id() -> None:
    response = client.get("/v1/tenants/acme/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "tenantId": "acme"}


def test_tenant_health_rejects_blank_id() -> None:
    response = client.get("/v1/tenants/%20%20/health")
    assert response.status_code == 400
    assert response.json()["detail"] == "tenant_id is required"


def test_ai_status_reports_fallback_when_not_configured() -> None:
    response = client.get("/v1/ai/status")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "azure_openai"
    assert body["mode"] in {"live", "deterministic-fallback"}


def test_platform_overview_returns_dashboard_data() -> None:
    response = client.get("/v1/platform/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["dashboardStats"]
    assert body["recentActivity"]
    assert body["agents"]


def test_prompt_improvement_has_enterprise_controls() -> None:
    response = client.post(
        "/v1/ai/improve-prompt",
        json={"prompt": "Create a sales agent."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] in {"azure_openai", "deterministic"}
    assert "human-in-the-loop" in body["improved_prompt"]


def test_solution_generation_returns_workflow_architecture() -> None:
    response = client.post(
        "/v1/solutions/generate",
        json={
            "name": "Support Triage",
            "requirement": "Classify support tickets, search docs, draft replies, and escalate urgent issues.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Support Triage"
    assert body["agents"]
    assert body["workflow"]
    assert body["governance"]


def test_workflow_lifecycle_create_and_run() -> None:
    create_response = client.post(
        "/v1/workflows",
        json={
            "name": "Revenue Expansion Flow",
            "description": "Identify target accounts, draft outreach, and route approvals.",
            "agents": 3,
        },
    )
    assert create_response.status_code == 200
    workflow = create_response.json()
    assert workflow["status"] == "testing"

    run_response = client.post(
        f"/v1/workflows/{workflow['id']}/control",
        json={"action": "run"},
    )
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "active"


def test_settings_profile_round_trip() -> None:
    initial = client.get("/v1/settings/profile")
    assert initial.status_code == 200
    body = initial.json()
    update = client.put(
        "/v1/settings/profile",
        json={
            "full_name": body["full_name"],
            "email": "founder@agentthat.ai",
            "role": body["role"],
        },
    )
    assert update.status_code == 200
    assert update.json()["email"] == "founder@agentthat.ai"
