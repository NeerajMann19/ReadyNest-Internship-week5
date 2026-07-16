import pytest
from uuid import uuid4

@pytest.mark.anyio
async def test_auth_integration_flow(client):
    email = f"user_{uuid4().hex[:6]}@auth.com"
    password = "authpassword123"

    # 1. Register User
    reg_res = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 200
    assert reg_res.json()["success"] is True

    # 2. Login User
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    assert access_token is not None

    # 3. Retrieve profile using access token
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_res = await client.get("/api/v1/auth/me", headers=headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["data"]["email"] == email

    # 4. Exchange refresh token for new access token
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_token_data = refresh_res.json()["data"]
    assert new_token_data["access_token"] != access_token
