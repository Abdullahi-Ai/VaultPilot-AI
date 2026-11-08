import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple, Set
from app.models.report import InvestigationReport

class ReportIntegrityError(ValueError):
    """Raised when an investigation report snapshot fails cryptographic integrity verification."""
    pass

# =========================================================================
# ISO 4217 Currency Reference & Minor Unit Precision Mappings
# =========================================================================

# Zero minor units (exponent = 0): No sub-unit in standard circulation
ZERO_DECIMAL_CURRENCIES = frozenset({
    "BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW",
    "PYG", "RWF", "UGX", "UYI", "VND", "VUV", "XAF", "XOF", "XPF"
})

# Three minor units (exponent = -3): 1/1000th sub-unit
THREE_DECIMAL_CURRENCIES = frozenset({
    "BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"
})

# Two minor units (exponent = -2): Standard 1/100th sub-unit
TWO_DECIMAL_CURRENCIES = frozenset({
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BMD", "BND", "BOB", "BOV", "BRL", "BSD",
    "BTN", "BWP", "BYN", "BZD", "CAD", "CDF", "CHE", "CHF", "CHW", "CLF",
    "CNY", "COP", "COU", "CRC", "CUC", "CUP", "CVE", "CZK", "DKK", "DOP",
    "DZD", "EGP", "ERN", "ETB", "EUR", "FJD", "FKP", "GBP", "GEL", "GHS",
    "GIP", "GMD", "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG", "HUF", "IDR",
    "ILS", "INR", "IRR", "JMD", "KES", "KGS", "KHR", "KPW", "KYD", "KZT",
    "LAK", "LBP", "LKR", "LRD", "LSL", "MAD", "MDL", "MGA", "MKD", "MMK",
    "MNT", "MOP", "MRU", "MUR", "MVR", "MWK", "MXN", "MXV", "MYR", "MZN",
    "NAD", "NGN", "NIO", "NOK", "NPR", "NZD", "PAB", "PEN", "PGK", "PHP",
    "PKR", "PLN", "QAR", "RON", "RSD", "RUB", "SAR", "SBD", "SCR", "SDG",
    "SEK", "SGD", "SHP", "SLL", "SOS", "SRD", "SSP", "STN", "SVC", "SYP",
    "SZL", "THB", "TJS", "TMT", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH",
    "USD", "USN", "UYU", "UYW", "UZS", "VES", "WST", "XCD", "YER", "ZAR",
    "ZMW", "ZWL"
})

RECOGNIZED_CURRENCIES = ZERO_DECIMAL_CURRENCIES | THREE_DECIMAL_CURRENCIES | TWO_DECIMAL_CURRENCIES

def get_currency_minor_units(currency: Optional[str]) -> Optional[int]:
    """
    Returns the ISO 4217 minor unit exponent (0, 2, or 3) for recognized currencies.
    Returns None if currency is missing, empty, or not an ISO 4217 recognized currency.
    """
    if not currency or not isinstance(currency, str):
        return None
    code = currency.upper().strip()
    if code in ZERO_DECIMAL_CURRENCIES:
        return 0
    if code in THREE_DECIMAL_CURRENCIES:
        return 3
    if code in TWO_DECIMAL_CURRENCIES:
        return 2
    return None

def is_currency_recognized(currency: Optional[str]) -> bool:
    """Returns True if the currency code is a recognized ISO 4217 currency."""
    return get_currency_minor_units(currency) is not None

def has_excessive_precision(val: Any, currency: Optional[str]) -> bool:
    """
    Checks if a monetary amount exceeds the minor-unit precision of a recognized currency.
    
    Returns True if:
      - Currency is recognized and the amount has non-zero fractional digits beyond the currency's minor units.
    Returns False if:
      - Amount is within normal minor units.
      - Amount is None or invalid.
      - Currency is unrecognized (handled separately under unverified currency).
    """
    minor_units = get_currency_minor_units(currency)
    if minor_units is None or val is None or val == "":
        return False
    try:
        s = str(val).strip()
        d = Decimal(s)
        if not d.is_finite():
            return False
        multiplier = Decimal(10) ** minor_units
        scaled = d * multiplier
        return (scaled % Decimal(1)) != Decimal(0)
    except (InvalidOperation, TypeError, ValueError):
        return False

# =========================================================================
# Financial Numeric Validation & Formatting
# =========================================================================

def validate_financial_decimal(val: Any, currency: Optional[str] = None) -> Optional[Decimal]:
    """
    Strictly parses and validates financial monetary amounts using Python Decimal.
    
    1. Rejects None, empty strings, and booleans.
    2. Parses valid positive and negative numeric representations.
    3. Rejects non-finite values (NaN, Infinity, -Infinity).
    4. Rejects formula-like expressions or expressions with operators (e.g. '-1+1').
    5. Normalizes signed negative zero to Decimal('0.00') or Decimal('0').
    6. For recognized currencies, ensures standard minimum precision (0 decimals for JPY, 3 for KWD, 2 for USD/EUR),
       while strictly preserving sub-cent precision (e.g. '123.456') without silent rounding.
    7. For unsupported, unrecognized, or missing currencies:
       Preserves the exact source Decimal digits without assuming 2 decimal places or padding.
    8. Never silently converts invalid inputs to Decimal('0.00').
    """
    if val is None or val == "" or isinstance(val, bool):
        return None
    try:
        s = str(val).strip()
        # Fast reject if string contains formula triggers, whitespace, or control characters
        if any(c in s for c in ("=", "@", " ", "\t", "\r", "\n", "%", "|")):
            return None
        # Reject non-finite strings
        if s.lower() in ("nan", "infinity", "-infinity", "+infinity", "inf", "-inf"):
            return None
        # Reject multiple signs or arithmetic operators like '-1+1' or '--5'
        if s.count("+") + s.count("-") > 1 and not (s.startswith(("-", "+")) and s[1:].replace(".", "", 1).isdigit()):
            return None

        d = Decimal(s)
        if not d.is_finite():
            return None

        # Normalize negative zero
        if d == Decimal(0):
            d = Decimal(0)

        minor_units = get_currency_minor_units(currency)
        if minor_units is None:
            # Unrecognized, unsupported, or missing currency:
            # Do NOT assume 2 decimal places! Preserve exact source precision as extracted without padding or rounding.
            return d

        # Recognized currency: determine minimum padding
        if minor_units == 0:
            min_exp = 0
            step = Decimal("1")
        elif minor_units == 3:
            min_exp = -3
            step = Decimal("0.001")
        else: # 2
            min_exp = -2
            step = Decimal("0.01")

        curr_exp = d.as_tuple().exponent
        # If source has fewer decimal places than standard minimum, pad to standard minimum
        if curr_exp > min_exp:
            return d.quantize(step)
        # If source has at least minimum precision (or finer, e.g. 123.456), preserve exact source digits!
        return d
    except (InvalidOperation, TypeError, ValueError):
        return None

def format_financial_decimal(val: Any, currency: Optional[str] = None) -> str:
    """
    Formats a validated monetary amount into an exact decimal string.
    Returns an empty string for missing or invalid values to preserve documentation gaps without
    corrupting financial balances to 0.00.
    """
    d = validate_financial_decimal(val, currency=currency)
    if d is None:
        return ""
    return str(d)

def sanitize_csv_text_cell(val: Any) -> str:
    """
    Safely sanitizes untrusted text values for CSV export.
    
    1. Returns None or empty as empty string.
    2. Strips leading whitespace and control characters (spaces, tabs, CR, LF)
       to inspect the true first character.
    3. If first non-whitespace character is a formula trigger (=, +, -, @, %, |),
       neutralizes formula execution by prepending a single quote (').
    4. Preserves ordinary safe text values unmodified.
    """
    if val is None:
        return ""
    s = str(val)
    if not s:
        return ""
    
    l_stripped = s.lstrip(" \t\r\n")
    if l_stripped and l_stripped[0] in ("=", "+", "-", "@", "%", "|"):
        return f"'{s}"
    return s

# =========================================================================
# CSV Financial Exporter Service
# =========================================================================

class CSVFinancialExporter:
    """
    Renders audit-grade, spreadsheet-compatible CSV financial schedules exclusively
    from an immutable InvestigationReport entity and its stored snapshot_payload.
    
    Enforces fail-closed cryptographic integrity verification before generating any content.
    """

    VALID_SCHEDULES = ("reconciliation", "summary", "findings", "evidence")

    @classmethod
    def export_schedule(
        cls,
        report: InvestigationReport,
        schedule: str = "reconciliation",
        include_metadata_header: bool = False
    ) -> str:
        """
        Exports a specified report schedule as a CSV string with a leading UTF-8 BOM.
        
        By default (include_metadata_header=False), the very first row is the standard CSV
        column header row for seamless compatibility with Python csv.reader, csv.DictReader,
        and pandas.
        
        If include_metadata_header=True, prepends 4 contextual audit comment lines (# ...).
        
        Refuses export (raises ReportIntegrityError) if the snapshot is missing, malformed,
        or fails SHA-256 cryptographic integrity verification.
        """
        schedule_lower = schedule.lower().strip()
        if schedule_lower not in cls.VALID_SCHEDULES:
            raise ValueError(
                f"Invalid schedule '{schedule}'. Must be one of: {', '.join(cls.VALID_SCHEDULES)}."
            )

        # 1. Gated Fail-Closed Integrity Verification
        if not report or not report.snapshot_payload or not report.snapshot_integrity_hash:
            raise ReportIntegrityError(
                "REPORT_INTEGRITY_VERIFICATION_FAILED: Report record has no cryptographic integrity hash or snapshot payload."
            )

        from app.services.report_service import ReportService
        if not ReportService.verify_report_integrity(report):
            raise ReportIntegrityError(
                "REPORT_INTEGRITY_VERIFICATION_FAILED: Stored snapshot payload failed SHA-256 integrity verification. "
                "Export generation refused."
            )

        snapshot = report.snapshot_payload or {}
        inv_summary = snapshot.get("investigation_summary") or {}
        findings = snapshot.get("findings_snapshot") or []
        evidence = snapshot.get("evidence_register_snapshot") or []
        financial = snapshot.get("financial_summary") or {}
        ledger = snapshot.get("reconciliation_ledger_snapshot") or []

        output = io.StringIO()

        # 2. Contextual Audit Header (Only if explicitly requested)
        if include_metadata_header:
            report_id = report.id
            version = report.report_version
            inv_id = report.investigation_id
            project_code = sanitize_csv_text_cell(inv_summary.get("project_code") or "N/A")
            project_name = sanitize_csv_text_cell(inv_summary.get("project_name") or "Unspecified Project")
            sha_hash = report.snapshot_integrity_hash

            output.write("# VaultPilot AI Audit Export\r\n")
            output.write(f"# Report ID: IR-{report_id}-V{version} | Investigation ID: #{inv_id}\r\n")
            output.write(f"# Project: {project_code} - {project_name}\r\n")
            output.write(f"# Cryptographic Integrity: VERIFIED ({sha_hash})\r\n")

        writer = csv.writer(output, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)

        # 3. Schedule-Specific Rendering
        if schedule_lower == "reconciliation":
            cls._render_reconciliation_schedule(writer, ledger, evidence)
        elif schedule_lower == "summary":
            cls._render_summary_schedule(writer, financial, ledger=ledger)
        elif schedule_lower == "findings":
            cls._render_findings_schedule(writer, findings)
        elif schedule_lower == "evidence":
            cls._render_evidence_schedule(writer, evidence)

        # Emit with UTF-8 Byte Order Mark for Excel compatibility
        return "\ufeff" + output.getvalue()

    @classmethod
    def export_schedule_bytes(
        cls,
        report: InvestigationReport,
        schedule: str = "reconciliation",
        include_metadata_header: bool = False
    ) -> bytes:
        """Exports a specified schedule as UTF-8 BOM encoded bytes."""
        text = cls.export_schedule(report, schedule=schedule, include_metadata_header=include_metadata_header)
        return text.encode("utf-8")

    @classmethod
    def _render_reconciliation_schedule(
        cls,
        writer: Any,
        ledger: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]]
    ) -> None:
        headers = [
            "Transaction_Tracking_ID",
            "Item_Description",
            "Supplier_Name",
            "Currency",
            "PO_Reference",
            "PO_Authorized_Amount",
            "Invoice_Number",
            "Invoice_Billed_Amount",
            "Receipt_Proof_ID",
            "Disbursed_Paid_Amount",
            "Variance_Amount",
            "Reconciliation_Status",
            "Match_Confidence",
            "Requires_Human_Review",
            "Human_Review_Reason",
            "Variance_Reason"
        ]
        writer.writerow(headers)

        if ledger:
            for row in ledger:
                curr = row.get("currency")
                is_rec = is_currency_recognized(curr)
                po_amt = row.get("po_amount")
                inv_amt = row.get("invoice_amount")
                paid_amt = row.get("paid_amount")
                var_amt = row.get("variance_amount")

                # Detect excessive fractional precision on any monetary amount
                excess_prec = any(
                    has_excessive_precision(amt, curr)
                    for amt in (po_amt, inv_amt, paid_amt, var_amt)
                    if amt is not None
                )

                req_review = bool(row.get("requires_human_review"))
                review_reasons: List[str] = []
                if row.get("human_review_reason"):
                    review_reasons.append(str(row.get("human_review_reason")))

                # Check currency validity
                if not curr:
                    req_review = True
                    review_reasons.append("Missing currency code on transaction.")
                elif not is_rec:
                    req_review = True
                    review_reasons.append(f"Unrecognized or unsupported currency '{curr}'.")

                if excess_prec:
                    req_review = True
                    review_reasons.append("Amount exceeds currency minor-unit precision.")

                # Adjust reconciliation status if currency or precision invalidates clean match
                status = row.get("reconciliation_status") or "UNVERIFIED"
                if not curr or not is_rec:
                    if status in ("RECONCILED", "RECONCILED_MATCH"):
                        status = "UNVERIFIED_CURRENCY"
                elif excess_prec:
                    if status in ("RECONCILED", "RECONCILED_MATCH"):
                        status = "EXCESSIVE_PRECISION_HOLD"

                combined_reason = "; ".join(dict.fromkeys(review_reasons))

                writer.writerow([
                    sanitize_csv_text_cell(str(row.get("transaction_id") or "N/A")),
                    sanitize_csv_text_cell(row.get("item_description") or "General Item"),
                    sanitize_csv_text_cell(row.get("supplier_name") or ""),
                    sanitize_csv_text_cell(curr or ""),
                    sanitize_csv_text_cell(row.get("po_reference") or ""),
                    format_financial_decimal(po_amt, currency=curr),
                    sanitize_csv_text_cell(row.get("invoice_number") or ""),
                    format_financial_decimal(inv_amt, currency=curr),
                    sanitize_csv_text_cell(row.get("receipt_proof") or ""),
                    format_financial_decimal(paid_amt, currency=curr),
                    format_financial_decimal(var_amt, currency=curr),
                    sanitize_csv_text_cell(status),
                    sanitize_csv_text_cell(row.get("match_confidence") or "UNMATCHED"),
                    "Yes" if req_review else "No",
                    sanitize_csv_text_cell(combined_reason),
                    sanitize_csv_text_cell(row.get("variance_reason") or "")
                ])
        else:
            # Rigorous Fallback matching engine for legacy snapshots without reconciliation_ledger_snapshot
            cls._render_legacy_fallback_reconciliation(writer, evidence)

    @classmethod
    def _render_legacy_fallback_reconciliation(
        cls,
        writer: Any,
        evidence: List[Dict[str, Any]]
    ) -> None:
        """
        Conservative legacy fallback matching engine.
        
        Strict rules:
        1. Never invents matches or asserts a 3-way match when documents are missing.
        2. Detects missing POs, missing receipts, and standalone receipts.
        3. Identifies ambiguous multiple candidate documents.
        4. Detects currency mismatches across matched documents.
        5. Computes actual variances and flags variance holds.
        6. Flags unsupported currencies and excessive precision for human review.
        """
        pos = [d for d in evidence if d.get("document_type") == "PURCHASE_ORDER"]
        invs = [d for d in evidence if d.get("document_type") == "INVOICE"]
        recs = [d for d in evidence if d.get("document_type") == "RECEIPT"]

        pos_by_ref: Dict[str, List[Dict[str, Any]]] = {}
        for po in pos:
            ref = po.get("extracted_data_summary", {}).get("po_reference")
            if ref:
                pos_by_ref.setdefault(ref, []).append(po)

        recs_by_inv_ref: Dict[str, List[Dict[str, Any]]] = {}
        for rec in recs:
            ref = rec.get("extracted_data_summary", {}).get("invoice_reference")
            if ref:
                recs_by_inv_ref.setdefault(ref, []).append(rec)

        used_po_ids: Set[Any] = set()
        used_rec_ids: Set[Any] = set()

        for inv in invs:
            i_data = inv.get("extracted_data_summary") or {}
            i_num = i_data.get("invoice_number") or f"INV-UNKNOWN-{inv.get('document_id')}"
            i_po_ref = i_data.get("po_reference")
            i_amt = i_data.get("amount")
            i_curr = i_data.get("currency")
            vendor = i_data.get("vendor") or ""

            po_candidates = pos_by_ref.get(i_po_ref, []) if i_po_ref else []
            rec_candidates = recs_by_inv_ref.get(i_num, []) if i_num else []

            # 1. PO resolution
            po_doc = None
            p_amt = None
            p_curr = None
            po_ref_display = i_po_ref or "No PO"

            if len(po_candidates) == 1:
                po_doc = po_candidates[0]
                used_po_ids.add(po_doc.get("document_id"))
                p_amt = po_doc.get("extracted_data_summary", {}).get("amount")
                p_curr = po_doc.get("extracted_data_summary", {}).get("currency")
                if not vendor:
                    vendor = po_doc.get("extracted_data_summary", {}).get("vendor") or ""

            # 2. Receipt resolution
            rec_doc = None
            r_amt = None
            r_curr = None
            r_proof = ""

            if len(rec_candidates) == 1:
                rec_doc = rec_candidates[0]
                used_rec_ids.add(rec_doc.get("document_id"))
                r_amt = rec_doc.get("extracted_data_summary", {}).get("amount")
                r_curr = rec_doc.get("extracted_data_summary", {}).get("currency")
                r_proof = rec_doc.get("extracted_data_summary", {}).get("receipt_id") or ""

            # 3. Determine Status, Confidence, Human Review, and Variance
            status = "UNVERIFIED"
            confidence = "UNMATCHED"
            requires_review = "Yes"
            review_reason = ""
            var_reason = ""
            var_str = ""

            if len(po_candidates) > 1 or len(rec_candidates) > 1:
                status = "AMBIGUOUS_MATCH"
                confidence = "AMBIGUOUS"
                review_reason = "Multiple candidate documents reference the same identifier."
            elif not po_candidates and not rec_candidates:
                status = "UNVERIFIED_STANDALONE_INVOICE"
                confidence = "UNMATCHED"
                review_reason = "Missing both purchase order authorization and payment receipt proof."
            elif not po_candidates:
                status = "MISSING_PO"
                confidence = "PARTIAL_MATCH"
                review_reason = "Missing purchase order authorization."
                if rec_doc:
                    var_str = format_financial_decimal(r_amt, currency=i_curr)
            elif not rec_candidates:
                status = "MISSING_RECEIPT"
                confidence = "PARTIAL_MATCH"
                review_reason = "Missing disbursement proof receipt."
            else:
                # Exactly 1 PO and 1 Receipt candidates found
                # Check currency consistency
                doc_currs = {c for c in (i_curr, p_curr, r_curr) if c}
                if len(doc_currs) > 1:
                    status = "CURRENCY_MISMATCH"
                    confidence = "UNVERIFIED"
                    review_reason = f"Currency mismatch across documents: {', '.join(sorted(doc_currs))}."
                elif not i_curr or not is_currency_recognized(i_curr):
                    status = "UNVERIFIED_CURRENCY"
                    confidence = "PARTIAL_MATCH"
                    review_reason = f"Unrecognized or unsupported currency '{i_curr}'."
                else:
                    # Currency matches and is recognized: compare amounts
                    d_p = validate_financial_decimal(p_amt, currency=i_curr)
                    d_i = validate_financial_decimal(i_amt, currency=i_curr)
                    d_r = validate_financial_decimal(r_amt, currency=i_curr)

                    if d_p is not None and d_i is not None and d_r is not None and d_p == d_i == d_r:
                        # Amounts match exactly: check for excessive fractional precision
                        if has_excessive_precision(d_i, i_curr):
                            status = "EXCESSIVE_PRECISION_HOLD"
                            confidence = "EXACT_MATCH"
                            requires_review = "Yes"
                            review_reason = "Amount exceeds currency minor-unit precision."
                            var_str = format_financial_decimal(Decimal(0), currency=i_curr)
                        else:
                            status = "RECONCILED"
                            confidence = "EXACT_MATCH"
                            requires_review = "No"
                            review_reason = ""
                            var_str = format_financial_decimal(Decimal(0), currency=i_curr)
                    else:
                        status = "VARIANCE_HOLD"
                        confidence = "VARIANCE_DETECTED"
                        requires_review = "Yes"
                        var_reason = "Disbursed amount differs from billed or authorized amount."
                        review_reason = "Amount variance across authorization, billing, or proof."
                        if d_r is not None and d_i is not None:
                            var_val = d_r - d_i
                            var_str = format_financial_decimal(var_val, currency=i_curr)

            writer.writerow([
                sanitize_csv_text_cell(str(i_num)),
                "Invoiced Procurement Item",
                sanitize_csv_text_cell(vendor),
                sanitize_csv_text_cell(i_curr or ""),
                sanitize_csv_text_cell(po_ref_display),
                format_financial_decimal(p_amt, currency=i_curr),
                sanitize_csv_text_cell(str(i_num)),
                format_financial_decimal(i_amt, currency=i_curr),
                sanitize_csv_text_cell(str(r_proof)),
                format_financial_decimal(r_amt, currency=i_curr),
                var_str,
                sanitize_csv_text_cell(status),
                sanitize_csv_text_cell(confidence),
                requires_review,
                sanitize_csv_text_cell(review_reason),
                sanitize_csv_text_cell(var_reason)
            ])

        # 4. Standalone unapplied receipts not matched to any invoice
        for rec in recs:
            if rec.get("document_id") not in used_rec_ids:
                r_data = rec.get("extracted_data_summary") or {}
                r_id = r_data.get("receipt_id") or f"REC-{rec.get('document_id')}"
                r_amt = r_data.get("amount")
                r_curr = r_data.get("currency")
                r_inv_ref = r_data.get("invoice_reference") or ""

                writer.writerow([
                    sanitize_csv_text_cell(str(r_id)),
                    "Unapplied Payment Receipt",
                    "",
                    sanitize_csv_text_cell(r_curr or ""),
                    "",
                    "",
                    sanitize_csv_text_cell(r_inv_ref),
                    "",
                    sanitize_csv_text_cell(str(r_id)),
                    format_financial_decimal(r_amt, currency=r_curr),
                    "",
                    "UNAPPLIED_RECEIPT",
                    "UNMATCHED",
                    "Yes",
                    "Disbursement voucher has no matching invoice in evidence register.",
                    ""
                ])

        # 5. Standalone unbilled purchase orders not referenced by any invoice
        for po in pos:
            if po.get("document_id") not in used_po_ids:
                p_data = po.get("extracted_data_summary") or {}
                p_ref = p_data.get("po_reference") or f"PO-{po.get('document_id')}"
                p_amt = p_data.get("amount")
                p_curr = p_data.get("currency")
                p_vendor = p_data.get("vendor") or ""

                writer.writerow([
                    sanitize_csv_text_cell(str(p_ref)),
                    "Unbilled Purchase Authorization",
                    sanitize_csv_text_cell(p_vendor),
                    sanitize_csv_text_cell(p_curr or ""),
                    sanitize_csv_text_cell(str(p_ref)),
                    format_financial_decimal(p_amt, currency=p_curr),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "UNBILLED_PO",
                    "UNMATCHED",
                    "No",
                    "Purchase order has no billed invoice in evidence register.",
                    ""
                ])

    @classmethod
    def _render_summary_schedule(
        cls,
        writer: Any,
        financial: Dict[str, Any],
        ledger: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        headers = [
            "Currency",
            "Metric_Category",
            "Amount",
            "Transaction_Count",
            "Accounting_Guidance"
        ]
        writer.writerow(headers)

        by_curr = financial.get("by_currency") or {}
        undoc = financial.get("undocumented_currency_entries") or []

        # Audit ledger entries to detect excessive precision or unsupported currencies
        excessive_by_curr: Dict[str, Dict[str, Any]] = {}
        unsupported_ledger_entries: List[Dict[str, Any]] = []

        if ledger:
            for row in ledger:
                curr = row.get("currency")
                if not curr:
                    continue
                if not is_currency_recognized(curr):
                    unsupported_ledger_entries.append(row)
                    continue

                paid_amt = row.get("paid_amount")
                inv_amt = row.get("invoice_amount")
                status = row.get("reconciliation_status")

                if has_excessive_precision(paid_amt, curr) or has_excessive_precision(inv_amt, curr):
                    excessive_by_curr.setdefault(curr, {"total_excessive": Decimal(0), "count": 0, "was_verified": Decimal(0)})
                    amt_to_hold = validate_financial_decimal(paid_amt or inv_amt, currency=curr) or Decimal(0)
                    excessive_by_curr[curr]["total_excessive"] += amt_to_hold
                    excessive_by_curr[curr]["count"] += 1
                    if status in ("RECONCILED_MATCH", "RECONCILED", "RECONCILED_WITH_VARIATION"):
                        excessive_by_curr[curr]["was_verified"] += amt_to_hold

        # Render recognized currencies
        for c, item in sorted(by_curr.items()):
            if not is_currency_recognized(c):
                # Unsupported currency code: exclude from verified totals and disclose under unsupported
                unsupp_amt = item.get("verified_expenditure", 0.0) + item.get("unverified_amounts", 0.0)
                writer.writerow([
                    sanitize_csv_text_cell(c),
                    "Unsupported Currency Disclosure",
                    format_financial_decimal(unsupp_amt, currency=c),
                    item.get("transaction_count", 0),
                    f"Currency code '{c}' is not an ISO 4217 recognized currency; excluded from verified totals."
                ])
                continue

            c_safe = sanitize_csv_text_cell(c)
            tx_count = item.get("transaction_count", 0)

            # Calculate clean verified expenditure excluding any entries with excessive precision
            if ledger:
                clean_verified = sum(
                    Decimal(str(r.get("paid_amount") or r.get("invoice_amount") or 0.0))
                    for r in ledger
                    if r.get("currency") == c
                    and r.get("reconciliation_status") in ("RECONCILED_MATCH", "RECONCILED", "RECONCILED_WITH_VARIATION")
                    and not has_excessive_precision(r.get("paid_amount"), c)
                    and not has_excessive_precision(r.get("invoice_amount"), c)
                )
            else:
                clean_verified = Decimal(str(item.get("verified_expenditure", 0.0)))

            writer.writerow([
                c_safe,
                "Verified Matching Expenditure",
                format_financial_decimal(clean_verified, currency=c),
                tx_count,
                "Fully reconciled three-way match (PO <-> Invoice <-> Receipt)"
            ])
            writer.writerow([
                c_safe,
                "Unapplied Payment Receipts",
                format_financial_decimal(item.get("unapplied_receipts", 0.0), currency=c),
                tx_count,
                "Disbursement voucher with no matching PO/invoice in scoped directory"
            ])
            writer.writerow([
                c_safe,
                "Variance Holds",
                format_financial_decimal(item.get("variance_hold_amounts", 0.0), currency=c),
                tx_count,
                "Billed variance or overpayment held pending contract amendment"
            ])
            writer.writerow([
                c_safe,
                "Potential Anomaly Amounts",
                format_financial_decimal(item.get("potential_anomaly_amounts", 0.0), currency=c),
                tx_count,
                "Partial payments, timing variances, or retention milestone deltas"
            ])

            # Disclose excessive precision amounts under a dedicated review row
            if c in excessive_by_curr and excessive_by_curr[c]["total_excessive"] > Decimal(0):
                writer.writerow([
                    c_safe,
                    "Amounts Exceeding Currency Precision",
                    format_financial_decimal(excessive_by_curr[c]["total_excessive"], currency=c),
                    excessive_by_curr[c]["count"],
                    "Monetary amounts exceeding ISO 4217 minor-unit precision; held for human review"
                ])

            writer.writerow([
                c_safe,
                "Unverified Amounts",
                format_financial_decimal(item.get("unverified_amounts", 0.0), currency=c),
                tx_count,
                "Incomplete extraction, low-resolution scan, or unverified evidence"
            ])

        # Missing currency disclosures
        for u in undoc:
            writer.writerow([
                "UNDOCUMENTED",
                "Missing Currency Disclosure",
                format_financial_decimal(u.get("unverified_amount")),
                1,
                sanitize_csv_text_cell(u.get("reason", "Missing, unextracted, or non-standard currency code."))
            ])

        # Unsupported currency disclosures from ledger (if any were not present in by_currency)
        for unsupp_row in unsupported_ledger_entries:
            unsupp_curr = unsupp_row.get("currency")
            if unsupp_curr not in by_curr:
                amt = unsupp_row.get("paid_amount") or unsupp_row.get("invoice_amount")
                writer.writerow([
                    sanitize_csv_text_cell(unsupp_curr),
                    "Unsupported Currency Disclosure",
                    format_financial_decimal(amt, currency=unsupp_curr),
                    1,
                    f"Currency code '{unsupp_curr}' is not an ISO 4217 recognized currency; excluded from verified totals."
                ])

    @classmethod
    def _render_findings_schedule(cls, writer: Any, findings: List[Dict[str, Any]]) -> None:
        headers = [
            "Finding_ID",
            "Classification",
            "Title",
            "Subject_Reference",
            "Expected_Value",
            "Observed_Value",
            "Variance_Explanation",
            "Classification_Rationale",
            "Recommended_Action",
            "Requires_Human_Review",
            "Connected_Document_IDs",
            "Source_File_Paths",
            "Missing_Evidence_Details",
            "Evidence_Limitations"
        ]
        writer.writerow(headers)

        for f in findings:
            doc_ids = f.get("source_document_ids") or []
            doc_ids_str = ", ".join(str(d) for d in doc_ids)
            paths = f.get("source_paths") or []
            paths_str = "; ".join(paths)

            writer.writerow([
                sanitize_csv_text_cell(str(f.get("finding_id", ""))),
                sanitize_csv_text_cell(f.get("classification") or "UNVERIFIED"),
                sanitize_csv_text_cell(f.get("title") or "Untitled Finding"),
                sanitize_csv_text_cell(f.get("subject_reference") or ""),
                sanitize_csv_text_cell(f.get("expected_value") or ""),
                sanitize_csv_text_cell(f.get("observed_value") or ""),
                sanitize_csv_text_cell(f.get("variance_explanation") or ""),
                sanitize_csv_text_cell(f.get("classification_rationale") or ""),
                sanitize_csv_text_cell(f.get("recommended_action") or ""),
                "Yes" if f.get("requires_human_review") else "No",
                sanitize_csv_text_cell(doc_ids_str),
                sanitize_csv_text_cell(paths_str),
                sanitize_csv_text_cell(f.get("missing_evidence_details") or ""),
                sanitize_csv_text_cell(f.get("evidence_limitations") or "")
            ])

    @classmethod
    def _render_evidence_schedule(cls, writer: Any, evidence: List[Dict[str, Any]]) -> None:
        headers = [
            "Document_ID",
            "Filename",
            "Evidence_Role",
            "Document_Type",
            "Extraction_Status",
            "Linked_Finding_IDs",
            "Scoped_Source_Path"
        ]
        writer.writerow(headers)

        for doc in evidence:
            f_ids = doc.get("linked_finding_ids") or []
            f_ids_str = ", ".join(str(fid) for fid in f_ids)

            writer.writerow([
                sanitize_csv_text_cell(str(doc.get("document_id", ""))),
                sanitize_csv_text_cell(doc.get("filename") or ""),
                sanitize_csv_text_cell(doc.get("evidence_role") or "SUPPORTING_EVIDENCE"),
                sanitize_csv_text_cell(doc.get("document_type") or "OTHER"),
                sanitize_csv_text_cell(doc.get("extraction_status") or "EXTRACTED"),
                sanitize_csv_text_cell(f_ids_str),
                sanitize_csv_text_cell(doc.get("source_path") or "")
            ])
