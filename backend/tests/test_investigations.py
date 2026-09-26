import pytest
import uuid
from unittest.mock import patch

@pytest.mark.asyncio
async def test_create_and_get_investigation(client):
    # Register & Login
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "inv-test@clustermind.io",
        "password": "SecurePassword123!"
    })
    token_resp = await client.post("/api/v1/auth/login", json={
        "email": "inv-test@clustermind.io",
        "password": "SecurePassword123!"
    })
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch seed cluster
    clusters_resp = await client.get("/api/v1/clusters", headers=headers)
    assert clusters_resp.status_code == 200
    clusters = clusters_resp.json()
    assert len(clusters) > 0
    cluster_id = clusters[0]["id"]

    # Post investigation
    inv_resp = await client.post("/api/v1/investigations", headers=headers, json={
        "cluster_id": cluster_id,
        "namespace": "default"
    })
    assert inv_resp.status_code == 202
    inv_data = inv_resp.json()
    assert inv_data["status"] == "running"

    # Fetch investigation details
    inv_id = inv_data["id"]
    get_resp = await client.get(f"/api/v1/investigations/{inv_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == inv_id
