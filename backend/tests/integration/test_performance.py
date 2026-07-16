import pytest
import time

@pytest.mark.anyio
async def test_large_dataset_performance_smoke(client, auth_headers, large_csv_content):
    # 1. Measure Ingestion / Upload timing
    files = {"file": ("large_perf_data.csv", large_csv_content, "text/csv")}
    data = {"dataset_name": "Performance Workspace"}
    
    start_upload = time.perf_counter()
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    end_upload = time.perf_counter()
    
    assert upload_res.status_code == 200
    dataset_id = upload_res.json()["data"]["id"]
    upload_time = end_upload - start_upload
    print(f"\n[PERF] Large CSV Upload Ingest time: {upload_time:.4f}s")
    assert upload_time < 5.0  # Safe threshold for 10k rows

    # 2. Measure Profiling execution timing
    start_profile = time.perf_counter()
    profile_res = await client.post(f"/api/v1/datasets/{dataset_id}/profile", headers=auth_headers)
    end_profile = time.perf_counter()
    
    assert profile_res.status_code == 200
    profile_time = end_profile - start_profile
    print(f"[PERF] Large CSV Profiling execution time: {profile_time:.4f}s")
    assert profile_time < 10.0  # Safe threshold for stats profiling 10k rows

    # 3. Measure Cleaning execution timing
    cleaning_ops = [
        {"type": "drop_duplicates"},
        {"type": "fill_missing", "column": "score", "parameters": {"method": "mean"}}
    ]
    
    start_clean = time.perf_counter()
    clean_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/clean",
        json={"operations": cleaning_ops},
        headers=auth_headers
    )
    end_clean = time.perf_counter()
    
    assert clean_res.status_code == 200
    clean_time = end_clean - start_clean
    print(f"[PERF] Large CSV Cleaning application time: {clean_time:.4f}s")
    assert clean_time < 10.0  # Safe threshold for cleaning transformations
