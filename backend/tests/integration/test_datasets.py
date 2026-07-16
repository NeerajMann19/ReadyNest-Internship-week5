import pytest

@pytest.mark.anyio
async def test_dataset_lifecycle_integration(client, auth_headers, sample_csv_content):
    # 1. Upload Dataset File
    files = {"file": ("integration_test.csv", sample_csv_content, "text/csv")}
    data = {
        "dataset_name": "Integration Workspace",
        "description": "Integration testing dataset"
    }
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    assert upload_res.status_code == 200
    dataset_id = upload_res.json()["data"]["id"]
    assert dataset_id is not None

    # 2. List Datasets with Search parameters
    list_res = await client.get(f"/api/v1/datasets?search=Integration&page=1&page_size=10", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) > 0

    # 3. Retrieve Dataset Details
    detail_res = await client.get(f"/api/v1/datasets/{dataset_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["dataset_name"] == "Integration Workspace"

    # 4. Preview Grid rows
    preview_res = await client.get(f"/api/v1/datasets/{dataset_id}/preview?page=1&page_size=2", headers=auth_headers)
    assert preview_res.status_code == 200
    assert preview_res.json()["data"]["total_rows"] == 4
    assert len(preview_res.json()["data"]["data"]) == 2

    # 5. Download File endpoint
    dl_res = await client.get(f"/api/v1/datasets/{dataset_id}/download", headers=auth_headers)
    assert dl_res.status_code == 200
    assert dl_res.headers.get("content-type") == "application/octet-stream"
