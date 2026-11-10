import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project import Project
from app.models.document import Document
from app.models.review import DocumentFieldReview, FieldReviewAuditLog, ReviewStatus
from app.services.review_service import EvidenceReviewService
from app.services.reconciliation_engine import MultiSourceReconciliationEngine

@pytest.fixture
def review_sample_project(test_db: Session) -> Project:
    project = Project(
        name="Review Test Project",
        code="PRJ-REV-001",
        budget=50000.0,
        currency="USD",
        nas_folder_path="/volume1/finance/review"
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project

@pytest.fixture
def review_sample_document(test_db: Session, review_sample_project: Project) -> Document:
    extracted_data = {
        "status": "EXTRACTED",
        "document_type": "INVOICE",
        "invoice_number": "INV-REV-2026",
        "po_reference": "PO-REV-100",
        "amount": 12500.50,
        "tax_amount": 1250.05,
        "currency": "USD",
        "vendor": "Alpha Tech Supplies",
        "date": "2026-02-15",
        "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "provenance": {
            "source_path": "/volume1/finance/review/INV-REV-2026.pdf",
            "extraction_method": "PDF_TEXT_LAYOUT",
            "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        },
        "field_provenance": {
            "amount": {"value": 12500.50, "source_location": "Line 14"},
            "currency": {"value": "USD", "source_location": "Line 14"},
            "vendor": {"value": "Alpha Tech Supplies", "source_location": "Line 3"},
            "invoice_number": {"value": "INV-REV-2026", "source_location": "Line 2"},
            "po_reference": {"value": "PO-REV-100", "source_location": "Line 5"}
        }
    }
    doc = Document(
        project_id=review_sample_project.id,
        filename="INV-REV-2026.pdf",
        file_path="/volume1/finance/review/INV-REV-2026.pdf",
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data=extracted_data
    )
    test_db.add(doc)
    test_db.commit()
    test_db.refresh(doc)
    return doc


def test_initialization_creates_pending_reviews_without_overwriting(test_db: Session, review_sample_document: Document):
    """Verify initialization creates review records in PENDING status without marking any as verified."""
    reviews = EvidenceReviewService.initialize_document_reviews(test_db, review_sample_document)
    assert len(reviews) >= 5

    amount_review = next((r for r in reviews if r.field_name == "amount"), None)
    assert amount_review is not None
    assert amount_review.status == ReviewStatus.PENDING
    assert amount_review.original_value == 12500.50
    assert amount_review.reviewed_value == 12500.50
    assert amount_review.source_provenance == {"value": 12500.50, "source_location": "Line 14"}
    assert amount_review.original_document_sha256 == review_sample_document.extracted_data["sha256"]

    # Check audit log initialization
    history = EvidenceReviewService.get_document_review_history(test_db, review_sample_document.id)
    assert len(history) >= 5
    init_entry = next((h for h in history if h.field_name == "amount"), None)
    assert init_entry is not None
    assert init_entry.action == "INITIALIZED"
    assert init_entry.new_status == ReviewStatus.PENDING


def test_verification_workflow_preserves_original_value(test_db: Session, review_sample_document: Document):
    """Verify field verification workflow records VERIFIED status, timestamp, notes, and audit history."""
    review = EvidenceReviewService.verify_field(
        db=test_db,
        document_id=review_sample_document.id,
        field_name="amount",
        reviewer_id="auditor_jane",
        notes="Matches signed physical goods receipt note."
    )
    assert review.status == ReviewStatus.VERIFIED
    assert review.original_value == 12500.50
    assert review.reviewed_value == 12500.50
    assert review.reviewer_id == "auditor_jane"
    assert review.review_timestamp is not None
    assert review.reviewer_notes == "Matches signed physical goods receipt note."

    # Document extracted_data must remain completely unmodified
    test_db.refresh(review_sample_document)
    assert review_sample_document.extracted_data["amount"] == 12500.50

    # Verify audit history
    history = EvidenceReviewService.get_document_review_history(test_db, review_sample_document.id)
    latest = next((h for h in history if h.field_name == "amount" and h.action == "VERIFIED"), None)
    assert latest is not None
    assert latest.previous_status == ReviewStatus.PENDING
    assert latest.new_status == ReviewStatus.VERIFIED
    assert latest.reviewer_id == "auditor_jane"


def test_correction_workflow_stores_correction_separately_without_overwriting(test_db: Session, review_sample_document: Document):
    """Verify field correction preserves original extracted value untouched while storing reviewed_value."""
    review = EvidenceReviewService.correct_field(
        db=test_db,
        document_id=review_sample_document.id,
        field_name="amount",
        corrected_value=12000.00,
        reviewer_id="auditor_bob",
        notes="Vendor applied $500.50 retrospective discount."
    )
    assert review.status == ReviewStatus.CORRECTED
    # MANDATORY: Original value is NEVER overwritten
    assert review.original_value == 12500.50
    assert review.reviewed_value == 12000.00
    assert review.reviewer_id == "auditor_bob"
    assert review.reviewer_notes == "Vendor applied $500.50 retrospective discount."

    # Verify audit history contains before and after values
    history = EvidenceReviewService.get_document_review_history(test_db, review_sample_document.id)
    corr_entry = next((h for h in history if h.field_name == "amount" and h.action == "CORRECTED"), None)
    assert corr_entry is not None
    assert corr_entry.previous_value == 12500.50
    assert corr_entry.new_value == 12000.00


def test_rejection_workflow_excludes_value_with_mandatory_reason(test_db: Session, review_sample_document: Document):
    """Verify field rejection zeroes/nullifies reviewed value and enforces mandatory rationale."""
    # Rejection without reason fails with HTTP 422
    with pytest.raises(Exception):
        EvidenceReviewService.reject_field(
            db=test_db,
            document_id=review_sample_document.id,
            field_name="amount",
            reason=""
        )

    review = EvidenceReviewService.reject_field(
        db=test_db,
        document_id=review_sample_document.id,
        field_name="amount",
        reviewer_id="auditor_jane",
        reason="Erroneously scanned pro-forma quote, not an actual invoice."
    )
    assert review.status == ReviewStatus.REJECTED
    assert review.original_value == 12500.50
    assert review.reviewed_value is None  # Excluded from calculations
    assert review.reviewer_notes == "Erroneously scanned pro-forma quote, not an actual invoice."


def test_clarification_workflow_sets_requires_clarification(test_db: Session, review_sample_document: Document):
    """Verify clarification request requires a question and updates status."""
    with pytest.raises(Exception):
        EvidenceReviewService.request_clarification(
            db=test_db,
            document_id=review_sample_document.id,
            field_name="vendor",
            clarification_question=""
        )

    review = EvidenceReviewService.request_clarification(
        db=test_db,
        document_id=review_sample_document.id,
        field_name="vendor",
        reviewer_id="auditor_jane",
        clarification_question="Is Alpha Tech Supplies a subsidiary of Alpha Corp?"
    )
    assert review.status == ReviewStatus.REQUIRES_CLARIFICATION
    assert review.reviewer_notes == "Is Alpha Tech Supplies a subsidiary of Alpha Corp?"


def test_document_review_summary_metrics(test_db: Session, review_sample_document: Document):
    """Verify summary metrics correctly count pending, verified, corrected, rejected, clarification."""
    EvidenceReviewService.verify_field(test_db, review_sample_document.id, "currency", "auditor_1", "OK")
    EvidenceReviewService.correct_field(test_db, review_sample_document.id, "amount", 10000.0, "auditor_1", "Discounted")
    EvidenceReviewService.reject_field(test_db, review_sample_document.id, "tax_amount", "auditor_1", "Exempt NGO grant")
    EvidenceReviewService.request_clarification(test_db, review_sample_document.id, "vendor", "auditor_1", "Subsidiary check")

    summary = EvidenceReviewService.get_document_review_summary(test_db, review_sample_document.id)
    assert summary["verified_count"] == 1
    assert summary["corrected_count"] == 1
    assert summary["rejected_count"] == 1
    assert summary["clarification_count"] == 1
    assert summary["is_fully_reviewed"] is False  # Because clarification is outstanding


def test_reconciliation_integration_with_human_correction(test_db: Session, review_sample_project: Project):
    """
    Verify that human review correction flows into reconciliation:
    PO ($10,000) vs Invoice ($12,000 original).
    Auditor corrects invoice to $10,000 (applying approved amendment).
    Reconciliation with review integration must match without unauthorized discrepancy!
    """
    po = Document(
        project_id=review_sample_project.id,
        filename="PO-100.pdf",
        file_path="/volume1/finance/review/PO-100.pdf",
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-100", "amount": 10000.0, "currency": "USD", "vendor": "Alpha Tech"}
    )
    inv = Document(
        project_id=review_sample_project.id,
        filename="INV-100.pdf",
        file_path="/volume1/finance/review/INV-100.pdf",
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-100", "invoice_number": "INV-100", "amount": 12000.0, "currency": "USD", "vendor": "Alpha Tech"}
    )
    rec = Document(
        project_id=review_sample_project.id,
        filename="REC-100.pdf",
        file_path="/volume1/finance/review/REC-100.pdf",
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_reference": "INV-100", "receipt_id": "REC-100", "amount": 10000.0, "currency": "USD", "status": "EXTRACTED"}
    )
    test_db.add_all([po, inv, rec])
    test_db.commit()

    # 1. Before review: Overbilling (+2,000) produces CONFIRMED_DISCREPANCY
    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/finance/review", db=test_db)
    assert entry.reconciliation_status == "VARIANCE_HOLD"
    assert finding is not None
    assert finding.classification == "CONFIRMED_DISCREPANCY"

    # 2. Human auditor corrects invoice amount to 10,000.0 based on verified credit memorandum
    EvidenceReviewService.correct_field(
        db=test_db,
        document_id=inv.id,
        field_name="amount",
        corrected_value=10000.0,
        reviewer_id="auditor_chief",
        notes="Substantiated by vendor credit note CM-09."
    )
    EvidenceReviewService.verify_field(
        db=test_db,
        document_id=inv.id,
        field_name="currency",
        reviewer_id="auditor_chief",
        notes="Verified USD"
    )

    # 3. After human review: Effective reconciliation reflects corrected amount
    entry_after, finding_after = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/finance/review", db=test_db)
    assert entry_after.reconciliation_status == "RECONCILED_MATCH"
    assert finding_after is None
    assert entry_after.paid_amount == 10000.0
    # Original amount preserved in invoice breakdown
    inv_bd = entry_after.multiple_invoices_breakdown[0]
    assert inv_bd["amount"] == 10000.0
    assert inv_bd["original_amount"] == 12000.0
    assert inv_bd["is_human_corrected"] is True


def test_reconciliation_integration_human_verification_resolves_untrusted_sidecar(test_db: Session, review_sample_project: Project):
    """
    Verify that an untrusted sidecar document (normally UNVERIFIED) reconciles cleanly
    when its primary fields (amount and currency) are human-verified by an auditor.
    """
    po = Document(
        project_id=review_sample_project.id,
        filename="PO-200.pdf",
        file_path="/volume1/finance/review/PO-200.pdf",
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-200", "amount": 5000.0, "currency": "USD", "vendor": "Beta Logistics"}
    )
    # Scanned PDF invoice using untrusted sidecar metadata
    inv = Document(
        project_id=review_sample_project.id,
        filename="INV-200.pdf",
        file_path="/volume1/finance/review/INV-200.pdf",
        document_type="INVOICE",
        extraction_status="UNVERIFIED",
        extracted_data={
            "po_reference": "PO-200",
            "invoice_number": "INV-200",
            "amount": 5000.0,
            "currency": "USD",
            "vendor": "Beta Logistics",
            "requires_human_verification": True,
            "provenance": {"extraction_method": "UNTRUSTED_SIDECAR"}
        }
    )
    rec = Document(
        project_id=review_sample_project.id,
        filename="REC-200.pdf",
        file_path="/volume1/finance/review/REC-200.pdf",
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_reference": "INV-200", "receipt_id": "REC-200", "amount": 5000.0, "currency": "USD", "status": "EXTRACTED"}
    )
    test_db.add_all([po, inv, rec])
    test_db.commit()

    # 1. Before human review: UNVERIFIED finding
    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/finance/review", db=test_db)
    assert entry.reconciliation_status == "UNVERIFIED"
    assert finding is not None
    assert finding.classification == "UNVERIFIED"

    # 2. Human auditor verifies amount and currency from physical hardcopy
    EvidenceReviewService.verify_field(test_db, inv.id, "amount", "auditor_sarah", "Hardcopy matches $5,000.00")
    EvidenceReviewService.verify_field(test_db, inv.id, "currency", "auditor_sarah", "Hardcopy confirms USD")

    # 3. After human review: Document is accepted as verified evidence
    entry_after, finding_after = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/finance/review", db=test_db)
    assert entry_after.reconciliation_status == "RECONCILED_MATCH"
    assert finding_after is None
    assert entry_after.paid_amount == 5000.0


def test_api_evidence_review_endpoints(test_db: Session, review_sample_document: Document):
    """Test all API endpoints for review workflows."""
    client = TestClient(app)

    # 1. Initialize reviews
    resp_init = client.post(f"/api/v1/documents/{review_sample_document.id}/reviews/initialize")
    assert resp_init.status_code == 200
    fields = resp_init.json()
    assert len(fields) >= 5

    # 2. Get document reviews summary
    resp_summary = client.get(f"/api/v1/documents/{review_sample_document.id}/reviews")
    assert resp_summary.status_code == 200
    summary = resp_summary.json()
    assert summary["document_id"] == review_sample_document.id
    assert summary["pending_count"] >= 5

    # 3. Verify a field
    resp_verify = client.post(
        f"/api/v1/documents/{review_sample_document.id}/reviews/currency/verify",
        json={"reviewer_id": "auditor_api", "notes": "Currency ISO code verified"}
    )
    assert resp_verify.status_code == 200
    assert resp_verify.json()["status"] == "VERIFIED"

    # 4. Correct a field
    resp_correct = client.post(
        f"/api/v1/documents/{review_sample_document.id}/reviews/amount/correct",
        json={"corrected_value": 11500.0, "reviewer_id": "auditor_api", "notes": "Tax deducted"}
    )
    assert resp_correct.status_code == 200
    assert resp_correct.json()["status"] == "CORRECTED"
    assert resp_correct.json()["original_value"] == 12500.50
    assert resp_correct.json()["reviewed_value"] == 11500.0

    # 5. Reject a field with validation
    resp_reject_invalid = client.post(
        f"/api/v1/documents/{review_sample_document.id}/reviews/vendor/reject",
        json={"reason": ""}
    )
    assert resp_reject_invalid.status_code == 422

    resp_reject = client.post(
        f"/api/v1/documents/{review_sample_document.id}/reviews/tax_amount/reject",
        json={"reason": "Tax not payable under grant exemption agreement"}
    )
    assert resp_reject.status_code == 200
    assert resp_reject.json()["status"] == "REJECTED"
    assert resp_reject.json()["reviewed_value"] is None

    # 6. Request clarification
    resp_clarify = client.post(
        f"/api/v1/documents/{review_sample_document.id}/reviews/vendor/clarify",
        json={"clarification_question": "Confirm vendor legal entity registration"}
    )
    assert resp_clarify.status_code == 200
    assert resp_clarify.json()["status"] == "REQUIRES_CLARIFICATION"

    # 7. Get specific field
    resp_field = client.get(f"/api/v1/documents/{review_sample_document.id}/reviews/amount")
    assert resp_field.status_code == 200
    assert resp_field.json()["reviewed_value"] == 11500.0

    # 8. Get review history
    resp_history = client.get(f"/api/v1/documents/{review_sample_document.id}/reviews/history")
    assert resp_history.status_code == 200
    history = resp_history.json()
    assert len(history) >= 4

    # 9. List pending reviews
    resp_pending = client.get("/api/v1/reviews/pending")
    assert resp_pending.status_code == 200
    assert isinstance(resp_pending.json(), list)

    # 10. Non-existent document returns 404
    resp_404 = client.get("/api/v1/documents/99999/reviews")
    assert resp_404.status_code == 404
