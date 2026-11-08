import pytest
from app.models.project import Project
from app.models.investigation import Investigation
from app.models.document import Document
from app.models.finding import Finding
from app.models.ledger import EvidenceLedgerEntry
from app.models.report import InvestigationReport
from app.services.report_service import ReportService

@pytest.fixture
def sample_investigation_setup(test_db):
    """Creates a complete populated investigation with documents, findings, and ledger entries."""
    project = Project(
        name="Clean Water Initiative",
        code="CWI-2026",
        donor="Global Water Aid",
        budget=100000.0,
        currency="USD",
        nas_folder_path="/volume1/finance/CWI-2026"
    )
    test_db.add(project)
    test_db.flush()

    inv = Investigation(
        project_id=project.id,
        title="Routine Water Grant Audit",
        scope_path="/volume1/finance/CWI-2026",
        status="COMPLETED",
        summary="Audit of Q1 expenses. Reconciled $8,500.00 USD.",
        document_count=3
    )
    test_db.add(inv)
    test_db.flush()

    doc_po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-2026-081.pdf",
        file_path="/volume1/finance/CWI-2026/orders/PO-2026-081.pdf",
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-2026-081", "amount": 8500.0, "currency": "USD", "vendor": "SunPower Ltd"}
    )
    doc_inv = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-SP-1092.pdf",
        file_path="/volume1/finance/CWI-2026/invoices/INV-SP-1092.pdf",
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_number": "INV-SP-1092", "po_reference": "PO-2026-081", "amount": 8500.0, "currency": "USD", "vendor": "SunPower Ltd"}
    )
    doc_rec = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="REC-BNK-993.pdf",
        file_path="/volume1/finance/CWI-2026/receipts/REC-BNK-993.pdf",
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"receipt_id": "REC-BNK-993", "invoice_reference": "INV-SP-1092", "amount": 8500.0, "currency": "USD", "payee": "SunPower Ltd"}
    )
    test_db.add_all([doc_po, doc_inv, doc_rec])
    test_db.flush()

    finding1 = Finding(
        investigation_id=inv.id,
        title="Prompt Invoicing Turnaround",
        classification="POTENTIAL_ANOMALY",
        subject_reference="PO-2026-081 vs INV-SP-1092",
        source_paths=[doc_po.file_path, doc_inv.file_path],
        expected_value="30-day payment cycle",
        observed_value="14-day turnaround",
        variance_explanation="Invoice submitted 14 days after purchase order issuance. Anomalous turnaround.",
        recommended_action="Verify field goods delivery receipt note.",
        source_document_ids=[doc_po.id, doc_inv.id],
        extracted_fields_used={"po_reference": "PO-2026-081", "invoice_number": "INV-SP-1092"},
        comparison_details={"days_delta": -16},
        evidence_limitations="Scoped to project folder.",
        classification_rationale="Classified as POTENTIAL_ANOMALY because rapid invoicing requires delivery confirmation."
    )
    test_db.add(finding1)

    entry1 = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-1-SP-1092",
        item_description="Solar Inverter Components",
        supplier_name="SunPower Ltd",
        po_reference="PO-2026-081",
        po_amount=8500.0,
        invoice_number="INV-SP-1092",
        invoice_amount=8500.0,
        receipt_proof="REC-BNK-993",
        receipt_amount=8500.0,
        paid_amount=8500.0,
        currency="USD",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH",
        source_file_paths=[doc_po.file_path, doc_inv.file_path, doc_rec.file_path],
        source_document_ids=[doc_po.id, doc_inv.id, doc_rec.id]
    )
    test_db.add(entry1)
    test_db.commit()

    return {
        "project": project,
        "investigation": inv,
        "docs": [doc_po, doc_inv, doc_rec],
        "findings": [finding1],
        "entries": [entry1]
    }


def test_1_report_creation_for_valid_investigation(client, sample_investigation_setup):
    """Test 1: Report creation for a valid investigation."""
    inv_id = sample_investigation_setup["investigation"].id
    resp = client.post(f"/api/v1/investigations/{inv_id}/reports", json={"title": "Official Audit Dossier Q1"})
    assert resp.status_code == 201
    data = resp.json()

    assert data["investigation_id"] == inv_id
    assert data["report_version"] == 1
    assert data["report_status"] == "FINAL"
    assert data["report_title"] == "Official Audit Dossier Q1"
    assert len(data["snapshot_integrity_hash"]) == 64
    assert "snapshot_payload" in data
    assert data["snapshot_payload"]["metadata"]["report_version"] == 1


def test_2_rejection_of_nonexistent_investigation(client):
    """Test 2: Rejection of nonexistent investigations (HTTP 404)."""
    resp = client.post("/api/v1/investigations/99999/reports", json={"title": "Ghost Report"})
    assert resp.status_code == 404
    assert "Investigation with ID 99999 not found" in resp.json()["detail"]


def test_3_project_investigation_ownership_validation(client, sample_investigation_setup):
    """Test 3: Project/investigation ownership validation."""
    inv = sample_investigation_setup["investigation"]
    proj = sample_investigation_setup["project"]
    resp = client.post(f"/api/v1/investigations/{inv.id}/reports", json={})
    assert resp.status_code == 201
    data = resp.json()

    assert data["project_id"] == proj.id
    assert data["snapshot_payload"]["investigation_summary"]["project_code"] == proj.code


def test_4_correct_findings_snapshot_capture(client, sample_investigation_setup):
    """Test 4: Correct findings snapshot capture."""
    inv_id = sample_investigation_setup["investigation"].id
    resp = client.post(f"/api/v1/investigations/{inv_id}/reports", json={})
    assert resp.status_code == 201
    findings_snap = resp.json()["snapshot_payload"]["findings_snapshot"]

    assert len(findings_snap) == 1
    f = findings_snap[0]
    assert f["title"] == "Prompt Invoicing Turnaround"
    assert f["classification"] == "POTENTIAL_ANOMALY"
    assert f["expected_value"] == "30-day payment cycle"
    assert f["observed_value"] == "14-day turnaround"
    assert f["requires_human_review"] is True
    assert len(f["source_paths"]) == 2


def test_5_correct_evidence_document_capture(client, sample_investigation_setup):
    """Test 5: Correct evidence document capture."""
    inv_id = sample_investigation_setup["investigation"].id
    resp = client.post(f"/api/v1/investigations/{inv_id}/reports", json={})
    assert resp.status_code == 201
    docs_snap = resp.json()["snapshot_payload"]["evidence_register_snapshot"]

    assert len(docs_snap) == 3
    doc_types = {d["document_type"] for d in docs_snap}
    assert doc_types == {"PURCHASE_ORDER", "INVOICE", "RECEIPT"}

    roles = {d["evidence_role"] for d in docs_snap}
    assert roles == {"AUTHORIZATION", "BILLING", "DISBURSEMENT_PROOF"}


def test_6_currency_separated_financial_summaries(test_db, sample_investigation_setup):
    """Test 6: Currency-separated financial summaries without cross-currency aggregation."""
    inv = sample_investigation_setup["investigation"]
    # Add a EUR entry to the investigation
    entry_eur = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-2-EUR",
        item_description="EU Water Testing Kits",
        supplier_name="EuroLab Gmbh",
        invoice_number="INV-EUR-01",
        invoice_amount=3200.0,
        paid_amount=3200.0,
        currency="EUR",
        reconciliation_status="RECONCILED_MATCH"
    )
    test_db.add(entry_eur)
    test_db.commit()

    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    by_curr = report.financial_summary["by_currency"]

    assert "USD" in by_curr
    assert "EUR" in by_curr
    assert by_curr["USD"]["verified_expenditure"] == 8500.0
    assert by_curr["EUR"]["verified_expenditure"] == 3200.0
    # Strict rule: No combined/converted total across currencies
    assert "total" not in by_curr


def test_7_missing_currency_excluded_from_verified_totals(test_db, sample_investigation_setup):
    """Test 7: Missing currency is excluded from verified totals and tracked in undocumented list."""
    inv = sample_investigation_setup["investigation"]
    entry_nocurr = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-NOCURR",
        item_description="Unspecified Field Supplies",
        paid_amount=4000.0,
        currency=None, # Missing currency
        reconciliation_status="RECONCILED_MATCH"
    )
    test_db.add(entry_nocurr)
    test_db.commit()

    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    by_curr = report.financial_summary["by_currency"]
    undocumented = report.financial_summary["undocumented_currency_entries"]

    # USD total must not include the 4000.0
    assert by_curr["USD"]["verified_expenditure"] == 8500.0
    # Must be recorded in undocumented entries
    assert len(undocumented) == 1
    assert undocumented[0]["transaction_id"] == "TXN-NOCURR"
    assert undocumented[0]["unverified_amount"] == 4000.0


def test_8_unapplied_receipts_separated_from_verified_expenditure(test_db, sample_investigation_setup):
    """Test 8: Unapplied receipts are recorded separately and excluded from verified expenditure."""
    inv = sample_investigation_setup["investigation"]
    rec_entry = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-STANDALONE-REC",
        item_description="Unapplied Bank Wire",
        paid_amount=1200.0,
        currency="USD",
        reconciliation_status="UNAPPLIED_RECEIPT"
    )
    test_db.add(rec_entry)
    test_db.commit()

    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    usd_summary = report.financial_summary["by_currency"]["USD"]

    assert usd_summary["verified_expenditure"] == 8500.0 # Unchanged
    assert usd_summary["unapplied_receipts"] == 1200.0


def test_9_potential_anomalies_retaining_classifications(test_db, sample_investigation_setup):
    """Test 9: Potential anomalies retain classifications and variance hold amounts."""
    inv = sample_investigation_setup["investigation"]
    entry_hold = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-HOLD",
        item_description="Unauthorized Excess Pump Accessories",
        invoice_amount=5000.0,
        variance_amount=1500.0,
        currency="USD",
        reconciliation_status="VARIANCE_HOLD"
    )
    test_db.add(entry_hold)
    test_db.commit()

    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    usd_summary = report.financial_summary["by_currency"]["USD"]

    assert usd_summary["variance_hold_amounts"] == 1500.0
    assert report.requires_human_review is True


def test_10_existing_report_unchanged_after_finding_is_edited(test_db, sample_investigation_setup):
    """Test 10: Existing report remains unchanged after an underlying live finding is edited."""
    inv = sample_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    original_title = report.snapshot_payload["findings_snapshot"][0]["title"]
    original_hash = report.snapshot_integrity_hash

    # Mutate the live finding in the database
    live_finding = sample_investigation_setup["findings"][0]
    live_finding.title = "MUTATED: Vendor Fraud Allegation (UNAUTHORIZED EDIT)"
    test_db.commit()

    # Re-fetch report from DB
    re_fetched = ReportService.get_report(db=test_db, report_id=report.id)
    snapshot_title = re_fetched.snapshot_payload["findings_snapshot"][0]["title"]

    assert snapshot_title == original_title
    assert snapshot_title != "MUTATED: Vendor Fraud Allegation (UNAUTHORIZED EDIT)"
    assert re_fetched.snapshot_integrity_hash == original_hash


def test_11_existing_report_unchanged_after_document_is_added(test_db, sample_investigation_setup):
    """Test 11: Existing report remains unchanged after a new document is added to investigation."""
    inv = sample_investigation_setup["investigation"]
    proj = sample_investigation_setup["project"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    original_doc_count = report.snapshot_payload["investigation_summary"]["document_count"]

    # Add a 4th document to the investigation
    new_doc = Document(
        project_id=proj.id,
        investigation_id=inv.id,
        filename="LATE_ADDITION.pdf",
        file_path="/volume1/finance/CWI-2026/LATE_ADDITION.pdf",
        document_type="OTHER"
    )
    test_db.add(new_doc)
    test_db.commit()

    re_fetched = ReportService.get_report(db=test_db, report_id=report.id)
    assert re_fetched.snapshot_payload["investigation_summary"]["document_count"] == original_doc_count
    assert len(re_fetched.snapshot_payload["evidence_register_snapshot"]) == original_doc_count


def test_12_earlier_report_preserved_after_newer_report_is_created(test_db, sample_investigation_setup):
    """Test 12: Earlier report is preserved when a newer report version is created."""
    inv = sample_investigation_setup["investigation"]
    report_v1 = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    assert report_v1.report_version == 1

    # Add new evidence finding
    new_f = Finding(
        investigation_id=inv.id,
        title="Second Finding in Q2",
        classification="MISSING_EVIDENCE",
        variance_explanation="Missing second receipt.",
        recommended_action="Request receipt.",
        source_document_ids=[]
    )
    test_db.add(new_f)
    test_db.commit()

    report_v2 = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    assert report_v2.report_version == 2

    # Re-fetch both reports
    v1_check = ReportService.get_report(db=test_db, report_id=report_v1.id)
    v2_check = ReportService.get_report(db=test_db, report_id=report_v2.id)

    assert v1_check.report_version == 1
    assert len(v1_check.snapshot_payload["findings_snapshot"]) == 1
    assert v2_check.report_version == 2
    assert len(v2_check.snapshot_payload["findings_snapshot"]) == 2


def test_13_cross_project_evidence_rejection(test_db, sample_investigation_setup):
    """Test 13: Cross-project evidence rejection raises ValueError."""
    inv = sample_investigation_setup["investigation"]
    # Create an alien document belonging to Project #999
    alien_doc = Document(
        project_id=999, # Mismatched project!
        investigation_id=inv.id,
        filename="ALIEN_DOC.pdf",
        file_path="/volume2/alien/ALIEN_DOC.pdf",
        document_type="INVOICE"
    )
    test_db.add(alien_doc)
    test_db.commit()

    with pytest.raises(ValueError, match="Cross-project safety violation"):
        ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)


def test_14_retrieval_of_report_from_stored_snapshot(client, sample_investigation_setup):
    """Test 14: Retrieval of report directly from stored snapshot."""
    inv_id = sample_investigation_setup["investigation"].id
    create_resp = client.post(f"/api/v1/investigations/{inv_id}/reports", json={"title": "Snapshot Test"})
    report_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/reports/{report_id}")
    assert get_resp.status_code == 200
    report_data = get_resp.json()

    assert report_data["id"] == report_id
    assert report_data["report_title"] == "Snapshot Test"
    assert "snapshot_payload" in report_data
    assert "financial_summary" in report_data


def test_15_correct_report_version_sequencing(client, sample_investigation_setup):
    """Test 15: Correct report version sequencing and list endpoint ordering."""
    inv_id = sample_investigation_setup["investigation"].id
    # Create version 1
    client.post(f"/api/v1/investigations/{inv_id}/reports", json={"title": "Version 1"})
    # Create version 2
    client.post(f"/api/v1/investigations/{inv_id}/reports", json={"title": "Version 2"})
    # Create version 3
    client.post(f"/api/v1/investigations/{inv_id}/reports", json={"title": "Version 3"})

    list_resp = client.get(f"/api/v1/investigations/{inv_id}/reports")
    assert list_resp.status_code == 200
    reports_list = list_resp.json()

    assert len(reports_list) == 3
    # Ordered descending: v3, v2, v1
    assert reports_list[0]["report_version"] == 3
    assert reports_list[1]["report_version"] == 2
    assert reports_list[2]["report_version"] == 1
