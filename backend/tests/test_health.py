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
