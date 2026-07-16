import pytest

@pytest.mark.anyio
async def test_dataset_profiling_integration(client, auth_headers, sample_csv_content):
    # 1. Setup - Upload file
    files = {"file": ("profiling_test.csv", sample_csv_content, "text/csv")}
    data = {"dataset_name": "Profiling Workspace"}
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    dataset_id = upload_res.json()["data"]["id"]

    # 2. Trigger Profiling
    profile_trigger = await client.post(f"/api/v1/datasets/{dataset_id}/profile", headers=auth_headers)
    assert profile_trigger.status_code == 200
    assert profile_trigger.json()["data"]["quality_score"] > 0

    # 3. Retrieve Profile details
    profile_get = await client.get(f"/api/v1/datasets/{dataset_id}/profile", headers=auth_headers)
    assert profile_get.status_code == 200
    assert len(profile_get.json()["data"]["column_summary"]) == 4
