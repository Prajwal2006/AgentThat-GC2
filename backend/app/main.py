from fastapi import FastAPI, HTTPException

app = FastAPI(title="AgentThat Backend", version="0.1.0")


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentthat-backend"}


@app.get("/v1/tenants/{tenant_id}/health")
def tenant_health(tenant_id: str) -> dict[str, str]:
    normalized = tenant_id.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    return {"status": "ok", "tenantId": normalized}
