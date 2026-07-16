import pytest
from uuid import uuid4

@pytest.mark.anyio
async def test_auth_headers_security(client):
    # 1. Missing Authorization Header
    res_missing = await client.get("/api/v1/auth/me")
    assert res_missing.status_code == 401
    
    # 2. Invalid Bearer Token format
    headers_invalid = {"Authorization": "Bearer invalid_jwt_token_signature_hash"}
    res_invalid = await client.get("/api/v1/auth/me", headers=headers_invalid)
    assert res_invalid.status_code == 401

@pytest.mark.anyio
async def test_cross_user_isolation(client, auth_headers, other_auth_headers, sample_csv_content):
    # 1. User A (auth_headers) uploads a dataset
    files = {"file": ("user_a_private.csv", sample_csv_content, "text/csv")}
    data = {"dataset_name": "User A Workspace"}
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    dataset_id = upload_res.json()["data"]["id"]

    # 2. User B (other_auth_headers) tries to access User A's dataset details - should fail with 404 NotFound
    res_get = await client.get(f"/api/v1/datasets/{dataset_id}", headers=other_auth_headers)
    assert res_get.status_code == 404

    # 3. User B tries to trigger profiling on User A's dataset - should fail with 404 NotFound
    res_profile = await client.post(f"/api/v1/datasets/{dataset_id}/profile", headers=other_auth_headers)
    assert res_profile.status_code == 404

    # 4. User B tries to download User A's dataset file - should fail with 404 NotFound
    res_dl = await client.get(f"/api/v1/datasets/{dataset_id}/download", headers=other_auth_headers)
    assert res_dl.status_code == 404
