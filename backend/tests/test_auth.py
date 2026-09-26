import pytest

@pytest.mark.asyncio
async def test_register_and_login(client):
    # 1. Register User
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": "sre-test@clustermind.io",
        "password": "SecurePassword123!"
    })
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "sre-test@clustermind.io"

    # 2. Login User
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "sre-test@clustermind.io",
        "password": "SecurePassword123!"
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data

    # 3. Fetch /me endpoint with Bearer header
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "sre-test@clustermind.io"

@pytest.mark.asyncio
async def test_invalid_login(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@clustermind.io",
        "password": "WrongPassword!"
    })
    assert resp.status_code == 401
