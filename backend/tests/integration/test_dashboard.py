import pytest

@pytest.mark.anyio
async def test_dashboard_summary_integration(client, auth_headers):
    # Retrieve dashboard unified aggregated statistics
    res = await client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "kpis" in data
    assert "charts" in data
    assert "recent_activity" in data
    assert "recent_datasets" in data
    assert "recent_cleaning_jobs" in data
    assert "recent_insights" in data
    assert "recent_reports" in data
    assert "metadata" in data
