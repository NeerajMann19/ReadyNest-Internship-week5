import pytest

@pytest.mark.anyio
async def test_dataset_insights_integration(client, auth_headers, sample_csv_content):
    # 1. Setup - Upload file
    files = {"file": ("insights_test.csv", sample_csv_content, "text/csv")}
    data = {"dataset_name": "Insights Workspace"}
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    dataset_id = upload_res.json()["data"]["id"]

    # Trigger profiling to make it ready for insights
    await client.post(f"/api/v1/datasets/{dataset_id}/profile", headers=auth_headers)

    # 2. Trigger AI Insights rules engine
    insights_trigger = await client.post(f"/api/v1/datasets/{dataset_id}/insights", headers=auth_headers)
    assert insights_trigger.status_code == 200
    assert "insights_json" in insights_trigger.json()["data"]

    # 3. Retrieve complete Insights observations
    insights_get = await client.get(f"/api/v1/datasets/{dataset_id}/insights", headers=auth_headers)
    assert insights_get.status_code == 200
    assert "summary_json" in insights_get.json()["data"]

    # 4. Fetch executive health summary metadata
    summary_get = await client.get(f"/api/v1/datasets/{dataset_id}/insights/summary", headers=auth_headers)
    assert summary_get.status_code == 200
    assert "quality_score" in summary_get.json()["data"]

    # 5. Flush Insights details
    insights_delete = await client.delete(f"/api/v1/datasets/{dataset_id}/insights", headers=auth_headers)
    assert insights_delete.status_code == 200

    # Confirm it returns 404 now
    insights_get_again = await client.get(f"/api/v1/datasets/{dataset_id}/insights", headers=auth_headers)
    assert insights_get_again.status_code == 404
