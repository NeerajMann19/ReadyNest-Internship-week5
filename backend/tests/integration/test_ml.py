"""
Integration tests for Machine Learning training pipeline, predictions, and edge cases.
"""
import pytest
import os
from uuid import uuid4
from app.services.ml import MLService

@pytest.mark.anyio
async def test_ml_lifecycle_integration(client, auth_headers):
    # 1. Setup - Ingest dataset with 15 rows to satisfy constraints
    csv_rows = ["id,name,score,age"]
    for i in range(15):
        csv_rows.append(f"{i},User{i},{80 + (i % 5)},{20 + i}")
    dataset_15_rows = "\n".join(csv_rows)

    files = {"file": ("ml_lifecycle_data.csv", dataset_15_rows, "text/csv")}
    data = {"dataset_name": "ML Workspace"}
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    dataset_id = upload_res.json()["data"]["id"]

    # 2. Trigger Async Training
    train_res = await client.post(
        f"/api/v1/ml/train?dataset_id={dataset_id}",
        json={
            "target_column": "score",
            "problem_type": "regression",
            "candidate_algorithms": ["random_forest", "linear_regression"]
        },
        headers=auth_headers
    )
    assert train_res.status_code == 202
    model_id = train_res.json()["data"]["id"]
    assert model_id is not None
    assert train_res.json()["data"]["status"] == "PENDING"

    # 3. Synchronously execute background training task
    await MLService.train_model_task(model_id)

    # 4. Fetch details and verify completed champion model
    detail_res = await client.get(f"/api/v1/ml/{model_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    model_data = detail_res.json()["data"]
    assert model_data["status"] == "COMPLETED"
    assert model_data["model_type"] in ["random_forest", "linear_regression"]
    assert model_data["best_score"] is not None
    assert "r2" in model_data["evaluation_metrics"]
    assert model_data["model_size_bytes"] > 0
    assert os.path.exists(f"uploads/models/model_{model_id}.joblib")

    # 5. Perform Real-time prediction row inference
    input_payload = {"id": 5, "name": "Eve", "age": 24}
    pred_res = await client.post(
        f"/api/v1/ml/{model_id}/predict",
        json={"input_data": input_payload},
        headers=auth_headers
    )
    assert pred_res.status_code == 200
    assert "prediction" in pred_res.json()["data"]

    # 6. Retrieve Prediction logs history
    history_res = await client.get(f"/api/v1/ml/{model_id}/history?limit=10", headers=auth_headers)
    assert history_res.status_code == 200
    assert len(history_res.json()["data"]) == 1
    assert history_res.json()["data"][0]["prediction"] is not None

    # 7. Verify model list endpoint
    list_res = await client.get("/api/v1/ml", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) > 0

    # 8. Delete model
    del_res = await client.delete(f"/api/v1/ml/{model_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert not os.path.exists(f"uploads/models/model_{model_id}.joblib")


@pytest.mark.anyio
async def test_ml_edge_cases_integration(client, auth_headers):
    # Setup - Ingest dataset with 15 rows
    csv_rows = ["id,name,score,age"]
    for i in range(15):
        csv_rows.append(f"{i},User{i},{80 + (i % 5)},{20 + i}")
    dataset_15_rows = "\n".join(csv_rows)

    files = {"file": ("ml_edge_cases.csv", dataset_15_rows, "text/csv")}
    data = {"dataset_name": "ML Edge Cases"}
    upload_res = await client.post("/api/v1/datasets", data=data, files=files, headers=auth_headers)
    dataset_id = upload_res.json()["data"]["id"]

    # 1. Edge Case: Target column missing
    bad_train_res = await client.post(
        f"/api/v1/ml/train?dataset_id={dataset_id}",
        json={"target_column": "missing_col"},
        headers=auth_headers
    )
    assert bad_train_res.status_code == 202
    model_id_bad = bad_train_res.json()["data"]["id"]
    
    await MLService.train_model_task(model_id_bad)
    
    detail_res_bad = await client.get(f"/api/v1/ml/{model_id_bad}", headers=auth_headers)
    assert detail_res_bad.status_code == 200
    assert detail_res_bad.json()["data"]["status"] == "FAILED"
    assert "missing" in detail_res_bad.json()["data"]["error_message"]

    # 2. Edge Case: Small dataset error
    small_csv = "id,score\n1,10\n2,20"
    small_files = {"file": ("small.csv", small_csv, "text/csv")}
    small_upload = await client.post("/api/v1/datasets", data=data, files=small_files, headers=auth_headers)
    small_dataset_id = small_upload.json()["data"]["id"]

    small_train_res = await client.post(
        f"/api/v1/ml/train?dataset_id={small_dataset_id}",
        json={"target_column": "score"},
        headers=auth_headers
    )
    model_id_small = small_train_res.json()["data"]["id"]
    await MLService.train_model_task(model_id_small)
    
    detail_res_small = await client.get(f"/api/v1/ml/{model_id_small}", headers=auth_headers)
    assert detail_res_small.status_code == 200
    assert detail_res_small.json()["data"]["status"] == "FAILED"
    assert "fewer than 10" in detail_res_small.json()["data"]["error_message"]
