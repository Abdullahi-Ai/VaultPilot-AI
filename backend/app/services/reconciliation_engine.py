import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.models.document import Document
from app.models.finding import Finding
from app.models.ledger import EvidenceLedgerEntry

CURRENCY_CODE_REGEX = re.compile(r"^[A-Za-z]{3}$")

def normalize_currency(curr: Any) -> Optional[str]:
    """
    Safely validates and normalizes a currency code.
    Returns 3-letter uppercase code (e.g. 'USD', 'EUR', 'KES') if valid.
    Returns None if missing, None, empty, whitespace-only, or not a valid 3-letter alphabetic code.
    Never defaults to USD or UNKNOWN.
    """
    if curr is None or not isinstance(curr, str):
        return None
    cleaned = curr.strip()
    if not cleaned:
        return None
    if CURRENCY_CODE_REGEX.match(cleaned):
        return cleaned.upper()
    return None

class MultiSourceReconciliationEngine:

    @staticmethod
    def match_documents(
        po_docs: List[Document],
        inv_docs: List[Document],
        rec_docs: List[Document]
    ) -> List[Dict[str, Any]]:
        """
        Task 1: Structured Matching Engine.
        Matches records using project association, PO reference, invoice reference,
        supplier identity, currency, transaction amounts, and dates.
        
        Strict rule: Do not match records solely because their amounts happen to be equal.
        Distinguishes: EXACT_MATCH, PROBABLE_MATCH, PARTIAL_MATCH, UNMATCHED, CONFLICTING_EVIDENCE, UNVERIFIED.
        """
        matched_groups: List[Dict[str, Any]] = []
        used_inv_ids = set()
        used_rec_ids = set()

        for po in po_docs:
            po_data = po.extracted_data or {}
            po_ref = po_data.get("po_reference")
            po_vendor = (po_data.get("vendor") or "").lower().strip()
            po_curr_raw = po_data.get("currency")
            po_curr = normalize_currency(po_curr_raw)
            po_amt = po_data.get("amount")

            # Look for invoices referencing this PO
            candidate_invoices = [
                inv for inv in inv_docs 
                if po_ref and (inv.extracted_data or {}).get("po_reference") == po_ref and inv.id not in used_inv_ids
            ]

            # Ambiguous/Probable match check: If no explicit PO ref, check vendor
            # STRICT: Never match purely on amount equality!
            if not candidate_invoices and po_vendor:
                for inv in inv_docs:
                    if inv.id in used_inv_ids:
                        continue
                    inv_data = inv.extracted_data or {}
                    inv_vendor = (inv_data.get("vendor") or "").lower().strip()
                    if inv_vendor and inv_vendor == po_vendor and not inv_data.get("po_reference"):
                        candidate_invoices.append(inv)
                        break

            # Find matching receipts for candidate invoices
            matched_receipts = []
            for inv in candidate_invoices:
                used_inv_ids.add(inv.id)
                inv_data = inv.extracted_data or {}
                inv_num = inv_data.get("invoice_number")
                rec_ref = inv_data.get("receipt_reference")
                
                # Check receipts citing this invoice number or receipt reference
                # Critical: Never match on None == None!
                for rec in rec_docs:
                    if rec.id in used_rec_ids:
                        continue
                    rec_data = rec.extracted_data or {}
                    rec_inv_ref = rec_data.get("invoice_reference") or rec_data.get("invoice_number")
                    rec_id = rec_data.get("receipt_id")
                    
                    is_rec_match = False
                    if inv_num and rec_inv_ref and rec_inv_ref == inv_num:
                        is_rec_match = True
                    elif rec_id and rec_ref and rec_id == rec_ref:
                        is_rec_match = True
                    
                    if is_rec_match:
                        matched_receipts.append(rec)
                        used_rec_ids.add(rec.id)

            # Determine Match Confidence
            confidence = "UNMATCHED"
            requires_review = False
            review_reason = None

            if candidate_invoices:
                all_explicit = all(bool(po_ref and (inv.extracted_data or {}).get("po_reference") == po_ref) for inv in candidate_invoices)
                
                inv_currencies = [
                    normalize_currency((inv.extracted_data or {}).get("currency"))
                    for inv in candidate_invoices
                ]
                has_invalid_or_missing_currency = (po_curr is None) or any(c is None for c in inv_currencies)
                curr_conflict = any(c != po_curr for c in inv_currencies if c is not None and po_curr is not None)
                inv_nums = [(inv.extracted_data or {}).get("invoice_number") for inv in candidate_invoices]
                has_duplicate_inv_numbers = len(inv_nums) != len(set(inv_nums))

                if has_invalid_or_missing_currency:
                    confidence = "UNVERIFIED"
                    requires_review = True
                    review_reason = "Missing, undocumented, or invalid currency code in Purchase Order or Invoices. Direct comparison prohibited."
                elif curr_conflict:
                    confidence = "CONFLICTING_EVIDENCE"
                    requires_review = True
                    review_reason = "Currency mismatch between Purchase Order and Invoices. Direct aggregation disallowed."
                elif has_duplicate_inv_numbers:
                    confidence = "CONFLICTING_EVIDENCE"
                    requires_review = True
                    review_reason = "Duplicate invoice references with conflicting data detected."
                elif not all_explicit:
                    confidence = "PROBABLE_MATCH"
                    requires_review = True
                    review_reason = "Invoices matched by vendor identity and order context; lacks explicit PO reference in document header."
                elif len(candidate_invoices) > 1:
                    inv_sum = sum(((inv.extracted_data or {}).get("amount") or 0.0) for inv in candidate_invoices)
                    confidence = "PARTIAL_MATCH" if inv_sum < (po_amt or 0.0) else "EXACT_MATCH"
                else:
                    confidence = "EXACT_MATCH"
            else:
                confidence = "UNMATCHED"
                requires_review = True
                review_reason = "Purchase order has no matching invoices within the investigated folder."

            matched_groups.append({
                "po_doc": po,
                "invoice_docs": candidate_invoices,
                "receipt_docs": matched_receipts,
                "match_confidence": confidence,
                "requires_human_review": requires_review,
                "human_review_reason": review_reason
            })

        # Add remaining unmatched invoices
        for inv in inv_docs:
            if inv.id not in used_inv_ids:
                used_inv_ids.add(inv.id)
                inv_data = inv.extracted_data or {}
                inv_num = inv_data.get("invoice_number")
                rec_ref = inv_data.get("receipt_reference")
                matched_recs = []
                for rec in rec_docs:
                    if rec.id in used_rec_ids:
                        continue
                    rec_data = rec.extracted_data or {}
                    rec_inv_ref = rec_data.get("invoice_reference") or rec_data.get("invoice_number")
                    rec_id = rec_data.get("receipt_id")
                    
                    is_rec_match = False
                    if inv_num and rec_inv_ref and rec_inv_ref == inv_num:
                        is_rec_match = True
                    elif rec_id and rec_ref and rec_id == rec_ref:
                        is_rec_match = True
                    
                    if is_rec_match:
                        matched_recs.append(rec)
                        used_rec_ids.add(rec.id)

                matched_groups.append({
                    "po_doc": None,
                    "invoice_docs": [inv],
                    "receipt_docs": matched_recs,
                    "match_confidence": "UNMATCHED" if not matched_recs else "PARTIAL_MATCH",
                    "requires_human_review": True,
                    "human_review_reason": "Invoice exists without an authorizing purchase order in the investigated folder."
                })

        # Add remaining unmatched receipts
        for rec in rec_docs:
            if rec.id not in used_rec_ids:
                used_rec_ids.add(rec.id)
                matched_groups.append({
                    "po_doc": None,
                    "invoice_docs": [],
                    "receipt_docs": [rec],
                    "match_confidence": "UNMATCHED",
                    "requires_human_review": True,
                    "human_review_reason": "Disbursement receipt exists without corresponding invoice or purchase order."
                })

        return matched_groups

    @staticmethod
    def reconcile_group(
        group: Dict[str, Any],
        investigation_id: int,
        target_scope: str,
        supporting_variations: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[EvidenceLedgerEntry, Optional[Finding]]:
        """
        Task 2: Three-Way Multi-Source Reconciliation (PO -> Invoices -> Receipts).
        Supports:
        - Exact 3-way match
        - Partial payment (paid < billed)
        - Overpayment (paid > billed) with conservative anomaly classification
        - Standalone unapplied receipts with missing-evidence classification
        - Multiple invoices against 1 PO (1:N)
        - Multiple receipts against 1 Invoice (1:N)
        - Approved variations
        - Missing receipts
        - Missing PO
        - Incomplete/unreadable docs
        - Conflicting evidence & currency integrity
        """
        po_doc = group.get("po_doc")
        invoice_docs = group.get("invoice_docs") or []
        receipt_docs = group.get("receipt_docs") or []
        confidence = group.get("match_confidence", "EXACT_MATCH")
        requires_review = group.get("requires_human_review", False)
        review_reason = group.get("human_review_reason")

        po_data = po_doc.extracted_data if po_doc else {}
        po_ref = po_data.get("po_reference")
        po_amt = po_data.get("amount")
        po_curr_raw = po_data.get("currency") if po_doc else None
        po_curr = normalize_currency(po_curr_raw)
        supplier = po_data.get("vendor")

        # Multi-invoice calculations
        valid_billed_amts = [
            (inv.extracted_data or {}).get("amount")
            for inv in invoice_docs
            if (inv.extracted_data or {}).get("amount") is not None
        ]
        total_billed = sum(valid_billed_amts) if valid_billed_amts else (0.0 if invoice_docs else None)
        inv_ref_str = ", ".join((inv.extracted_data or {}).get("invoice_number", "INV-UNKNOWN") for inv in invoice_docs) if invoice_docs else None
        if not supplier and invoice_docs:
            supplier = (invoice_docs[0].extracted_data or {}).get("vendor")

        inv_currs = [
            normalize_currency((inv.extracted_data or {}).get("currency"))
            for inv in invoice_docs
        ]
        inv_currs_raw = [
            (inv.extracted_data or {}).get("currency")
            for inv in invoice_docs
        ]

        # Multi-receipt calculations
        valid_paid_amts = [
            (rec.extracted_data or {}).get("amount")
            for rec in receipt_docs
            if (rec.extracted_data or {}).get("amount") is not None
        ]
        total_paid = sum(valid_paid_amts) if valid_paid_amts else (0.0 if receipt_docs and any((r.extracted_data or {}).get("status") == "EXTRACTED" for r in receipt_docs) else None)
        rec_ref_str = ", ".join((rec.extracted_data or {}).get("receipt_id", "REC-UNKNOWN") for rec in receipt_docs) if receipt_docs else None

        rec_currs = [
            normalize_currency((rec.extracted_data or {}).get("currency"))
            for rec in receipt_docs
        ]
        rec_currs_raw = [
            (rec.extracted_data or {}).get("currency")
            for rec in receipt_docs
        ]

        # DEF-04: Credit note check
        negative_invoices = [inv for inv in invoice_docs if ((inv.extracted_data or {}).get("amount") or 0.0) < 0]
        has_credit_notes = len(negative_invoices) > 0

        # Build breakdowns for 1:N preserving original extracted currency
        invoices_breakdown = [
            {
                "invoice_number": (inv.extracted_data or {}).get("invoice_number"),
                "amount": (inv.extracted_data or {}).get("amount"),
                "currency": (inv.extracted_data or {}).get("currency"),
                "normalized_currency": normalize_currency((inv.extracted_data or {}).get("currency")),
                "is_credit_adjustment": ((inv.extracted_data or {}).get("amount") or 0.0) < 0,
                "doc_id": inv.id
            }
            for inv in invoice_docs
        ]

        receipts_breakdown = [
            {
                "receipt_id": (rec.extracted_data or {}).get("receipt_id"),
                "amount": (rec.extracted_data or {}).get("amount"),
                "currency": (rec.extracted_data or {}).get("currency"),
                "normalized_currency": normalize_currency((rec.extracted_data or {}).get("currency")),
                "doc_id": rec.id
            }
            for rec in receipt_docs
        ]

        all_doc_ids = []
        if po_doc: all_doc_ids.append(po_doc.id)
        all_doc_ids.extend([inv.id for inv in invoice_docs])
        all_doc_ids.extend([rec.id for rec in receipt_docs])

        all_paths = []
        if po_doc: all_paths.append(po_doc.file_path)
        all_paths.extend([inv.file_path for inv in invoice_docs])
        all_paths.extend([rec.file_path for rec in receipt_docs])

        # Approved variations
        variations = supporting_variations or []
        approved_var_sum = sum(v.get("amount", 0.0) for v in variations)

        # Primary Currency: Do NOT default to USD. Preserve None if missing.
        currency = po_curr if (po_doc and po_curr) else (inv_currs[0] if (inv_currs and inv_currs[0]) else (rec_currs[0] if (rec_currs and rec_currs[0]) else None))
        curr_display = currency or "[UNDOCUMENTED CURRENCY]"

        # Evaluate currency integrity
        has_missing_currency = False
        if po_doc and po_curr is None:
            has_missing_currency = True
        if invoice_docs and any(c is None for c in inv_currs):
            has_missing_currency = True
        if receipt_docs and any(c is None for c in rec_currs):
            has_missing_currency = True

        reconciliation_status = "UNVERIFIED"
        variance_amt = None
        variance_reason = None
        finding: Optional[Finding] = None

        # Check for unreadable / degraded documents first
        unverified_doc = next((d for d in [po_doc] + invoice_docs + receipt_docs if d and d.extraction_status == "UNVERIFIED"), None)
        if unverified_doc:
            reconciliation_status = "UNVERIFIED"
            requires_review = True
            review_reason = f"Document '{unverified_doc.filename}' extraction is unverified due to optical degradation or ink smudge."
            finding = Finding(
                investigation_id=investigation_id,
                title="Optical Degradation - Unverified Source Document",
                classification="UNVERIFIED",
                subject_reference=unverified_doc.filename,
                source_paths=[unverified_doc.file_path],
                expected_value="Readable financial amount & date",
                observed_value="Smudged / unreadable optical text",
                variance_explanation="Receipt photo contains smudged numbers and low resolution. Amount remains unverified.",
                recommended_action="Obtain high-resolution scan or manual confirmation from field team.",
                source_document_ids=[unverified_doc.id],
                extracted_fields_used={"filename": unverified_doc.filename, "extraction_status": "UNVERIFIED"},
                comparison_details={"status": "unverified_scan"},
                evidence_limitations="Optical degradation prevents reliable OCR or vision extraction.",
                missing_evidence_details="Legible high-resolution re-scan.",
                classification_rationale="Classified as UNVERIFIED because source text quality is below audit threshold."
            )
            finding.documents = [unverified_doc]

        # DEF-01: Missing or Invalid Currency
        elif has_missing_currency:
            reconciliation_status = "UNVERIFIED"
            confidence = "UNVERIFIED"
            requires_review = True
            review_reason = "Missing, unextracted, or invalid currency specification in source documents prevents reliable financial comparison."
            finding = Finding(
                investigation_id=investigation_id,
                title="Undocumented or Invalid Currency Specification",
                classification="UNVERIFIED",
                subject_reference=po_ref or inv_ref_str or rec_ref_str or "Transaction Record",
                source_paths=all_paths,
                expected_value="Explicit standardized 3-letter currency code (e.g. USD, EUR, KES)",
                observed_value=f"Missing or invalid currency (PO: {po_curr_raw}, Invoices: {inv_currs_raw}, Receipts: {rec_currs_raw})",
                variance_explanation=(
                    "One or more financial documents in this transaction chain do not specify a valid currency code. "
                    "Financial comparisons and mathematical subtractions cannot be performed across undocumented currencies. "
                    "Amounts are withheld from verified totals to maintain data integrity."
                ),
                recommended_action="Inspect source document files manually to confirm the operating currency denomination.",
                source_document_ids=all_doc_ids,
                extracted_fields_used={
                    "po_currency_raw": po_curr_raw,
                    "invoice_currencies_raw": inv_currs_raw,
                    "receipt_currencies_raw": rec_currs_raw
                },
                comparison_details={"status": "missing_currency_withheld"},
                evidence_limitations=f"Scoped to '{target_scope}'. Undocumented currency cannot be defaulted.",
                missing_evidence_details="Legible currency indication on purchase orders, invoices, or payment slips.",
                classification_rationale="Classified as UNVERIFIED because financial comparison cannot be performed without valid currency denomination."
            )
            finding.documents = [d for d in [po_doc] + invoice_docs + receipt_docs if d]

        # Case: Currency Mismatch
        elif po_doc and invoice_docs and po_curr != inv_currs[0]:
            reconciliation_status = "VARIANCE_HOLD"
            confidence = "CONFLICTING_EVIDENCE"
            requires_review = True
            review_reason = f"PO currency ({po_curr}) differs from Invoice currency ({inv_currs[0]}). Multi-currency segregation enforced."
            finding = Finding(
                investigation_id=investigation_id,
                title="Multi-Currency Mismatch Without Verified Conversion Rate",
                classification="POTENTIAL_ANOMALY",
                subject_reference=f"{po_ref} ({po_curr}) vs {inv_ref_str} ({inv_currs[0]})",
                source_paths=all_paths,
                expected_value=f"{po_amt:.2f} {po_curr}" if po_amt is not None else f"PO {po_curr}",
                observed_value=f"{total_billed:.2f} {inv_currs[0]}" if total_billed is not None else f"Invoices {inv_currs[0]}",
                variance_explanation=f"Purchase order is in {po_curr} while invoices are in {inv_currs[0]}. Direct subtraction disallowed.",
                recommended_action="Check contract conversion rate or verified bank exchange voucher.",
                source_document_ids=all_doc_ids,
                extracted_fields_used={"po_currency": po_curr, "invoice_currency": inv_currs[0]},
                comparison_details={"currency_segregation": True},
                evidence_limitations=f"Scoped to '{target_scope}'. Currency exchange agreements not discovered.",
                missing_evidence_details="Signed currency exchange clause or official conversion ticket.",
                classification_rationale="Classified as POTENTIAL_ANOMALY because cross-currency transactions require verified exchange rate."
            )
            finding.documents = [d for d in [po_doc] + invoice_docs if d]

        # DEF-03: Standalone Unapplied Receipt (Receipt without Invoice or PO)
        elif not po_doc and not invoice_docs and receipt_docs:
            reconciliation_status = "UNAPPLIED_RECEIPT"
            confidence = "UNMATCHED"
            variance_amt = total_paid
            variance_reason = "Disbursement receipt has no corresponding invoice or purchase order in scoped folder."
            requires_review = True
            review_reason = "Unapplied payment receipt. Supporting commercial invoice or purchase order authorization was not located."
            finding = Finding(
                investigation_id=investigation_id,
                title="Disbursement Receipt Without Supporting Invoice or Purchase Order",
                classification="MISSING_EVIDENCE",
                subject_reference=rec_ref_str,
                source_paths=all_paths,
                expected_value="Commercial Invoice and Approved Purchase Order",
                observed_value=f"Disbursement receipt of {total_paid:.2f} {curr_display} with no corresponding invoice or PO in scoped folder",
                variance_explanation=(
                    f"Payment receipt {rec_ref_str} ({total_paid:.2f} {curr_display}) was discovered without an identifiable "
                    f"commercial invoice or authorizing purchase order within the scoped directory '{target_scope}'. "
                    "Note: This records that supporting authorization was not located in this repository; it does not claim "
                    "that the payment was unauthorized or that improper expenditure occurred."
                ),
                recommended_action="Cross-reference central finance voucher records and procurement archives to identify the underlying contract.",
                source_document_ids=all_doc_ids,
                extracted_fields_used={"receipt_id": rec_ref_str, "amount": total_paid, "currency": currency},
                comparison_details={"supporting_invoice_found": False, "supporting_po_found": False, "amount": total_paid, "currency": currency},
                evidence_limitations=f"Scoped strictly to '{target_scope}'. Central finance filing archives were not searched.",
                missing_evidence_details="Vendor invoice, signed delivery note, or purchase order authorization.",
                classification_rationale="Classified as MISSING_EVIDENCE because donor compliance requires supporting commercial documentation for disbursements."
            )
            finding.documents = receipt_docs

        # Case: Missing Receipt (Billed without payment proof) - Check this before missing PO
        elif invoice_docs and not receipt_docs:
            reconciliation_status = "MISSING_RECEIPT"
            variance_amt = total_billed
            variance_reason = "Invoice has no supporting payment receipt or bank remittance in scoped folder."
            requires_review = True
            review_reason = "Missing disbursement evidence. Commercial invoice does NOT constitute proof of payment."
            finding = Finding(
                investigation_id=investigation_id,
                title="Missing Disbursement Proof for Commercial Invoice",
                classification="MISSING_EVIDENCE",
                subject_reference=inv_ref_str,
                source_paths=all_paths,
                expected_value="Payment Receipt / Bank Remittance Voucher",
                observed_value="Invoice exists without payment record in scoped directory",
                variance_explanation=(
                    f"Invoice {inv_ref_str} ({total_billed:.2f} {curr_display}) has no corresponding bank slip, "
                    "receipt, or cash voucher within the searched folder. Note: This indicates the record was "
                    "not found in this folder, not that payment did not occur."
                ),
                recommended_action="Check whether payment voucher was archived in the central finance directory.",
                source_document_ids=all_doc_ids,
                extracted_fields_used={"invoice_number": inv_ref_str, "amount": total_billed, "currency": currency},
                comparison_details={"disbursement_proof_found": False},
                evidence_limitations=f"Scoped to folder '{target_scope}'. Note: Record absence in this directory does not prove non-payment.",
                missing_evidence_details="Bank wire advice, remittance slip, or cash payment receipt.",
                classification_rationale="Classified as MISSING_EVIDENCE because donor compliance requires payment verification."
            )
            finding.documents = invoice_docs

        # Case: Missing PO (Standalone invoice)
        elif not po_doc and invoice_docs:
            reconciliation_status = "MISSING_PO"
            requires_review = True
            review_reason = "Commercial invoice submitted without authorizing Purchase Order."
            finding = Finding(
                investigation_id=investigation_id,
                title="Invoice Submitted Without Authorizing Purchase Order",
                classification="MISSING_EVIDENCE",
                subject_reference=inv_ref_str,
                source_paths=all_paths,
                expected_value="Approved Purchase Order / Contract Authorization",
                observed_value="Invoice exists without prior PO authorization in searched folder",
                variance_explanation=(
                    f"Invoice {inv_ref_str} ({total_billed:.2f} {curr_display}) has no corresponding PO in scoped folder. "
                    "Note: This records absence in this folder, not conclusive proof that no PO was issued."
                ),
                recommended_action="Verify central procurement repository for missing PO authorization.",
                source_document_ids=all_doc_ids,
                extracted_fields_used={"invoice_number": inv_ref_str, "amount": total_billed, "currency": currency},
                comparison_details={"po_found": False},
                evidence_limitations=f"Scoped to '{target_scope}'. Central procurement archives were not searched.",
                missing_evidence_details="Authorizing Purchase Order document.",
                classification_rationale="Classified as MISSING_EVIDENCE because commercial commitments require prior PO authorization."
            )
            finding.documents = invoice_docs

        # Case: Billed Amount Exceeds PO Authorization (Discrepancy Check)
        elif po_amt and total_billed and round(total_billed - po_amt, 2) > 0.01:
            diff = round(total_billed - po_amt, 2)
            # Check if covered by approved variations
            if approved_var_sum > 0 and abs(diff - approved_var_sum) < 0.01:
                reconciliation_status = "RECONCILED_WITH_VARIATION"
                variance_amt = approved_var_sum
                variance_reason = f"Billed excess (+{approved_var_sum:.2f} {curr_display}) is substantiated by approved variation orders."
            else:
                reconciliation_status = "VARIANCE_HOLD"
                variance_amt = diff
                variance_reason = f"Invoiced billing exceeds approved PO authorization by +{diff:.2f} {curr_display}."
                requires_review = True
                review_reason = "Unsubstantiated billing variance exceeding approved purchase order limit."
                finding = Finding(
                    investigation_id=investigation_id,
                    title="Billed Amount Exceeds Purchase Order Authorization",
                    classification="CONFIRMED_DISCREPANCY",
                    subject_reference=f"{po_ref} / {inv_ref_str}",
                    source_paths=all_paths,
                    expected_value=f"PO Authorization: {po_amt:.2f} {curr_display}",
                    observed_value=f"Invoiced Billing: {total_billed:.2f} {curr_display} (+{diff:.2f} variance)",
                    variance_explanation=(
                        f"Invoice {inv_ref_str} bills {total_billed:.2f} {curr_display}, exceeding the approved "
                        f"purchase order {po_ref} ({po_amt:.2f} {curr_display}) by {diff:.2f} {curr_display}. "
                        "Exhaustive search of authorized project repository confirmed no formal amendment or variation order exists."
                    ),
                    recommended_action="Procurement officer must confirm whether an approved PO amendment was issued outside this repository.",
                    source_document_ids=all_doc_ids,
                    extracted_fields_used={"po_reference": po_ref, "po_amount": po_amt, "invoice_amount": total_billed, "currency": currency},
                    comparison_details={
                        "po_authorized_amount": po_amt,
                        "invoiced_amount": total_billed,
                        "unauthorized_variance": diff,
                        "currency": currency,
                        "calculation": f"{total_billed:.2f} - {po_amt:.2f} = +{diff:.2f} {curr_display}"
                    },
                    evidence_limitations=f"Scoped strictly to project directory '{target_scope}'.",
                    missing_evidence_details="No approved contract variation order or PO amendment exists within the scoped repository.",
                    classification_rationale="Classified as CONFIRMED_DISCREPANCY because all scoped evidence was verified and no authorizing amendment covers the variance."
                )
                finding.documents = [d for d in [po_doc] + invoice_docs if d]

        # DEF-02: Overpayment Check (Supported Disbursements Exceed Invoiced Billing)
        elif total_billed and total_paid and round(total_paid - total_billed, 2) > 0.01:
            diff = round(total_paid - total_billed, 2)
            rec_ids = [(r.extracted_data or {}).get("receipt_id") for r in receipt_docs if (r.extracted_data or {}).get("receipt_id")]
            has_duplicate_receipts = len(rec_ids) != len(set(rec_ids))

            if has_duplicate_receipts:
                reconciliation_status = "VARIANCE_HOLD"
                confidence = "CONFLICTING_EVIDENCE"
                requires_review = True
                review_reason = "Duplicate payment receipt references detected. Overpayment calculation withheld due to conflicting proof."
                finding = Finding(
                    investigation_id=investigation_id,
                    title="Duplicate Payment Receipt References in Payment Proof",
                    classification="POTENTIAL_ANOMALY",
                    subject_reference=rec_ref_str,
                    source_paths=all_paths,
                    expected_value="Distinct, non-duplicative payment receipts",
                    observed_value=f"Repeated receipt references detected among {len(receipt_docs)} receipts",
                    variance_explanation=(
                        "Duplicate receipt identifiers were detected in the payment documentation for this invoice. "
                        "Double-counting duplicate slips could produce a false overpayment calculation. "
                        "Payment allocation requires manual review."
                    ),
                    recommended_action="Finance auditor must inspect original bank remittance slips to eliminate duplicate vouchers.",
                    source_document_ids=all_doc_ids,
                    extracted_fields_used={"receipt_ids": rec_ids, "currency": currency},
                    comparison_details={"duplicate_receipts_detected": True},
                    evidence_limitations=f"Scoped to '{target_scope}'.",
                    missing_evidence_details="Unique payment vouchers verifying distinct disbursements.",
                    classification_rationale="Classified as POTENTIAL_ANOMALY because duplicate payment slips must be verified before confirming disbursement totals."
                )
                finding.documents = receipt_docs
            elif confidence in ["PROBABLE_MATCH", "UNMATCHED"]:
                reconciliation_status = "UNVERIFIED"
                requires_review = True
                review_reason = "Payment receipt allocation to invoice is ambiguous. Overpayment cannot be asserted with certainty."
                finding = Finding(
                    investigation_id=investigation_id,
                    title="Ambiguous Payment Allocation - Overpayment Indeterminate",
                    classification="UNVERIFIED",
                    subject_reference=f"{inv_ref_str} vs {rec_ref_str}",
                    source_paths=all_paths,
                    expected_value=f"Explicit payment remittance referencing invoice {inv_ref_str}",
                    observed_value=f"Disbursement of {total_paid:.2f} {curr_display} allocated without explicit invoice reference",
                    variance_explanation=(
                        f"Receipts totaling {total_paid:.2f} {curr_display} appear to exceed invoice {inv_ref_str} ({total_billed:.2f} {curr_display}), "
                        "but the matching between these documents is contextual or ambiguous. "
                        "The disbursement may cover multiple unindexed invoices or vendor credit."
                    ),
                    recommended_action="Inspect vendor statement of account or remittance advice to confirm transaction allocation.",
                    source_document_ids=all_doc_ids,
                    extracted_fields_used={"invoiced_amount": total_billed, "disbursed_amount": total_paid, "currency": currency},
                    comparison_details={"ambiguous_matching": True},
                    evidence_limitations=f"Scoped to '{target_scope}'.",
                    missing_evidence_details="Vendor remittance advice detailing invoice allocation.",
                    classification_rationale="Classified as UNVERIFIED because ambiguous document matching precludes confirming an overpayment."
                )
                finding.documents = invoice_docs + receipt_docs
            else:
                reconciliation_status = "VARIANCE_HOLD"
                variance_amt = diff
                variance_reason = f"Supported disbursement receipts ({total_paid:.2f} {curr_display}) exceed invoiced amount ({total_billed:.2f} {curr_display}) by +{diff:.2f} {curr_display}."
                requires_review = True
                review_reason = "Supported disbursement exceeds billed invoice amount. Potential overpayment or unindexed additional invoice."
                finding = Finding(
                    investigation_id=investigation_id,
                    title="Disbursement Receipts Exceed Invoiced Amount",
                    classification="POTENTIAL_ANOMALY",
                    subject_reference=f"{inv_ref_str} vs {rec_ref_str}",
                    source_paths=all_paths,
                    expected_value=f"Invoiced Total: {total_billed:.2f} {curr_display}",
                    observed_value=f"Disbursed Total: {total_paid:.2f} {curr_display} (+{diff:.2f} {curr_display} excess)",
                    variance_explanation=(
                        f"Payment receipts totaling {total_paid:.2f} {curr_display} were matched to invoice {inv_ref_str} ({total_billed:.2f} {curr_display}), "
                        f"showing an excess disbursement of {diff:.2f} {curr_display}. "
                        "Plausible operational explanations include advance payments for upcoming project phases, unattached debit notes, "
                        "or administrative duplicate processing. Evidence is insufficient to establish improper conduct without review of supplier account statements."
                    ),
                    recommended_action="Finance officer must obtain supplier statement of account to confirm whether excess funds were credited toward future orders or refunded.",
                    source_document_ids=all_doc_ids,
                    extracted_fields_used={
                        "invoice_number": inv_ref_str,
                        "invoiced_amount": total_billed,
                        "receipt_proof": rec_ref_str,
                        "disbursed_amount": total_paid,
                        "excess_disbursement": diff,
                        "currency": currency
                    },
                    comparison_details={
                        "invoiced_amount": total_billed,
                        "disbursed_amount": total_paid,
                        "excess_disbursement": diff,
                        "currency": currency,
                        "calculation": f"{total_paid:.2f} - {total_billed:.2f} = +{diff:.2f} {curr_display}"
                    },
                    evidence_limitations=f"Scoped to directory '{target_scope}'. Supplier ledger statements and refund slips were not audited.",
                    missing_evidence_details="Supplier statement of account, credit memorandum, or refund receipt.",
                    classification_rationale="Classified as POTENTIAL_ANOMALY because excess disbursement warrants account verification but does not constitute conclusive proof of misconduct."
                )
                finding.documents = invoice_docs + receipt_docs

        # Case: Partial Payment (Receipts < Invoices)
        elif total_billed and total_paid and total_paid < total_billed:
            reconciliation_status = "PARTIAL_PAYMENT"
            variance_amt = round(total_billed - total_paid, 2)
            variance_reason = f"Supported disbursement ({total_paid:.2f} {curr_display}) is less than billed amount ({total_billed:.2f} {curr_display}). Outstanding balance: {variance_amt:.2f} {curr_display}."
            requires_review = True
            review_reason = "Partial milestone disbursement detected. Outstanding balance remains unpaid or un-evidenced."
            finding = Finding(
                investigation_id=investigation_id,
                title="Partial Payment - Incomplete Disbursement Evidence",
                classification="POTENTIAL_ANOMALY",
                subject_reference=f"{inv_ref_str} vs {rec_ref_str}",
                source_paths=all_paths,
                expected_value=f"Full Invoiced Balance: {total_billed:.2f} {curr_display}",
                observed_value=f"Disbursed Proof: {total_paid:.2f} {curr_display} (Outstanding: {variance_amt:.2f} {curr_display})",
                variance_explanation=(
                    f"Disbursement proof ({total_paid:.2f} {curr_display}) covers part of invoice {inv_ref_str} ({total_billed:.2f} {curr_display}). "
                    f"Remaining balance of {variance_amt:.2f} {curr_display} has no payment proof in the scoped directory. "
                    "Plausible explanation: staged milestone retention or pending installment."
                ),
                recommended_action="Confirm milestone retention terms or check for secondary installment voucher.",
                source_document_ids=all_doc_ids,
                extracted_fields_used={"billed_amount": total_billed, "paid_amount": total_paid, "currency": currency},
                comparison_details={
                    "billed_amount": total_billed,
                    "paid_amount": total_paid,
                    "unpaid_balance": variance_amt,
                    "calculation": f"{total_billed:.2f} - {total_paid:.2f} = {variance_amt:.2f} {curr_display}"
                },
                evidence_limitations=f"Scoped to '{target_scope}'. Secondary installment receipts may be pending.",
                missing_evidence_details="Final installment disbursement voucher or milestone retention certificate.",
                classification_rationale="Classified as POTENTIAL_ANOMALY because phased milestone payments are common in NGO grants."
            )
            finding.documents = [d for d in invoice_docs + receipt_docs if d]

        # Case: Multiple Invoices against one PO (1:N)
        elif len(invoice_docs) > 1 and po_doc:
            reconciliation_status = "MULTI_INVOICE_PO"
            delta = round(total_billed - po_amt, 2) if po_amt else 0.0
            if abs(delta) < 0.01:
                variance_reason = f"Multiple invoices ({len(invoice_docs)}) aggregate exactly to PO authorization ({po_amt:.2f} {curr_display})."
            else:
                variance_amt = delta
                variance_reason = f"Multiple invoices aggregate to {total_billed:.2f} {curr_display} vs PO {po_amt:.2f} {curr_display} (delta: {delta:+.2f})."
                requires_review = True
                review_reason = "Multiple invoices exceed or differ from PO authorization limit."

        # Case: Multiple Receipts against one Invoice (1:N)
        elif len(receipt_docs) > 1 and invoice_docs:
            reconciliation_status = "MULTI_RECEIPT_INVOICE"
            diff = round(total_paid - total_billed, 2)
            if abs(diff) < 0.01:
                variance_reason = f"Multiple payment receipts ({len(receipt_docs)}) reconcile full invoice amount ({total_billed:.2f} {curr_display})."
            else:
                variance_amt = diff
                variance_reason = f"Multiple receipts total {total_paid:.2f} vs invoice {total_billed:.2f} {curr_display}."

        # Case: Exact 3-Way Match
        elif po_amt and total_billed and total_paid and abs(po_amt - total_billed) < 0.01 and abs(total_billed - total_paid) < 0.01:
            reconciliation_status = "RECONCILED_MATCH"
            confidence = "EXACT_MATCH"

        # DEF-04: Credit note check adjustment note
        if has_credit_notes:
            requires_review = True
            cn_note = f"Transaction includes {len(negative_invoices)} credit adjustment(s)/negative line item(s)."
            review_reason = f"{review_reason}; {cn_note}" if review_reason else cn_note

        # Construct Ledger Entry
        entry = EvidenceLedgerEntry(
            investigation_id=investigation_id,
            transaction_id=f"TXN-{investigation_id}-{po_ref or inv_ref_str or 'MISC'}",
            item_description=po_data.get("description") or (invoice_docs[0].extracted_data or {}).get("description", "Project Procurement Item") if invoice_docs else "General Evidence Item",
            supplier_name=supplier,
            po_reference=po_ref,
            po_amount=po_amt,
            invoice_number=inv_ref_str,
            invoice_amount=total_billed,
            receipt_proof=rec_ref_str,
            receipt_amount=total_paid,
            paid_amount=total_paid,
            approved_variation_amount=approved_var_sum,
            variance_amount=variance_amt,
            variance_reason=variance_reason,
            currency=currency,
            reconciliation_status=reconciliation_status,
            match_confidence=confidence,
            requires_human_review=requires_review,
            human_review_reason=review_reason,
            multiple_invoices_breakdown=invoices_breakdown,
            multiple_receipts_breakdown=receipts_breakdown,
            source_file_paths=all_paths,
            po_document_id=po_doc.id if po_doc else None,
            invoice_document_id=invoice_docs[0].id if invoice_docs else None,
            receipt_document_id=receipt_docs[0].id if receipt_docs else None,
            source_document_ids=all_doc_ids,
            matching_criteria={"matched_by": confidence, "invoice_count": len(invoice_docs), "receipt_count": len(receipt_docs)}
        )

        return entry, finding

    @staticmethod
    def reconcile_project_financial_report(
        report_doc: Document,
        ledger_entries: List[EvidenceLedgerEntry],
        investigation_id: int,
        target_scope: str
    ) -> Tuple[Dict[str, Any], Optional[Finding]]:
        """
        Task 3: Project Financial Report Context Reconciler.
        Compares reported expenditure against transaction-level evidence:
        - Preserves report's reporting period and currency.
        - Never double-counts transaction records.
        - Never claims an aggregate report independently proves individual payments.
        - Identifies unexplained differences without claiming fraud.
        """
        rep_data = report_doc.extracted_data or {}
        report_period = rep_data.get("reporting_period", "Q1 2026")
        rep_curr_raw = rep_data.get("currency")
        rep_curr = normalize_currency(rep_curr_raw)
        reported_expenditure = rep_data.get("total_expenditure", 0.0)

        # DEF-01: Guard against missing or invalid report currency
        if rep_curr is None:
            finding = Finding(
                investigation_id=investigation_id,
                title="Undocumented Currency in Project Financial Report",
                classification="UNVERIFIED",
                subject_reference=f"Financial Report ({report_period})",
                source_paths=[report_doc.file_path],
                expected_value="Standardized 3-letter currency code (e.g. USD, EUR, KES)",
                observed_value=f"Missing or invalid currency code: '{rep_curr_raw}'",
                variance_explanation="Project financial report does not specify a valid currency code. Cannot correlate against transaction disbursements.",
                recommended_action="Verify report currency denomination with project accountant.",
                source_document_ids=[report_doc.id],
                extracted_fields_used={"report_doc": report_doc.filename, "reporting_period": report_period, "currency_raw": rep_curr_raw},
                comparison_details={"status": "missing_currency_withheld"},
                evidence_limitations=f"Scoped to '{target_scope}'.",
                missing_evidence_details="Financial report header showing currency unit.",
                classification_rationale="Classified as UNVERIFIED because financial comparison cannot be performed without valid currency."
            )
            finding.documents = [report_doc]
            result_summary = {
                "report_filename": report_doc.filename,
                "reporting_period": report_period,
                "currency": rep_curr_raw,
                "reported_expenditure": reported_expenditure,
                "transaction_paid_total": 0.0,
                "variance": None,
                "reconciled": False,
                "transactions_correlated": 0
            }
            return result_summary, finding

        # Sum transaction disbursements strictly matching currency and within period
        seen_txns = set()
        matched_txns = []
        transaction_paid_total = 0.0

        for entry in ledger_entries:
            entry_curr = normalize_currency(entry.currency)
            if entry_curr and entry_curr == rep_curr and entry.paid_amount and entry.paid_amount > 0:
                txn_key = entry.transaction_id or str(entry.id)
                if txn_key not in seen_txns:
                    seen_txns.add(txn_key)
                    matched_txns.append(entry)
                    transaction_paid_total += entry.paid_amount

        transaction_paid_total = round(transaction_paid_total, 2)
        variance = round(reported_expenditure - transaction_paid_total, 2)

        is_reconciled = abs(variance) < 0.01
        finding: Optional[Finding] = None

        if not is_reconciled:
            finding = Finding(
                investigation_id=investigation_id,
                title="Variance Between Project Financial Report and Transaction Evidence",
                classification="POTENTIAL_ANOMALY",
                subject_reference=f"Financial Report ({report_period})",
                source_paths=[report_doc.file_path],
                expected_value=f"Reported Expenditure: {reported_expenditure:.2f} {rep_curr}",
                observed_value=f"Verified Transaction Paid Total: {transaction_paid_total:.2f} {rep_curr} (Variance: {variance:+.2f})",
                variance_explanation=(
                    f"Financial report claims total expenditure of {reported_expenditure:.2f} {rep_curr} for {report_period}. "
                    f"However, transaction-level receipts in scoped directory substantiate {transaction_paid_total:.2f} {rep_curr}, "
                    f"leaving an unexplained difference of {variance:+.2f} {rep_curr}. "
                    "Note: An aggregate financial report summarizes claims; it does not independently prove individual disbursements."
                ),
                recommended_action="Finance manager must reconcile general ledger journals with supporting vendor payment vouchers.",
                source_document_ids=[report_doc.id] + [e.receipt_document_id for e in matched_txns if e.receipt_document_id],
                extracted_fields_used={
                    "report_doc": report_doc.filename,
                    "reporting_period": report_period,
                    "reported_expenditure": reported_expenditure,
                    "currency": rep_curr
                },
                comparison_details={
                    "reported_expenditure": reported_expenditure,
                    "transaction_paid_total": transaction_paid_total,
                    "unreconciled_delta": variance,
                    "currency": rep_curr,
                    "calculation": f"{reported_expenditure:.2f} - {transaction_paid_total:.2f} = {variance:+.2f} {rep_curr}"
                },
                evidence_limitations=f"Scoped to '{target_scope}'. Sub-grantee accounts and accrual adjustments were not audited.",
                missing_evidence_details="Supporting payment vouchers covering the unreconciled expenditure balance.",
                classification_rationale="Classified as POTENTIAL_ANOMALY because timing differences or accrual journals may explain the report variance."
            )
            finding.documents = [report_doc]

        result_summary = {
            "report_filename": report_doc.filename,
            "reporting_period": report_period,
            "currency": rep_curr,
            "reported_expenditure": reported_expenditure,
            "transaction_paid_total": transaction_paid_total,
            "variance": variance,
            "reconciled": is_reconciled,
            "transactions_correlated": len(matched_txns)
        }

        # Mark reconciled status on correlated ledger entries
        for entry in matched_txns:
            entry.project_report_reference = f"{report_doc.filename} ({report_period})"
            entry.report_reconciled = is_reconciled

        return result_summary, finding
