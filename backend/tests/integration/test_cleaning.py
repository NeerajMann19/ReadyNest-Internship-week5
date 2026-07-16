import pytest

@pytest.mark.anyio
async def test_dataset_cleaning_integration(client, auth_headers, sample_csv_content):
    # 1. Setup - Upload file
    files = {"file": ("cleaning_test.csv", sample_csv_content, "text/csv")}
    data = {"dataset_name": "Cleaning Workspace"}
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    dataset_id = upload_res.json()["data"]["id"]

    # Trigger initial profiling
    await client.post(f"/api/v1/datasets/{dataset_id}/profile", headers=auth_headers)

    # 2. Simulate cleaning preview
    preview_operations = [
        {"type": "drop_duplicates"},
        {"type": "fill_missing", "column": "score", "parameters": {"method": "mean"}}
    ]
    preview_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/clean/preview",
        json={"operations": preview_operations},
        headers=auth_headers
    )
    assert preview_res.status_code == 200
    assert "after" in preview_res.json()["data"]

    # 3. Apply cleaning operations
    apply_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/clean",
        json={"operations": preview_operations},
        headers=auth_headers
    )
    assert apply_res.status_code == 200
    # Confirm version 2 is now active
    assert len(apply_res.json()["data"]["versions"]) == 2
    active_version = next((v for v in apply_res.json()["data"]["versions"] if v["is_current"]), None)
    assert active_version["version_number"] == 2
