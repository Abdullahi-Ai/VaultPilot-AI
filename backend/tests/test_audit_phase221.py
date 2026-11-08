import pytest
from app.models.document import Document
from app.models.project import Project
from app.models.ledger import EvidenceLedgerEntry
from app.services.reconciliation_engine import MultiSourceReconciliationEngine, normalize_currency
from app.services.investigation_service import InvestigationService

def test_remediated_missing_currency_does_not_default_to_usd():
    """
    Requirement 1: Missing currency does not default to USD.
    When 'currency' key is omitted, entry.currency must be None, not 'USD'.
    Entry must be marked UNVERIFIED with human review required.
    """
    po = Document(
        id=301, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-NOCURR.pdf", file_path="/vol/p1/PO-NOCURR.pdf",
        extracted_data={"po_reference": "PO-NOCURR", "amount": 1000.0, "vendor": "Local NGO"} # no 'currency'
    )
    inv = Document(
        id=302, project_id=1, document_type="INVOICE",
        filename="INV-NOCURR.pdf", file_path="/vol/p1/INV-NOCURR.pdf",
        extracted_data={"invoice_number": "INV-NOCURR", "po_reference": "PO-NOCURR", "amount": 1000.0, "vendor": "Local NGO"}
    )
    group = MultiSourceReconciliationEngine.match_documents([po], [inv], [])[0]
    assert group["match_confidence"] == "UNVERIFIED"
    assert group["requires_human_review"] is True

    entry, finding = MultiSourceReconciliationEngine.reconcile_group(group, investigation_id=1, target_scope="/vol/p1")
    assert entry.currency is None
    assert entry.reconciliation_status == "UNVERIFIED"
    assert entry.requires_human_review is True
    assert finding is not None
    assert finding.classification == "UNVERIFIED"
    assert finding.title == "Undocumented or Invalid Currency Specification"

def test_remediated_explicit_null_currency_does_not_crash():
    """
    Requirement 2: Explicit null currency does not crash with AttributeError.
    """
    po = Document(
        id=303, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-NULL.pdf", file_path="/vol/p1/PO-NULL.pdf",
        extracted_data={"po_reference": "PO-NULL", "amount": 1000.0, "currency": None, "vendor": "Local NGO"}
    )
    inv = Document(
        id=304, project_id=1, document_type="INVOICE",
        filename="INV-NULL.pdf", file_path="/vol/p1/INV-NULL.pdf",
        extracted_data={"invoice_number": "INV-NULL", "po_reference": "PO-NULL", "amount": 1000.0, "currency": None, "vendor": "Local NGO"}
    )
    # Must not raise AttributeError
    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [])
    assert len(groups) == 1
    assert groups[0]["match_confidence"] == "UNVERIFIED"
    assert groups[0]["requires_human_review"] is True

    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/vol/p1")
    assert entry.currency is None
    assert entry.reconciliation_status == "UNVERIFIED"
    assert finding is not None
    assert finding.classification == "UNVERIFIED"

def test_remediated_empty_and_whitespace_currency_rejected_safely():
    """
    Requirement 3: Empty string and whitespace-only currencies are rejected safely.
    """
    assert normalize_currency("") is None
    assert normalize_currency("   ") is None
    assert normalize_currency("\t\n") is None
    assert normalize_currency(None) is None
    assert normalize_currency("$") is None
    assert normalize_currency("123") is None
    assert normalize_currency("USD") == "USD"
    assert normalize_currency(" eur ") == "EUR"
    assert normalize_currency("kes") == "KES"

def test_remediated_invalid_currency_not_aggregated():
    """
    Requirement 4: Invalid/missing currency amounts are not aggregated into verified totals.
    """
    entry = EvidenceLedgerEntry(
        id=1,
        reconciliation_status="RECONCILED_MATCH", # even if marked match
        paid_amount=5000.0,
        currency=None # missing currency
    )
    verified_spend = {}
    curr = normalize_currency(entry.currency)
    if curr:
        verified_spend[curr] = verified_spend.get(curr, 0.0) + entry.paid_amount

    # Nothing should be aggregated
    assert len(verified_spend) == 0

def test_remediated_valid_currencies_remain_segregated():
    """
    Requirement 5: Valid currencies remain strictly segregated.
    """
    po_usd = Document(
        id=305, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-USD.pdf", file_path="/vol/p1/PO-USD.pdf",
        extracted_data={"po_reference": "PO-USD", "amount": 1000.0, "currency": "USD", "vendor": "Global NGO"}
    )
    inv_eur = Document(
        id=306, project_id=1, document_type="INVOICE",
        filename="INV-EUR.pdf", file_path="/vol/p1/INV-EUR.pdf",
        extracted_data={"invoice_number": "INV-EUR", "po_reference": "PO-USD", "amount": 1000.0, "currency": "EUR", "vendor": "Global NGO"}
    )
    group = MultiSourceReconciliationEngine.match_documents([po_usd], [inv_eur], [])[0]
    assert group["match_confidence"] == "CONFLICTING_EVIDENCE"

    entry, finding = MultiSourceReconciliationEngine.reconcile_group(group, investigation_id=1, target_scope="/vol/p1")
    assert entry.reconciliation_status == "VARIANCE_HOLD"
    assert finding is not None
    assert finding.classification == "POTENTIAL_ANOMALY"
    assert "Multi-Currency Mismatch" in finding.title

def test_remediated_genuine_supported_overpayment():
    """
    Requirement 6: Genuine supported overpayment creates POTENTIAL_ANOMALY finding and VARIANCE_HOLD.
    Example: Invoice USD 1,000, Receipts USD 1,500 -> Difference +500.
    """
    po = Document(
        id=101, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-101.pdf", file_path="/vol/p1/PO-101.pdf",
        extracted_data={"po_reference": "PO-101", "amount": 1000.0, "currency": "USD", "vendor": "SolarTech"}
    )
    inv = Document(
        id=102, project_id=1, document_type="INVOICE",
        filename="INV-102.pdf", file_path="/vol/p1/INV-102.pdf",
        extracted_data={"invoice_number": "INV-102", "po_reference": "PO-101", "amount": 1000.0, "currency": "USD", "vendor": "SolarTech"}
    )
    rec = Document(
        id=103, project_id=1, document_type="RECEIPT",
        filename="REC-103.pdf", file_path="/vol/p1/REC-103.pdf",
        extracted_data={"receipt_id": "REC-103", "invoice_reference": "INV-102", "amount": 1500.0, "currency": "USD", "payee": "SolarTech"}
    )

    group = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec])[0]
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(group, investigation_id=1, target_scope="/vol/p1")

    assert entry.reconciliation_status == "VARIANCE_HOLD"
    assert entry.variance_amount == 500.0
    assert entry.paid_amount == 1500.0
    assert entry.requires_human_review is True
    assert finding is not None
    assert finding.classification == "POTENTIAL_ANOMALY"
    assert finding.title == "Disbursement Receipts Exceed Invoiced Amount"
    assert "+500.00 USD" in finding.comparison_details["calculation"]
    # Check that fraud is NOT accused
    assert "fraud" not in finding.variance_explanation.lower()
    assert "misconduct" not in finding.variance_explanation.lower()

def test_remediated_duplicate_receipts_do_not_create_false_overpayment():
    """
    Requirement 7: Duplicate receipts do not create false overpayments; flagged as conflicting evidence.
    """
    po = Document(
        id=104, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-104.pdf", file_path="/vol/p1/PO-104.pdf",
        extracted_data={"po_reference": "PO-104", "amount": 1000.0, "currency": "USD", "vendor": "SolarTech"}
    )
    inv = Document(
        id=105, project_id=1, document_type="INVOICE",
        filename="INV-105.pdf", file_path="/vol/p1/INV-105.pdf",
        extracted_data={"invoice_number": "INV-105", "po_reference": "PO-104", "amount": 1000.0, "currency": "USD", "vendor": "SolarTech"}
    )
    # Two identical receipts with same receipt_id
    rec1 = Document(
        id=106, project_id=1, document_type="RECEIPT",
        filename="REC-106.pdf", file_path="/vol/p1/REC-106.pdf",
        extracted_data={"receipt_id": "REC-DUP", "invoice_reference": "INV-105", "amount": 1000.0, "currency": "USD"}
    )
    rec2 = Document(
        id=107, project_id=1, document_type="RECEIPT",
        filename="REC-106_copy.pdf", file_path="/vol/p1/REC-106_copy.pdf",
        extracted_data={"receipt_id": "REC-DUP", "invoice_reference": "INV-105", "amount": 1000.0, "currency": "USD"}
    )

    group = {
        "po_doc": po,
        "invoice_docs": [inv],
        "receipt_docs": [rec1, rec2],
        "match_confidence": "EXACT_MATCH",
        "requires_human_review": False
    }
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(group, investigation_id=1, target_scope="/vol/p1")

    assert entry.match_confidence == "CONFLICTING_EVIDENCE"
    assert entry.requires_human_review is True
    assert finding is not None
    assert finding.title == "Duplicate Payment Receipt References in Payment Proof"

def test_remediated_ambiguous_payment_allocation():
    """
    Requirement 8: Ambiguous allocations require human review and mark UNVERIFIED.
    """
    po = Document(
        id=108, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-108.pdf", file_path="/vol/p1/PO-108.pdf",
        extracted_data={"po_reference": "PO-108", "amount": 1000.0, "currency": "USD", "vendor": "SolarTech"}
    )
    inv = Document(
        id=109, project_id=1, document_type="INVOICE",
        filename="INV-109.pdf", file_path="/vol/p1/INV-109.pdf",
        extracted_data={"invoice_number": "INV-109", "amount": 1000.0, "currency": "USD", "vendor": "SolarTech"}
    )
    rec = Document(
        id=110, project_id=1, document_type="RECEIPT",
        filename="REC-110.pdf", file_path="/vol/p1/REC-110.pdf",
        extracted_data={"receipt_id": "REC-110", "amount": 1500.0, "currency": "USD", "payee": "SolarTech"}
    )

    # Group matched with PROBABLE_MATCH (vendor matching only, no explicit refs)
    group = {
        "po_doc": po,
        "invoice_docs": [inv],
        "receipt_docs": [rec],
        "match_confidence": "PROBABLE_MATCH",
        "requires_human_review": True
    }
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(group, investigation_id=1, target_scope="/vol/p1")

    assert entry.reconciliation_status == "UNVERIFIED"
    assert entry.requires_human_review is True
    assert finding is not None
    assert finding.classification == "UNVERIFIED"
    assert "Ambiguous Payment Allocation" in finding.title

def test_remediated_standalone_receipt_unapplied_status():
    """
    Requirement 9: Standalone receipts generate MISSING_EVIDENCE finding and UNAPPLIED_RECEIPT status.
    """
    rec = Document(
        id=201, project_id=1, document_type="RECEIPT",
        filename="REC-STANDALONE.pdf", file_path="/vol/p1/REC-STANDALONE.pdf",
        extracted_data={"receipt_id": "REC-STANDALONE", "amount": 750.0, "currency": "USD", "payee": "Consultant"}
    )

    matched_groups = MultiSourceReconciliationEngine.match_documents([], [], [rec])
    assert len(matched_groups) == 1
    assert matched_groups[0]["match_confidence"] == "UNMATCHED"

    entry, finding = MultiSourceReconciliationEngine.reconcile_group(matched_groups[0], investigation_id=1, target_scope="/vol/p1")
    assert entry.reconciliation_status == "UNAPPLIED_RECEIPT"
    assert entry.paid_amount == 750.0
    assert entry.currency == "USD"
    assert entry.requires_human_review is True
    assert finding is not None
    assert finding.classification == "MISSING_EVIDENCE"
    assert finding.title == "Disbursement Receipt Without Supporting Invoice or Purchase Order"
    assert "does not claim that the payment was unauthorized" in finding.variance_explanation

def test_remediated_credit_note_detected_and_flagged():
    """
    Requirement 10: Credit notes / negative invoice amounts are detected and require human review.
    """
    po = Document(
        id=401, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-401.pdf", file_path="/vol/p1/PO-401.pdf",
        extracted_data={"po_reference": "PO-401", "amount": 1000.0, "currency": "USD", "vendor": "VendorA"}
    )
    inv1 = Document(
        id=402, project_id=1, document_type="INVOICE",
        filename="INV-402.pdf", file_path="/vol/p1/INV-402.pdf",
        extracted_data={"invoice_number": "INV-402", "po_reference": "PO-401", "amount": 1000.0, "currency": "USD", "vendor": "VendorA"}
    )
    inv_credit = Document(
        id=403, project_id=1, document_type="INVOICE",
        filename="INV-CREDIT.pdf", file_path="/vol/p1/INV-CREDIT.pdf",
        extracted_data={"invoice_number": "INV-CREDIT", "po_reference": "PO-401", "amount": -200.0, "currency": "USD", "vendor": "VendorA"}
    )

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv1, inv_credit], [])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/vol/p1")

    assert entry.invoice_amount == 800.0
    assert entry.requires_human_review is True
    assert "credit adjustment" in entry.human_review_reason.lower()
    assert any(b.get("is_credit_adjustment") is True for b in entry.multiple_invoices_breakdown)

def test_remediated_identical_amount_matching_refusal():
    """
    Requirement 11: Matching is never performed solely on amount equality.
    """
    po = Document(
        id=501, project_id=1, document_type="PURCHASE_ORDER",
        filename="PO-BUILDING.pdf", file_path="/vol/p1/PO-BUILDING.pdf",
        extracted_data={"po_reference": "PO-501", "amount": 5000.0, "currency": "USD", "vendor": "Builder Corp"}
    )
    inv = Document(
        id=502, project_id=1, document_type="INVOICE",
        filename="INV-CATERING.pdf", file_path="/vol/p1/INV-CATERING.pdf",
        extracted_data={"invoice_number": "INV-999", "po_reference": "PO-DIFFERENT", "amount": 5000.0, "currency": "USD", "vendor": "Catering Ltd"}
    )

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [])
    assert len(groups) == 2
    assert groups[0]["match_confidence"] == "UNMATCHED"
    assert groups[1]["match_confidence"] == "UNMATCHED"

def test_remediated_project_report_deduplication():
    """
    Requirement 12: Project Financial Report Context Reconciler deduplication.
    """
    report = Document(
        id=601, project_id=1, document_type="FINANCIAL_REPORT",
        filename="Q1_Report.pdf", file_path="/vol/p1/Q1_Report.pdf",
        extracted_data={"reporting_period": "Q1 2026", "currency": "USD", "total_expenditure": 1000.0}
    )

    entry1 = EvidenceLedgerEntry(id=1, transaction_id="TXN-SAME", paid_amount=1000.0, currency="USD")
    entry2 = EvidenceLedgerEntry(id=2, transaction_id="TXN-SAME", paid_amount=1000.0, currency="USD")

    summary, finding = MultiSourceReconciliationEngine.reconcile_project_financial_report(
        report_doc=report,
        ledger_entries=[entry1, entry2],
        investigation_id=1,
        target_scope="/vol/p1"
    )

    assert summary["transactions_correlated"] == 1
    assert summary["transaction_paid_total"] == 1000.0
    assert summary["reconciled"] is True
    assert finding is None
