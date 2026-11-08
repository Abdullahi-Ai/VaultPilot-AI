import pytest
from app.main import app

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert "VaultPilot AI" in response.json()["service"]

def test_create_and_list_project(client):
    payload = {
        "name": "Clean Water Initiative",
        "code": "PRJ-WTR-2026",
        "donor": "Global Water Fund",
        "budget": 45000.0,
        "currency": "USD",
        "nas_folder_path": "/volume1/NGO_Projects/Water_2026",
        "description": "Drilling boreholes in semi-arid zones"
    }
    create_res = client.post("/api/v1/projects/", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["code"] == "PRJ-WTR-2026"
    assert created_data["id"] is not None

    list_res = client.get("/api/v1/projects/")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

def test_run_investigation_and_findings(client):
    # 1. Create project
    proj_payload = {
        "name": "Education Tech Grant",
        "code": "PRJ-EDU-2026",
        "donor": "Global Literacy Partner",
        "budget": 30000.0,
        "currency": "USD",
        "nas_folder_path": "/volume1/NGO_Projects/Education_2026"
    }
    proj_res = client.post("/api/v1/projects/", json=proj_payload)
    proj_id = proj_res.json()["id"]

    # 2. Run investigation with Pydantic body to /api/v1/investigations/run
    inv_payload = {
        "project_id": proj_id,
        "folder_path": "/volume1/NGO_Projects/Education_2026",
        "title": "Comprehensive Education Grant Audit"
    }
    inv_res = client.post("/api/v1/investigations/run", json=inv_payload)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    assert inv_data["status"] == "COMPLETED"
    assert inv_data["document_count"] > 0
    assert len(inv_data["findings"]) > 0
    assert len(inv_data["ledger_entries"]) > 0

    # 3. Check findings endpoint
    findings_res = client.get(f"/api/v1/findings/?investigation_id={inv_data['id']}")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert any(f["classification"] == "CONFIRMED_DISCREPANCY" for f in findings)
    assert any(f["classification"] == "MISSING_EVIDENCE" for f in findings)
    assert any(f["classification"] == "UNVERIFIED" for f in findings)
    assert any(f["classification"] == "POTENTIAL_ANOMALY" for f in findings)

    # 4. Check dashboard statistics
    dash_res = client.get("/api/v1/dashboard/stats")
    assert dash_res.status_code == 200
    dash_stats = dash_res.json()
    assert dash_stats["total_projects"] >= 1
    assert dash_stats["total_investigations"] >= 1
    assert dash_stats["findings_by_classification"]["CONFIRMED_DISCREPANCY"] >= 1

def test_run_investigation_validation_errors(client):
    # Test missing folder_path
    res1 = client.post("/api/v1/investigations/run", json={"project_id": 1, "folder_path": ""})
    assert res1.status_code in [400, 422]

    # Test directory traversal in folder_path
    res2 = client.post("/api/v1/investigations/run", json={"project_id": 1, "folder_path": "/volume1/../../etc"})
    assert res2.status_code in [400, 422]

    # Test non-existent project_id
    res3 = client.post("/api/v1/investigations/run", json={"project_id": 9999, "folder_path": "/volume1/test"})
    assert res3.status_code == 404
