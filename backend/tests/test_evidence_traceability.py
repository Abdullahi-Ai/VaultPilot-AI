import pytest
from app.models.project import Project
from app.models.document import Document
from app.services.investigation_service import InvestigationService

def test_finding_to_document_traceability(client):
    """
    Task 1 & Task 6: Verify finding-to-document traceable relationships.
    Every finding must identify its source documents, extracted fields, and comparison details.
    """
    # 1. Create project & run investigation
    proj_res = client.post("/api/v1/projects/", json={
        "name": "Health Clinic Supply Chain",
        "code": "PRJ-HC-2026",
        "budget": 60000.0,
        "currency": "USD",
        "nas_folder_path": "/volume1/NGO_Projects/Health_2026"
    })
    proj_id = proj_res.json()["id"]

    inv_res = client.post("/api/v1/investigations/run", json={
        "project_id": proj_id,
        "folder_path": "/volume1/NGO_Projects/Health_2026",
        "title": "Health Supply Chain Audit"
    })
    inv_id = inv_res.json()["id"]

    # 2. Get findings list
    findings_res = client.get(f"/api/v1/findings/?investigation_id={inv_id}")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) > 0

    # 3. Check individual finding detail for traceability
    discrepancy = next(f for f in findings if f["classification"] == "CONFIRMED_DISCREPANCY")
    detail_res = client.get(f"/api/v1/findings/{discrepancy['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert len(detail["source_document_ids"]) >= 1
    assert len(detail["documents"]) >= 1
    for doc in detail["documents"]:
        assert doc["id"] in detail["source_document_ids"]
        assert doc["filename"] is not None
        assert doc["file_path"] is not None
        assert doc["project_id"] == proj_id

    # Check explainability fields
    assert "calculation" in detail["comparison_details"]
    assert detail["classification_rationale"] is not None
    assert detail["missing_evidence_details"] is not None
    assert detail["evidence_limitations"] is not None

def test_cross_project_evidence_rejection(test_db):
    """
    Task 2 & Task 6: Cross-project evidence rejection.
    An evidence document belonging to Project A cannot be associated with Project B.
    """
    p1 = Project(name="Project Alpha", code="PRJ-A", nas_folder_path="/volume1/A")
    p2 = Project(name="Project Beta", code="PRJ-B", nas_folder_path="/volume1/B")
    test_db.add_all([p1, p2])
    test_db.commit()
    test_db.refresh(p1)
    test_db.refresh(p2)

    doc_alpha = Document(
        project_id=p1.id,
        filename="Invoice_Alpha.pdf",
        file_path="/volume1/A/Invoice_Alpha.pdf",
        document_type="INVOICE"
    )
    test_db.add(doc_alpha)
    test_db.commit()
    test_db.refresh(doc_alpha)

    # Validating doc_alpha against Project Alpha should pass
    InvestigationService.validate_document_project(doc_alpha, p1.id)

    # Validating doc_alpha against Project Beta must raise ValueError
    with pytest.raises(ValueError) as excinfo:
        InvestigationService.validate_document_project(doc_alpha, p2.id)
    assert "Cross-project evidence rejection" in str(excinfo.value)
    assert f"belongs to Project #{p1.id}" in str(excinfo.value)

def test_ledger_to_document_relationships(client):
    """
    Task 2 & Task 6: Ledger-to-document relationships.
    Evidence ledger entries must reference supporting documents via direct FKs and document IDs.
    """
    proj_res = client.post("/api/v1/projects/", json={
        "name": "Shelter Rehabilitation Grant",
        "code": "PRJ-SHT-2026",
        "budget": 40000.0,
        "currency": "USD",
        "nas_folder_path": "/volume1/NGO_Projects/Shelter_2026"
    })
    proj_id = proj_res.json()["id"]

    inv_res = client.post("/api/v1/investigations/run", json={
        "project_id": proj_id,
        "folder_path": "/volume1/NGO_Projects/Shelter_2026"
    })
    inv_id = inv_res.json()["id"]

    ledger_res = client.get(f"/api/v1/ledger/?investigation_id={inv_id}")
    assert ledger_res.status_code == 200
    entries = ledger_res.json()
    assert len(entries) > 0

    reconciled_entry = next(e for e in entries if e["reconciliation_status"] == "RECONCILED_MATCH")
    detail_res = client.get(f"/api/v1/ledger/{reconciled_entry['id']}")
    assert detail_res.status_code == 200
    entry_detail = detail_res.json()

    assert entry_detail["po_document_id"] is not None
    assert entry_detail["invoice_document_id"] is not None
    assert entry_detail["receipt_document_id"] is not None
    assert len(entry_detail["source_document_ids"]) == 3
    assert entry_detail["po_document"]["document_type"] == "PURCHASE_ORDER"
    assert entry_detail["invoice_document"]["document_type"] == "INVOICE"
    assert entry_detail["receipt_document"]["document_type"] == "RECEIPT"

def test_missing_evidence_scope(client):
    """
    Task 2 & Task 3: Missing evidence must remain explicitly scoped to searched folder.
    Must never be upgraded to confirmed discrepancy or imply non-payment outside folder.
    """
    proj_res = client.post("/api/v1/projects/", json={
        "name": "Solar Water Project",
        "code": "PRJ-SWP-2026",
        "budget": 25000.0,
        "currency": "USD",
        "nas_folder_path": "/volume1/NGO_Projects/Solar_2026"
    })
    proj_id = proj_res.json()["id"]

    inv_res = client.post("/api/v1/investigations/run", json={
        "project_id": proj_id,
        "folder_path": "/volume1/NGO_Projects/Solar_2026"
    })
    inv_id = inv_res.json()["id"]

    findings_res = client.get(f"/api/v1/findings/?investigation_id={inv_id}&classification=MISSING_EVIDENCE")
    assert findings_res.status_code == 200
    missing_findings = findings_res.json()
    assert len(missing_findings) >= 1

    f = missing_findings[0]
    assert f["classification"] == "MISSING_EVIDENCE"
    assert "/volume1/NGO_Projects/Solar_2026" in f["evidence_limitations"]
    assert "not found in this folder" in f["variance_explanation"].lower() or "not located" in f["evidence_limitations"].lower()

def test_unsupported_or_unavailable_source_references(client):
    """
    Task 4 & Task 6: Querying unavailable or deleted references returns clean 404s.
    """
    assert client.get("/api/v1/findings/999999").status_code == 404
    assert client.get("/api/v1/ledger/999999").status_code == 404
    assert client.get("/api/v1/documents/999999").status_code == 404

def test_finding_explanation_consistency(client):
    """
    Task 3: Every finding must expose complete explainability fields.
    """
    proj_res = client.post("/api/v1/projects/", json={
        "name": "Audit Test Project",
        "code": "PRJ-AUDIT-2026",
        "budget": 10000.0,
        "currency": "USD",
        "nas_folder_path": "/volume1/NGO_Projects/Audit"
    })
    proj_id = proj_res.json()["id"]

    inv_res = client.post("/api/v1/investigations/run", json={
        "project_id": proj_id,
        "folder_path": "/volume1/NGO_Projects/Audit"
    })
    inv_id = inv_res.json()["id"]

    findings = client.get(f"/api/v1/findings/?investigation_id={inv_id}").json()
    for f in findings:
        assert f["observed_value"] is not None
        assert len(f["source_paths"]) > 0
        assert f["variance_explanation"] is not None
        assert f["recommended_action"] is not None
        assert f["classification_rationale"] is not None
        assert f["evidence_limitations"] is not None
        # Verify no mention of fraud
        assert "fraud" not in f["variance_explanation"].lower()
        assert "fraud" not in f["recommended_action"].lower()
