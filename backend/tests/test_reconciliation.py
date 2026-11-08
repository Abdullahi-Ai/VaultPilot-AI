import pytest
from app.services.investigation_service import InvestigationService

def test_equal_amounts_reconciliation():
    """
    Test 1: Equal amounts between PO and Invoice.
    Should produce RECONCILED_MATCH and no discrepancy finding.
    """
    status, finding = InvestigationService.evaluate_amount_comparison(
        po_ref="PO-2026-001",
        po_amt=10000.0,
        po_curr="USD",
        inv_ref="INV-2026-001",
        inv_amt=10000.0,
        inv_curr="USD",
        evidence_sufficiency="SUFFICIENT"
    )
    assert status == "RECONCILED_MATCH"
    assert finding is None

def test_different_amounts_insufficient_evidence():
    """
    Test 2: Different amounts with INSUFFICIENT supporting evidence.
    Must NOT automatically be classified as CONFIRMED_DISCREPANCY.
    Must be classified as POTENTIAL_ANOMALY, noting possible unindexed amendments/taxes.
    Must NEVER describe the anomaly as fraud.
    """
    status, finding = InvestigationService.evaluate_amount_comparison(
        po_ref="PO-2026-002",
        po_amt=5000.0,
        po_curr="USD",
        inv_ref="INV-2026-002",
        inv_amt=6200.0,
        inv_curr="USD",
        evidence_sufficiency="INSUFFICIENT"
    )
    assert status == "VARIANCE_HOLD"
    assert finding is not None
    assert finding.classification == "POTENTIAL_ANOMALY"
    assert "fraud" not in finding.variance_explanation.lower()
    assert "fraud" not in finding.recommended_action.lower()
    assert "insufficient" in finding.title.lower() or "insufficient" in finding.variance_explanation.lower()

def test_different_amounts_with_approved_variation():
    """
    Test 3: Different amounts with an approved supporting variation.
    Variance is covered by an approved variation order.
    Must NOT be classified as CONFIRMED_DISCREPANCY.
    """
    variations = [
        {"ref": "VO-2026-01", "amount": 2500.0, "reason": "Scope addition approved by donor"}
    ]
    status, finding = InvestigationService.evaluate_amount_comparison(
        po_ref="PO-2026-003",
        po_amt=15000.0,
        po_curr="USD",
        inv_ref="INV-2026-003",
        inv_amt=17500.0,
        inv_curr="USD",
        supporting_variations=variations,
        evidence_sufficiency="SUFFICIENT"
    )
    assert status == "RECONCILED_WITH_VARIATION"
    assert finding is not None
    assert finding.classification != "CONFIRMED_DISCREPANCY"
    assert finding.classification == "POTENTIAL_ANOMALY"
    assert "VO-2026-01" in finding.subject_reference or "VO-2026-01" in finding.variance_explanation
    assert "fraud" not in finding.variance_explanation.lower()

def test_missing_supporting_documentation():
    """
    Test 4: Indeterminate or missing extraction fields.
    Must be classified as UNVERIFIED or MISSING_EVIDENCE, not confirmed discrepancy.
    """
    status, finding = InvestigationService.evaluate_amount_comparison(
        po_ref="PO-2026-004",
        po_amt=None,
        po_curr="USD",
        inv_ref="INV-2026-004",
        inv_amt=8000.0,
        inv_curr="USD"
    )
    assert status == "UNVERIFIED"
    assert finding is not None
    assert finding.classification == "UNVERIFIED"
    assert "fraud" not in finding.variance_explanation.lower()

def test_different_currencies():
    """
    Test 5: Multi-currency mismatch (e.g. EUR vs USD).
    Must NOT perform direct mathematical subtraction or sum currencies.
    Must classify as POTENTIAL_ANOMALY and keep currencies segregated.
    """
    status, finding = InvestigationService.evaluate_amount_comparison(
        po_ref="PO-2026-005",
        po_amt=10000.0,
        po_curr="EUR",
        inv_ref="INV-2026-005",
        inv_amt=11000.0,
        inv_curr="USD",
        evidence_sufficiency="SUFFICIENT"
    )
    assert status == "VARIANCE_HOLD"
    assert finding is not None
    assert finding.classification == "POTENTIAL_ANOMALY"
    assert "multi-currency" in finding.title.lower() or "currency" in finding.title.lower()
    assert "EUR" in finding.expected_value
    assert "USD" in finding.observed_value
    assert "fraud" not in finding.variance_explanation.lower()
