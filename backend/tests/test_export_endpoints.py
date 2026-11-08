import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.project import Project
from app.models.investigation import Investigation
from app.models.document import Document
from app.models.finding import Finding
from app.models.ledger import EvidenceLedgerEntry
from app.models.report import InvestigationReport
from app.services.report_service import ReportService

@pytest.fixture
def export_test_data(test_db):
    """Sets up an investigation environment with a verified report snapshot."""
    project1 = Project(
        name="Clean Water Initiative",
        code="PRJ-WASH-2026",
        donor="Global Health Alliance",
        budget=100000.0,
        currency="USD",
        nas_folder_path="/volume1/finance/WASH-2026"
    )
    project2 = Project(
        name="Solar Clinic Support",
        code="PRJ-SOLAR-2026",
        donor="Solar Foundation",
        budget=50000.0,
        currency="USD",
        nas_folder_path="/volume1/finance/SOLAR-2026"
    )
    test_db.add_all([project1, project2])
    test_db.flush()

    inv1 = Investigation(
        project_id=project1.id,
        title="Q1 WASH Procurement Audit",
        scope_path="/volume1/finance/WASH-2026",
        status="COMPLETED",
        summary="Audit of water purification equipment.",
        document_count=2
    )
    inv2 = Investigation(
        project_id=project2.id,
        title="Q1 Solar Panels Audit",
        scope_path="/volume1/finance/SOLAR-2026",
        status="COMPLETED",
        summary="Audit of solar panels procurement.",
        document_count=1
    )
    test_db.add_all([inv1, inv2])
    test_db.flush()

    doc_po = Document(
        project_id=project1.id,
        investigation_id=inv1.id,
        filename="PO-WASH-101.pdf",
        file_path="/volume1/finance/WASH-2026/PO-WASH-101.pdf",
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-101", "amount": 5000.0, "currency": "USD"}
    )
    doc_inv = Document(
        project_id=project1.id,
        investigation_id=inv1.id,
        filename="INV-WASH-202.pdf",
        file_path="/volume1/finance/WASH-2026/INV-WASH-202.pdf",
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_number": "INV-202", "po_reference": "PO-101", "amount": 5000.0, "currency": "USD"}
    )
    test_db.add_all([doc_po, doc_inv])
    test_db.flush()

    f1 = Finding(
        investigation_id=inv1.id,
        title="Discrepant Shipping Charge",
        classification="CONFIRMED_DISCREPANCY",
        variance_explanation="Unapproved shipping fee of 150 USD billed.",
        recommended_action="Recover 150 USD from vendor."
    )
    test_db.add(f1)

    entry = EvidenceLedgerEntry(
        investigation_id=inv1.id,
        transaction_id="TXN-WASH-001",
        item_description="Filtration Membrane Filters",
        po_reference="PO-101",
        po_amount=5000.0,
        invoice_number="INV-202",
        invoice_amount=5000.0,
        paid_amount=5000.0,
        currency="USD",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH"
    )
    test_db.add(entry)
    test_db.commit()

    report1 = ReportService.create_report_snapshot(db=test_db, investigation_id=inv1.id, title="Official Audit Dossier")

    return {
        "project1": project1,
        "project2": project2,
        "inv1": inv1,
        "inv2": inv2,
        "report1": report1
    }

def test_scoped_html_export_success(client: TestClient, export_test_data):
    """Verify scoped HTML export returns 200, proper CSP, headers, and full HTML document."""
    inv1 = export_test_data["inv1"]
    report1 = export_test_data["report1"]

    resp = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/html")
    assert resp.status_code == 200
    assert "text/html; charset=utf-8" in resp.headers["content-type"]
    assert f'inline; filename="audit_dossier_report_{report1.id}_v{report1.report_version}.html"' in resp.headers["content-disposition"]

    # Verify CSP and security headers
    assert "default-src 'none'" in resp.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in resp.headers["content-security-policy"]
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["x-content-type-options"] == "nosniff"

    # Verify document content
    html_text = resp.text
    assert "<!DOCTYPE html>" in html_text
    assert "VaultPilot AI" in html_text
    assert f"IR-{report1.id}-V{report1.report_version}" in html_text
    assert "SNAPSHOT INTEGRITY: VERIFIED" in html_text
    assert "Filtration Membrane Filters" in html_text
    assert "http://" not in html_text
    assert "https://" not in html_text

def test_scoped_csv_export_success(client: TestClient, export_test_data):
    """Verify scoped CSV export returns 200, UTF-8 BOM, correct headers, and sanitized rows."""
    inv1 = export_test_data["inv1"]
    report1 = export_test_data["report1"]

    resp = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/csv?schedule=reconciliation")
    assert resp.status_code == 200
    assert "text/csv; charset=utf-8" in resp.headers["content-type"]
    assert f'attachment; filename="audit_report_{report1.id}_reconciliation_v{report1.report_version}.csv"' in resp.headers["content-disposition"]
    assert resp.headers["x-content-type-options"] == "nosniff"

    # Verify UTF-8 BOM prefix
    content_bytes = resp.content
    assert content_bytes.startswith(b"\xef\xbb\xbf")

    # Verify CSV structure
    csv_text = resp.text
    assert "Transaction_Tracking_ID,Item_Description" in csv_text
    assert "TXN-WASH-001" in csv_text
    assert "Filtration Membrane Filters" in csv_text

def test_scoped_csv_export_all_schedules(client: TestClient, export_test_data):
    """Verify scoped CSV export handles summary, findings, and evidence schedules."""
    inv1 = export_test_data["inv1"]
    report1 = export_test_data["report1"]

    for sched in ["summary", "findings", "evidence"]:
        resp = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/csv?schedule={sched}")
        assert resp.status_code == 200
        assert f'attachment; filename="audit_report_{report1.id}_{sched}_v{report1.report_version}.csv"' in resp.headers["content-disposition"]

def test_scoped_csv_export_invalid_schedule_returns_400(client: TestClient, export_test_data):
    """Verify invalid schedule query parameter returns 400 Bad Request."""
    inv1 = export_test_data["inv1"]
    report1 = export_test_data["report1"]

    resp = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/csv?schedule=invalid_sched")
    assert resp.status_code == 400
    assert "Invalid schedule" in resp.json()["detail"]

def test_scoped_exports_ownership_mismatch_returns_404(client: TestClient, export_test_data):
    """Verify querying report under the wrong investigation ID returns 404."""
    inv2 = export_test_data["inv2"] # Project 2 / Investigation 2
    report1 = export_test_data["report1"] # Belongs to Investigation 1

    # HTML export mismatch
    resp_html = client.get(f"/api/v1/investigations/{inv2.id}/reports/{report1.id}/html")
    assert resp_html.status_code == 404
    assert "not found for investigation" in resp_html.json()["detail"]

    # CSV export mismatch
    resp_csv = client.get(f"/api/v1/investigations/{inv2.id}/reports/{report1.id}/csv")
    assert resp_csv.status_code == 404
    assert "not found for investigation" in resp_csv.json()["detail"]

def test_scoped_exports_nonexistent_report_returns_404(client: TestClient, export_test_data):
    """Verify querying a non-existent report ID returns 404."""
    inv1 = export_test_data["inv1"]

    resp_html = client.get(f"/api/v1/investigations/{inv1.id}/reports/99999/html")
    assert resp_html.status_code == 404

    resp_csv = client.get(f"/api/v1/investigations/{inv1.id}/reports/99999/csv")
    assert resp_csv.status_code == 404

def test_scoped_exports_tampered_snapshot_returns_409_conflict(client: TestClient, test_db, export_test_data):
    """Verify that a tampered snapshot payload triggers fail-closed 409 Conflict for both HTML and CSV."""
    inv1 = export_test_data["inv1"]
    report1 = export_test_data["report1"]

    # Tamper with snapshot in DB
    tampered_payload = dict(report1.snapshot_payload)
    tampered_payload["unauthorized_modification"] = "tampered"
    report1.snapshot_payload = tampered_payload
    test_db.commit()

    # HTML export must refuse with 409 Conflict
    resp_html = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/html")
    assert resp_html.status_code == 409
    assert "REPORT_INTEGRITY_VERIFICATION_FAILED" in resp_html.json()["detail"]

    # CSV export must refuse with 409 Conflict
    resp_csv = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/csv")
    assert resp_csv.status_code == 409
    assert "REPORT_INTEGRITY_VERIFICATION_FAILED" in resp_csv.json()["detail"]

def test_scoped_exports_corrupted_hash_returns_409_conflict(client: TestClient, test_db, export_test_data):
    """Verify that a snapshot with corrupted/mismatched integrity hash triggers fail-closed 409 Conflict."""
    inv1 = export_test_data["inv1"]
    report1 = export_test_data["report1"]

    report1.snapshot_integrity_hash = "0" * 64
    test_db.commit()

    resp_html = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/html")
    assert resp_html.status_code == 409
    assert "REPORT_INTEGRITY_VERIFICATION_FAILED" in resp_html.json()["detail"]

    resp_csv = client.get(f"/api/v1/investigations/{inv1.id}/reports/{report1.id}/csv")
    assert resp_csv.status_code == 409
    assert "REPORT_INTEGRITY_VERIFICATION_FAILED" in resp_csv.json()["detail"]

def test_scoped_exports_missing_investigation_returns_404(client: TestClient, export_test_data):
    """Verify that referencing a non-existent investigation ID returns 404."""
    report1 = export_test_data["report1"]

    resp_html = client.get(f"/api/v1/investigations/99999/reports/{report1.id}/html")
    assert resp_html.status_code == 404

    resp_csv = client.get(f"/api/v1/investigations/99999/reports/{report1.id}/csv")
    assert resp_csv.status_code == 404

