import pytest
from app.models.document import Document
from app.models.project import Project
from app.models.ledger import EvidenceLedgerEntry
from app.services.reconciliation_engine import MultiSourceReconciliationEngine
from app.services.investigation_service import InvestigationService

def make_doc(doc_id: int, project_id: int, filename: str, doc_type: str, data: dict, status: str = "EXTRACTED") -> Document:
    return Document(
        id=doc_id,
        project_id=project_id,
        filename=filename,
        file_path=f"/volume1/grant/{filename}",
        document_type=doc_type,
        extraction_status=status,
        extracted_data=data
    )

def test_1_exact_three_way_match():
    """1. Exact PO/invoice/receipt match."""
    po = make_doc(1, 10, "PO-100.pdf", "PURCHASE_ORDER", {"po_reference": "PO-100", "vendor": "SolarTech", "amount": 5000.0, "currency": "USD"})
    inv = make_doc(2, 10, "INV-100.pdf", "INVOICE", {"po_reference": "PO-100", "invoice_number": "INV-100", "vendor": "SolarTech", "amount": 5000.0, "currency": "USD"})
    rec = make_doc(3, 10, "REC-100.pdf", "RECEIPT", {"invoice_reference": "INV-100", "receipt_id": "REC-100", "amount": 5000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec])
    assert len(groups) == 1
    assert groups[0]["match_confidence"] == "EXACT_MATCH"

    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.reconciliation_status == "RECONCILED_MATCH"
    assert entry.match_confidence == "EXACT_MATCH"
    assert entry.paid_amount == 5000.0
    assert entry.requires_human_review is False
    assert finding is None

def test_2_invoice_with_no_receipt():
    """2. Invoice with no receipt."""
    po = make_doc(1, 10, "PO-200.pdf", "PURCHASE_ORDER", {"po_reference": "PO-200", "amount": 4000.0, "currency": "USD"})
    inv = make_doc(2, 10, "INV-200.pdf", "INVOICE", {"po_reference": "PO-200", "invoice_number": "INV-200", "amount": 4000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.reconciliation_status == "MISSING_RECEIPT"
    assert entry.requires_human_review is True
    assert finding is not None
    assert finding.classification == "MISSING_EVIDENCE"
    assert "payment" in finding.title.lower() or "disbursement" in finding.title.lower()

def test_3_partial_payment():
    """3. Partial payment (receipts < invoice amount)."""
    po = make_doc(1, 10, "PO-300.pdf", "PURCHASE_ORDER", {"po_reference": "PO-300", "amount": 10000.0, "currency": "USD"})
    inv = make_doc(2, 10, "INV-300.pdf", "INVOICE", {"po_reference": "PO-300", "invoice_number": "INV-300", "amount": 10000.0, "currency": "USD"})
    rec = make_doc(3, 10, "REC-300.pdf", "RECEIPT", {"invoice_reference": "INV-300", "receipt_id": "REC-300", "amount": 6000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.reconciliation_status == "PARTIAL_PAYMENT"
    assert entry.paid_amount == 6000.0
    assert entry.variance_amount == 4000.0
    assert entry.requires_human_review is True
    assert finding is not None
    assert finding.classification == "POTENTIAL_ANOMALY"

def test_4_multiple_invoices_against_one_po():
    """4. Multiple invoices against one PO (1:N)."""
    po = make_doc(1, 10, "PO-400.pdf", "PURCHASE_ORDER", {"po_reference": "PO-400", "amount": 20000.0, "currency": "USD"})
    inv1 = make_doc(2, 10, "INV-401.pdf", "INVOICE", {"po_reference": "PO-400", "invoice_number": "INV-401", "amount": 12000.0, "currency": "USD"})
    inv2 = make_doc(3, 10, "INV-402.pdf", "INVOICE", {"po_reference": "PO-400", "invoice_number": "INV-402", "amount": 8000.0, "currency": "USD"})
    rec1 = make_doc(4, 10, "REC-401.pdf", "RECEIPT", {"invoice_reference": "INV-401", "receipt_id": "REC-401", "amount": 12000.0, "currency": "USD"})
    rec2 = make_doc(5, 10, "REC-402.pdf", "RECEIPT", {"invoice_reference": "INV-402", "receipt_id": "REC-402", "amount": 8000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv1, inv2], [rec1, rec2])
    assert len(groups[0]["invoice_docs"]) == 2
    assert len(groups[0]["receipt_docs"]) == 2

    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.reconciliation_status == "MULTI_INVOICE_PO"
    assert entry.invoice_amount == 20000.0
    assert len(entry.multiple_invoices_breakdown) == 2

def test_5_multiple_receipts_against_one_invoice():
    """5. Multiple receipts against one invoice (1:N)."""
    po = make_doc(1, 10, "PO-500.pdf", "PURCHASE_ORDER", {"po_reference": "PO-500", "amount": 15000.0, "currency": "USD"})
    inv = make_doc(2, 10, "INV-500.pdf", "INVOICE", {"po_reference": "PO-500", "invoice_number": "INV-500", "amount": 15000.0, "currency": "USD"})
    rec1 = make_doc(3, 10, "REC-501.pdf", "RECEIPT", {"invoice_reference": "INV-500", "receipt_id": "REC-501", "amount": 10000.0, "currency": "USD"})
    rec2 = make_doc(4, 10, "REC-502.pdf", "RECEIPT", {"invoice_reference": "INV-500", "receipt_id": "REC-502", "amount": 5000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec1, rec2])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.reconciliation_status == "MULTI_RECEIPT_INVOICE"
    assert entry.paid_amount == 15000.0
    assert len(entry.multiple_receipts_breakdown) == 2

def test_6_approved_variation():
    """6. Approved variation covers excess invoice."""
    po = make_doc(1, 10, "PO-600.pdf", "PURCHASE_ORDER", {"po_reference": "PO-600", "amount": 18000.0, "currency": "USD"})
    inv = make_doc(2, 10, "INV-600.pdf", "INVOICE", {"po_reference": "PO-600", "invoice_number": "INV-600", "amount": 21500.0, "currency": "USD"})
    rec = make_doc(3, 10, "REC-600.pdf", "RECEIPT", {"invoice_reference": "INV-600", "receipt_id": "REC-600", "amount": 21500.0, "currency": "USD"})

    variations = [{"ref": "VO-600-A", "amount": 3500.0, "reason": "Scope expansion approved"}]
    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant", supporting_variations=variations)
    assert entry.reconciliation_status == "RECONCILED_WITH_VARIATION"
    assert entry.approved_variation_amount == 3500.0
    assert finding is None or finding.classification != "CONFIRMED_DISCREPANCY"

def test_7_cross_project_document_rejection():
    """7. Cross-project document rejection."""
    doc_other = make_doc(99, 999, "Other_Project_Doc.pdf", "INVOICE", {"amount": 500.0})
    with pytest.raises(ValueError) as exc:
        InvestigationService.validate_document_project(doc_other, project_id=10)
    assert "Cross-project evidence rejection" in str(exc.value)

def test_8_currency_mismatch():
    """8. Currency mismatch triggers CONFLICTING_EVIDENCE / VARIANCE_HOLD."""
    po = make_doc(1, 10, "PO-800.pdf", "PURCHASE_ORDER", {"po_reference": "PO-800", "amount": 10000.0, "currency": "EUR"})
    inv = make_doc(2, 10, "INV-800.pdf", "INVOICE", {"po_reference": "PO-800", "invoice_number": "INV-800", "amount": 11000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [])
    assert groups[0]["match_confidence"] == "CONFLICTING_EVIDENCE"

    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.reconciliation_status == "VARIANCE_HOLD"
    assert finding is not None
    assert finding.classification == "POTENTIAL_ANOMALY"

def test_9_duplicate_document_references():
    """9. Duplicate invoice numbers with differing amounts trigger CONFLICTING_EVIDENCE."""
    po = make_doc(1, 10, "PO-900.pdf", "PURCHASE_ORDER", {"po_reference": "PO-900", "amount": 10000.0, "currency": "USD"})
    inv1 = make_doc(2, 10, "INV-900A.pdf", "INVOICE", {"po_reference": "PO-900", "invoice_number": "INV-DUP", "amount": 5000.0, "currency": "USD"})
    inv2 = make_doc(3, 10, "INV-900B.pdf", "INVOICE", {"po_reference": "PO-900", "invoice_number": "INV-DUP", "amount": 6000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv1, inv2], [])
    assert groups[0]["match_confidence"] == "CONFLICTING_EVIDENCE"
    assert groups[0]["requires_human_review"] is True

def test_10_ambiguous_matching_not_solely_on_amounts():
    """10. Do not match records solely because amounts happen to be equal."""
    po = make_doc(1, 10, "PO-1000.pdf", "PURCHASE_ORDER", {"po_reference": "PO-1000", "vendor": "Vendor Alpha", "amount": 7500.0, "currency": "USD"})
    inv = make_doc(2, 10, "INV-1000.pdf", "INVOICE", {"po_reference": None, "invoice_number": "INV-RANDOM", "vendor": "Vendor Omega", "amount": 7500.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [])
    # Should not pair Vendor Omega to Vendor Alpha solely because amount is $7,500
    po_group = next(g for g in groups if g["po_doc"] == po)
    assert len(po_group["invoice_docs"]) == 0
    assert po_group["match_confidence"] == "UNMATCHED"

def test_11_missing_purchase_order():
    """11. Standalone invoice with missing purchase order."""
    inv = make_doc(1, 10, "INV-UNSUPP.pdf", "INVOICE", {"po_reference": None, "invoice_number": "INV-UNSUPP", "amount": 3200.0, "currency": "USD"})
    rec = make_doc(2, 10, "REC-UNSUPP.pdf", "RECEIPT", {"invoice_reference": "INV-UNSUPP", "receipt_id": "REC-UNSUPP", "amount": 3200.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([], [inv], [rec])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.reconciliation_status == "MISSING_PO"
    assert finding is not None
    assert finding.classification == "MISSING_EVIDENCE"

def test_12_project_report_versus_transaction_evidence():
    """12. Project financial report versus transaction-level evidence."""
    rep_doc = make_doc(1, 10, "Q1_Report.xlsx", "FINANCIAL_REPORT", {
        "reporting_period": "Q1 2026",
        "currency": "USD",
        "total_expenditure": 15000.0
    })

    # Ledger has transactions totaling only 8500.0 USD
    e1 = EvidenceLedgerEntry(investigation_id=1, transaction_id="TXN-1", item_description="Solar Inverter", currency="USD", paid_amount=8500.0, reconciliation_status="RECONCILED_MATCH")
    e2 = EvidenceLedgerEntry(investigation_id=1, transaction_id="TXN-2", item_description="Pending Item", currency="USD", paid_amount=0.0, reconciliation_status="MISSING_RECEIPT")

    result, finding = MultiSourceReconciliationEngine.reconcile_project_financial_report(rep_doc, [e1, e2], investigation_id=1, target_scope="/volume1/grant")
    assert result["reconciled"] is False
    assert result["variance"] == 6500.0
    assert finding is not None
    assert finding.classification == "POTENTIAL_ANOMALY"
    assert "report" in finding.title.lower()

def test_13_preservation_of_original_provenance():
    """13. Preservation of original provenance across all matched groups."""
    po = make_doc(10, 10, "PO-ORIG.pdf", "PURCHASE_ORDER", {"po_reference": "PO-ORIG", "amount": 5000.0, "currency": "USD"})
    inv = make_doc(20, 10, "INV-ORIG.pdf", "INVOICE", {"po_reference": "PO-ORIG", "invoice_number": "INV-ORIG", "amount": 5000.0, "currency": "USD"})
    rec = make_doc(30, 10, "REC-ORIG.pdf", "RECEIPT", {"invoice_reference": "INV-ORIG", "receipt_id": "REC-ORIG", "amount": 5000.0, "currency": "USD"})

    groups = MultiSourceReconciliationEngine.match_documents([po], [inv], [rec])
    entry, finding = MultiSourceReconciliationEngine.reconcile_group(groups[0], investigation_id=1, target_scope="/volume1/grant")
    assert entry.po_document_id == 10
    assert entry.invoice_document_id == 20
    assert entry.receipt_document_id == 30
    assert set(entry.source_document_ids) == {10, 20, 30}
    assert "/volume1/grant/PO-ORIG.pdf" in entry.source_file_paths
    assert "/volume1/grant/INV-ORIG.pdf" in entry.source_file_paths
    assert "/volume1/grant/REC-ORIG.pdf" in entry.source_file_paths
