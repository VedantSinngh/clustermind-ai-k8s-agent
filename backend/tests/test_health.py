import pytest

@pytest.mark.asyncio
async def test_healthz(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_livez(client):
    response = await client.get("/livez")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

@pytest.mark.asyncio
async def test_healthz_ready(client):
    response = await client.get("/healthz/ready")
    assert response.status_code in [200, 53]
    if response.status_code == 200:
        assert response.json()["database"] == "ok"
