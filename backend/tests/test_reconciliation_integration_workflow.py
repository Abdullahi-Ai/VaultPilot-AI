import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project import Project
from app.models.document import Document
from app.models.investigation import Investigation
from app.models.report import InvestigationReport
from app.services.review_service import EvidenceReviewService
from app.services.investigation_service import InvestigationService
from app.services.report_service import ReportService

@pytest.fixture
def workflow_setup(test_db: Session, tmp_path):
    project = Project(
        name="Human Verification NGO Project",
        code="PRJ-HVR-2026",
        budget=80000.0,
        currency="USD",
        nas_folder_path=str(tmp_path)
    )
    test_db.add(project)
    test_db.commit()

    investigation = Investigation(
        project_id=project.id,
        title="Human Verification Workflow Audit",
        scope_path=str(tmp_path),
        status="IN_PROGRESS",
        created_at=datetime.datetime.utcnow()
    )
    test_db.add(investigation)
    test_db.commit()

    return project, investigation, tmp_path


def test_1_resolution_of_unverified_finding_after_human_verification(test_db: Session, workflow_setup):
    """
    1. Unverified sidecar document creates UNVERIFIED finding and holds payment credit.
    2. Auditor verifies amount and currency from physical voucher.
    3. Re-reconciliation clears UNVERIFIED finding and credits verified spend.
    """
    project, inv, tmp_path = workflow_setup

    po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-HVR-01.txt",
        file_path=str(tmp_path / "PO-HVR-01.txt"),
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-HVR-01", "amount": 7500.0, "currency": "USD", "vendor": "Global Solar"}
    )
    # Unverified scan with sidecar
    inv_doc = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-HVR-01.pdf",
        file_path=str(tmp_path / "INV-HVR-01.pdf"),
        document_type="INVOICE",
        extraction_status="UNVERIFIED",
        extracted_data={
            "po_reference": "PO-HVR-01",
            "invoice_number": "INV-HVR-01",
            "amount": 7500.0,
            "currency": "USD",
            "vendor": "Global Solar",
            "requires_human_verification": True,
            "provenance": {"extraction_method": "UNTRUSTED_SIDECAR"}
        }
    )
    rec = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="REC-HVR-01.txt",
        file_path=str(tmp_path / "REC-HVR-01.txt"),
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_reference": "INV-HVR-01", "receipt_id": "REC-HVR-01", "amount": 7500.0, "currency": "USD", "status": "EXTRACTED"}
    )
    test_db.add_all([po, inv_doc, rec])
    test_db.commit()

    # Initial reconciliation run
    InvestigationService.reconcile_investigation(test_db, inv.id)
    assert inv.status == "COMPLETED"
    assert inv.verified_totals.get("USD", 0.0) == 0.0
    unverified_f = next((f for f in inv.findings if f.classification == "UNVERIFIED"), None)
    assert unverified_f is not None

    # Auditor verifies amount and currency from physical documentation
    EvidenceReviewService.verify_field(test_db, inv_doc.id, "amount", "auditor_elena", "Verified against paper receipt")
    EvidenceReviewService.verify_field(test_db, inv_doc.id, "currency", "auditor_elena", "Verified USD")

    # Re-evaluate reconciliation via API/Service
    InvestigationService.reconcile_investigation(test_db, inv.id)
    test_db.refresh(inv)

    # UNVERIFIED finding is resolved
    unverified_f_after = next((f for f in inv.findings if f.classification == "UNVERIFIED"), None)
    assert unverified_f_after is None
    # Verified spend is credited because matching payment receipt exists
    assert inv.verified_totals.get("USD") == 7500.0
    ledger = inv.ledger_entries[0]
    assert ledger.reconciliation_status == "RECONCILED_MATCH"


def test_2_correction_of_discrepancy_with_supporting_evidence(test_db: Session, workflow_setup):
    """
    PO $10,000 vs Invoice $12,000 generates CONFIRMED_DISCREPANCY.
    Auditor corrects invoice to $10,000 based on verified credit memo CM-01.
    Re-reconciliation resolves discrepancy and preserves original amount in breakdown.
    If corrected amount still exceeds PO (e.g. $11,000), discrepancy remains.
    """
    project, inv, tmp_path = workflow_setup

    po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-DISC-02.txt",
        file_path=str(tmp_path / "PO-DISC-02.txt"),
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-DISC-02", "amount": 10000.0, "currency": "USD", "vendor": "Machinery Corp"}
    )
    inv_doc = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-DISC-02.txt",
        file_path=str(tmp_path / "INV-DISC-02.txt"),
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-DISC-02", "invoice_number": "INV-DISC-02", "amount": 12000.0, "currency": "USD", "vendor": "Machinery Corp"}
    )
    rec = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="REC-DISC-02.txt",
        file_path=str(tmp_path / "REC-DISC-02.txt"),
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_reference": "INV-DISC-02", "receipt_id": "REC-DISC-02", "amount": 10000.0, "currency": "USD", "status": "EXTRACTED"}
    )
    test_db.add_all([po, inv_doc, rec])
    test_db.commit()

    # Initial reconciliation: Overbilling (+2,000) generates CONFIRMED_DISCREPANCY
    InvestigationService.reconcile_investigation(test_db, inv.id)
    assert any(f.classification == "CONFIRMED_DISCREPANCY" for f in inv.findings)

    # Case A: Partial correction that STILL exceeds PO ($11,000 > $10,000) does NOT clear discrepancy
    EvidenceReviewService.correct_field(test_db, inv_doc.id, "amount", 11000.0, "auditor_1", "Partial adjustment")
    InvestigationService.reconcile_investigation(test_db, inv.id)
    test_db.refresh(inv)
    assert any(f.classification == "CONFIRMED_DISCREPANCY" for f in inv.findings)

    # Case B: Full correction matching PO authorization ($10,000) based on credit note CM-01
    EvidenceReviewService.correct_field(test_db, inv_doc.id, "amount", 10000.0, "auditor_1", "Credit note CM-01 covers 2,000 discount")
    InvestigationService.reconcile_investigation(test_db, inv.id)
    test_db.refresh(inv)

    assert not any(f.classification == "CONFIRMED_DISCREPANCY" for f in inv.findings)
    ledger = inv.ledger_entries[0]
    assert ledger.reconciliation_status == "RECONCILED_MATCH"
    # Breakdown preserves original extracted amount
    assert ledger.multiple_invoices_breakdown[0]["amount"] == 10000.0
    assert ledger.multiple_invoices_breakdown[0]["original_amount"] == 12000.0
    assert ledger.multiple_invoices_breakdown[0]["is_human_corrected"] is True


def test_3_verified_invoice_does_not_prove_payment(test_db: Session, workflow_setup):
    """
    Requirement 2: A verified invoice must NOT automatically establish verified expenditure.
    Payment credit requires adequate supporting disbursement evidence.
    """
    project, inv, tmp_path = workflow_setup

    po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-UNPAID-01.txt",
        file_path=str(tmp_path / "PO-UNPAID-01.txt"),
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-UNPAID-01", "amount": 15000.0, "currency": "USD", "vendor": "Supplies Ltd"}
    )
    inv_doc = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-UNPAID-01.txt",
        file_path=str(tmp_path / "INV-UNPAID-01.txt"),
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-UNPAID-01", "invoice_number": "INV-UNPAID-01", "amount": 15000.0, "currency": "USD", "vendor": "Supplies Ltd"}
    )
    test_db.add_all([po, inv_doc])
    test_db.commit()

    # Human auditor verifies the invoice
    EvidenceReviewService.verify_field(test_db, inv_doc.id, "amount", "auditor_1", "Invoice confirmed valid")
    EvidenceReviewService.verify_field(test_db, inv_doc.id, "currency", "auditor_1", "USD confirmed")

    InvestigationService.reconcile_investigation(test_db, inv.id)
    test_db.refresh(inv)

    # CRITICAL: Missing receipt means NO verified expenditure credit
    assert inv.verified_totals.get("USD", 0.0) == 0.0
    ledger = inv.ledger_entries[0]
    assert ledger.reconciliation_status == "MISSING_RECEIPT"
    assert ledger.paid_amount in (None, 0.0)
    assert any(f.classification == "MISSING_EVIDENCE" for f in inv.findings)


def test_4_rejection_strictly_excludes_values_from_reconciliation(test_db: Session, workflow_setup):
    """
    Requirement 2: Rejected fields must remain excluded from verified calculations.
    """
    project, inv, tmp_path = workflow_setup

    po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-REJ-01.txt",
        file_path=str(tmp_path / "PO-REJ-01.txt"),
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-REJ-01", "amount": 5000.0, "currency": "USD", "vendor": "Office Store"}
    )
    inv_doc = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-REJ-01.txt",
        file_path=str(tmp_path / "INV-REJ-01.txt"),
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-REJ-01", "invoice_number": "INV-REJ-01", "amount": 5000.0, "currency": "USD", "vendor": "Office Store"}
    )
    rec = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="REC-REJ-01.txt",
        file_path=str(tmp_path / "REC-REJ-01.txt"),
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_reference": "INV-REJ-01", "receipt_id": "REC-REJ-01", "amount": 5000.0, "currency": "USD", "status": "EXTRACTED"}
    )
    test_db.add_all([po, inv_doc, rec])
    test_db.commit()

    # Reject invoice amount with mandatory justification
    EvidenceReviewService.reject_field(test_db, inv_doc.id, "amount", "auditor_1", "Duplicate forged billing")

    InvestigationService.reconcile_investigation(test_db, inv.id)
    test_db.refresh(inv)

    # Excluded from verified calculations
    assert inv.verified_totals.get("USD", 0.0) == 0.0


def test_5_incomplete_review_does_not_silently_verify(test_db: Session, workflow_setup):
    """
    Requirement 2: Pending and incomplete reviews must remain unverified.
    Only currency verified, amount still pending.
    """
    project, inv, tmp_path = workflow_setup

    inv_doc = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-INC-01.pdf",
        file_path=str(tmp_path / "INV-INC-01.pdf"),
        document_type="INVOICE",
        extraction_status="UNVERIFIED",
        extracted_data={
            "invoice_number": "INV-INC-01",
            "amount": 4000.0,
            "currency": "USD",
            "requires_human_verification": True,
            "provenance": {"extraction_method": "UNTRUSTED_SIDECAR"}
        }
    )
    test_db.add(inv_doc)
    test_db.commit()

    # Auditor only verifies currency, leaves amount PENDING
    EvidenceReviewService.verify_field(test_db, inv_doc.id, "currency", "auditor_1", "USD OK")

    InvestigationService.reconcile_investigation(test_db, inv.id)
    test_db.refresh(inv)

    # Must NOT silently verify
    unverified_f = next((f for f in inv.findings if f.classification == "UNVERIFIED"), None)
    assert unverified_f is not None


def test_6_preservation_of_sealed_reports_and_audit_history(test_db: Session, workflow_setup):
    """
    Requirement 1: Re-reconciliation must NOT overwrite sealed investigation reports
    or historical reconciliation evidence.
    """
    project, inv, tmp_path = workflow_setup

    po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-SEAL-01.txt",
        file_path=str(tmp_path / "PO-SEAL-01.txt"),
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-SEAL-01", "amount": 6000.0, "currency": "USD", "vendor": "Safe Logistics"}
    )
    inv_doc = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-SEAL-01.txt",
        file_path=str(tmp_path / "INV-SEAL-01.txt"),
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-SEAL-01", "invoice_number": "INV-SEAL-01", "amount": 7000.0, "currency": "USD", "vendor": "Safe Logistics"}
    )
    test_db.add_all([po, inv_doc])
    test_db.commit()

    # Initial reconciliation
    InvestigationService.reconcile_investigation(test_db, inv.id)

    # Seal an official report snapshot
    sealed_rep = ReportService.create_report_snapshot(test_db, inv.id, "Pre-Review Sealed Audit Report")
    initial_hash = sealed_rep.snapshot_integrity_hash
    initial_findings_count = len(sealed_rep.snapshot_payload["findings_snapshot"])

    # Auditor performs review corrections
    EvidenceReviewService.correct_field(test_db, inv_doc.id, "amount", 6000.0, "auditor_chief", "Amended to match PO")

    # Trigger re-reconciliation
    InvestigationService.reconcile_investigation(test_db, inv.id)

    # CRITICAL CHECK: Sealed report snapshot is 100% UNCHANGED and preserved
    test_db.refresh(sealed_rep)
    assert sealed_rep.snapshot_integrity_hash == initial_hash
    assert len(sealed_rep.snapshot_payload["findings_snapshot"]) == initial_findings_count
    assert sealed_rep.snapshot_payload["findings_snapshot"][0]["classification"] == "CONFIRMED_DISCREPANCY"

    # Audit history preserved
    history = EvidenceReviewService.get_document_review_history(test_db, inv_doc.id)
    assert len(history) >= 2


def test_7_api_reconcile_investigation_endpoint(test_db: Session, workflow_setup):
    """
    Test POST /api/v1/investigations/{id}/reconcile and POST /api/v1/documents/{id}/reconcile.
    """
    client = TestClient(app)
    project, inv, tmp_path = workflow_setup

    po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-API-01.txt",
        file_path=str(tmp_path / "PO-API-01.txt"),
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-API-01", "amount": 3000.0, "currency": "USD", "vendor": "API Tech"}
    )
    test_db.add(po)
    test_db.commit()

    # Endpoint 1: POST /api/v1/investigations/{id}/reconcile
    resp1 = client.post(f"/api/v1/investigations/{inv.id}/reconcile")
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "COMPLETED"

    # Endpoint 2: POST /api/v1/documents/{doc_id}/reconcile
    resp2 = client.post(f"/api/v1/documents/{po.id}/reconcile")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "SUCCESS"
    assert resp2.json()["investigation_id"] == inv.id
