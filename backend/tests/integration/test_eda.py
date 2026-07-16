import pytest

@pytest.mark.anyio
async def test_dataset_eda_integration(client, auth_headers, sample_csv_content):
    # 1. Setup - Upload file
    files = {"file": ("eda_test.csv", sample_csv_content, "text/csv")}
    data = {"dataset_name": "EDA Workspace"}
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    dataset_id = upload_res.json()["data"]["id"]

    # 2. Trigger EDA calculations
    eda_trigger = await client.post(f"/api/v1/datasets/{dataset_id}/eda", headers=auth_headers)
    assert eda_trigger.status_code == 200
    assert "statistics_json" in eda_trigger.json()["data"]

    # 3. Retrieve EDA calculations
    eda_get = await client.get(f"/api/v1/datasets/{dataset_id}/eda", headers=auth_headers)
    assert eda_get.status_code == 200
    assert "numeric_analysis" in eda_get.json()["data"]["statistics_json"]

    # 4. Flush EDA computations
    eda_delete = await client.delete(f"/api/v1/datasets/{dataset_id}/eda", headers=auth_headers)
    assert eda_delete.status_code == 200

    # Confirm it returns 404 now
    eda_get_again = await client.get(f"/api/v1/datasets/{dataset_id}/eda", headers=auth_headers)
    assert eda_get_again.status_code == 404
