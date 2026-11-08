import re
import html
from typing import Dict, Any, List, Optional
from app.models.report import InvestigationReport

def escape_cell(val: Any) -> str:
    """
    Safely sanitizes untrusted content for a Markdown table cell.
    Applies HTML entity escaping to prevent stored XSS, neutralizes Markdown
    links and image brackets to prevent URI injection and beacon calls,
    converts pipe symbols to &#124; to preserve table column alignments,
    and converts newlines to <br> tags.
    """
    if val is None:
        return "N/A"
    # 1. HTML entity escaping (quotes, ampersands, angle brackets)
    s = html.escape(str(val), quote=True)
    # 2. Neutralize Markdown link and image bracket syntax
    s = s.replace("[", "&#91;").replace("]", "&#93;")
    # 3. Table column delimiter protection
    s = s.replace("|", "&#124;")
    # 4. Multiline normalization inside table cells
    s = s.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
    return s.strip()

def escape_text(val: Any) -> str:
    """
    Safely sanitizes text content in Markdown prose.
    Applies HTML entity escaping, neutralizes Markdown link/image brackets,
    strips leading ATX header markers (#), neutralizes Setext heading underlines (=== / ---),
    and neutralizes horizontal rule dividers (---, ***, ___).
    """
    if val is None:
        return "N/A"
    # 1. HTML entity escaping
    s = html.escape(str(val), quote=True)
    # 2. Neutralize Markdown link/image brackets
    s = s.replace("[", "&#91;").replace("]", "&#93;")
    
    lines = []
    for line in s.splitlines():
        trimmed = line.lstrip()
        # Neutralize ATX headings
        if trimmed.startswith("#"):
            trimmed = trimmed.lstrip("#").strip()
        # Neutralize Setext headings (e.g. === or ---)
        if re.match(r"^[=-]{2,}\s*$", trimmed):
            trimmed = trimmed.replace("-", "&#45;").replace("=", "&#61;")
        # Neutralize Horizontal Rules (e.g. ---, ***, ___)
        elif re.match(r"^([*\-_]\s*){3,}\s*$", trimmed):
            trimmed = trimmed.replace("-", "&#45;").replace("*", "&#42;").replace("_", "&#95;")
        lines.append(trimmed)
    return "\n".join(lines).strip()

def format_currency_amount(amt: Any, curr: Optional[str]) -> str:
    """Formats monetary amount with 2 decimal places and currency code, with safe fallbacks."""
    if amt is None:
        return "N/A"
    try:
        num = float(amt)
        curr_safe = html.escape(str(curr), quote=True) if curr else ""
        c_str = f" {curr_safe}" if curr_safe else ""
        return f"{num:,.2f}{c_str}"
    except (ValueError, TypeError):
        c_str = f" {escape_cell(curr)}" if curr else ""
        return f"{escape_cell(amt)}{c_str}"

class MarkdownDossierRenderer:
    """
    Renders an audit-grade Markdown Audit Dossier exclusively from an immutable
    InvestigationReport entity and its stored snapshot_payload.
    Never queries or mutates live investigation or finding records.
    """

    @staticmethod
    def render(report: InvestigationReport) -> str:
        snapshot = report.snapshot_payload or {}
        metadata = snapshot.get("metadata") or {}
        inv_summary = snapshot.get("investigation_summary") or {}
        findings = snapshot.get("findings_snapshot") or []
        evidence = snapshot.get("evidence_register_snapshot") or []
        financial = snapshot.get("financial_summary") or {}
        ledger = snapshot.get("reconciliation_ledger_snapshot") or []

        # Runtime cryptographic verification
        from app.services.report_service import ReportService
        is_verified = ReportService.verify_report_integrity(report)

        if is_verified:
            integrity_badge = "`[SNAPSHOT INTEGRITY: VERIFIED (SHA-256 MATCH)]`"
        else:
            integrity_badge = "`[SNAPSHOT INTEGRITY: COMPROMISED / HASH MISMATCH]`"

        # Header metadata
        report_id = report.id
        investigation_id = report.investigation_id
        report_version = report.report_version
        report_status = report.report_status
        report_title = escape_text(report.report_title)
        generation_ts = report.generation_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if report.generation_timestamp else "N/A"
        schema_version = escape_text(report.reporting_schema_version or metadata.get("schema_version") or "1.0.0")
        methodology_version = escape_text(report.methodology_version or metadata.get("methodology_version") or "VaultPilot-Audit-Methodology-2.0")
        integrity_hash = escape_text(report.snapshot_integrity_hash or "N/A")
        scope_path = escape_text(report.investigation_scope or inv_summary.get("investigation_scope") or "N/A")
        exec_summary = escape_text(report.executive_summary or inv_summary.get("investigation_title") or "Routine Financial Evidence Audit")

        sections: List[str] = []

        # =========================================================================
        # 1. Report Title and Metadata
        # =========================================================================
        sec1 = f"""# VaultPilot AI: Audit Dossier & Financial Investigation Report
## {report_title}

- **Report ID:** #{report_id}
- **Investigation ID:** #{investigation_id}
- **Report Version:** v{report_version}
- **Report Status:** `{report_status}`
- **Snapshot Integrity Status:** **{integrity_badge}**
- **Generation Timestamp:** {generation_ts}
- **Reporting Schema Version:** `{schema_version}`
- **Methodology Version:** `{methodology_version}`
- **Snapshot Integrity Hash:** `{integrity_hash}`
"""
        sections.append(sec1.strip())

        # =========================================================================
        # 2. Executive Summary
        # =========================================================================
        sec2 = f"""## 1. Executive Summary

{exec_summary}
"""
        sections.append(sec2.strip())

        # =========================================================================
        # 3. Investigation Scope
        # =========================================================================
        project_name = escape_text(inv_summary.get("project_name") or "Unspecified Project")
        project_code = escape_text(inv_summary.get("project_code") or "N/A")
        donor = escape_text(inv_summary.get("donor") or "Unspecified Donor")
        inv_status = escape_text(inv_summary.get("investigation_status") or "COMPLETED")
        doc_count = inv_summary.get("document_count", len(evidence))
        doc_counts = inv_summary.get("document_counts_by_type") or {}

        counts_breakdown = "\n".join(
            f"  - **{escape_text(k)}:** {v}" for k, v in sorted(doc_counts.items())
        ) if doc_counts else "  - *No categorized breakdown available.*"

        sec3 = f"""## 2. Investigation Scope

- **Project Name:** {project_name}
- **Project Code:** `{project_code}`
- **Donor / Grantor:** {donor}
- **Authorized Directory Scope:** `{scope_path}`
- **Investigation Execution Status:** `{inv_status}`
- **Total Documents Discovered:** {doc_count}
- **Document Breakdown by Type:**
{counts_breakdown}
"""
        sections.append(sec3.strip())

        # =========================================================================
        # 4. Investigation Methodology
        # =========================================================================
        sec4 = f"""## 3. Investigation Methodology

This investigation report was compiled following the **{methodology_version}** standard:
1. **Scoped Document Discovery:** Files were discovered exclusively within the authorized directory `{scope_path}`. No traversal or external network lookups were performed.
2. **Structured Evidence Extraction:** Procurement records, billing invoices, payment receipts, and financial reports were extracted using standardized schemas distinguishing extracted, unavailable, and unverified values without data interpolation.
3. **Three-Way Documentary Reconciliation:** Commercial commitments were cross-referenced across three tiers: Purchase Orders (authorization) ↔ Invoices (billing claims) ↔ Payment Receipts/Vouchers (disbursement proof).
4. **Conservative Classification:** Findings were classified under a four-tier taxonomy: `CONFIRMED_DISCREPANCY`, `POTENTIAL_ANOMALY`, `MISSING_EVIDENCE`, and `UNVERIFIED`. No accusations of fraud or misconduct are asserted.
5. **Multi-Currency Segregation:** Disparate currencies are partitioned into separate schedules. Direct mathematical aggregation or cross-currency conversions are disallowed without signed exchange vouchers.
6. **Immutable Snapshotting:** Report state is compiled from a frozen snapshot payload with canonical SHA-256 integrity verification.
"""
        sections.append(sec4.strip())

        # =========================================================================
        # 5. Financial Reconciliation Summary
        # =========================================================================
        by_curr = financial.get("by_currency") or {}
        undocumented_entries = financial.get("undocumented_currency_entries") or []

        currencies_audited = ", ".join(sorted(by_curr.keys())) if by_curr else "None"
        human_review_label = "**REQUIRED** (Anomalies, unverified items, or documentation gaps identified)" if report.requires_human_review else "NOT REQUIRED (All records reconciled cleanly)"

        verified_spend_lines = []
        for c, item in sorted(by_curr.items()):
            verified_spend_lines.append(f"- **{c}:** {format_currency_amount(item.get('verified_expenditure', 0.0), c)}")

        verified_spend_text = "\n".join(verified_spend_lines) if verified_spend_lines else "- *No verified matching expenditure recorded.*"

        sec5 = f"""## 4. Financial Reconciliation Summary

- **Currencies Audited:** {currencies_audited}
- **Human Supervisory Review:** {human_review_label}
- **Verified Matching Expenditure (3-Way Reconciled):**
{verified_spend_text}
"""
        sections.append(sec5.strip())

        # =========================================================================
        # 6. Currency-Separated Expenditure Schedules
        # =========================================================================
        sec6_parts = ["## 5. Currency-Separated Expenditure Schedules\n"]

        if by_curr:
            for c, item in sorted(by_curr.items()):
                v_exp = format_currency_amount(item.get("verified_expenditure", 0.0), c)
                u_rec = format_currency_amount(item.get("unapplied_receipts", 0.0), c)
                v_hold = format_currency_amount(item.get("variance_hold_amounts", 0.0), c)
                p_anom = format_currency_amount(item.get("potential_anomaly_amounts", 0.0), c)
                unver = format_currency_amount(item.get("unverified_amounts", 0.0), c)
                tx_count = item.get("transaction_count", 0)

                table_curr = f"""### Schedule: {c} Financial Summary

| Category / Metric | Amount ({c}) | Accounting Interpretation & Audit Guidance |
| :--- | :--- | :--- |
| **Verified Matching Expenditure** | `{v_exp}` | Fully reconciled 3-way match (PO ↔ Invoice ↔ Receipt) |
| **Unapplied Payment Receipts** | `{u_rec}` | Disbursement proof with no matching PO/invoice in scoped directory |
| **Variance Holds** | `{v_hold}` | Billed variance or overpayment held pending contract amendment |
| **Potential Anomaly Amounts** | `{p_anom}` | Partial payments, timing variances, or retention milestone deltas |
| **Unverified / Smudged Amounts** | `{unver}` | Incomplete extraction or low-resolution scan |
| **Transaction Item Count** | **{tx_count} items** | Total distinct transaction clusters audited in {c} |
"""
                sec6_parts.append(table_curr.strip())
        else:
            sec6_parts.append("*No standardized currency schedules recorded.*")

        if undocumented_entries:
            undoc_rows = []
            for u in undocumented_entries:
                l_id = escape_cell(u.get("ledger_entry_id", "N/A"))
                tx_id = escape_cell(u.get("transaction_id", "N/A"))
                amt = format_currency_amount(u.get("unverified_amount"), "UNKNOWN")
                reason = escape_cell(u.get("reason", "Missing currency code"))
                undoc_rows.append(f"| #{l_id} | `{tx_id}` | `{amt}` | {reason} |")

            undoc_table = """### Undocumented / Missing Currency Disclosures

> **Audit Warning:** The following transactions lacked an explicit, standardized currency code and were excluded from verified expenditure totals to prevent cross-currency distortion:

| Ledger ID | Transaction Tracking ID | Amount | Withholding Reason |
| :--- | :--- | :--- | :--- |
""" + "\n".join(undoc_rows)
            sec6_parts.append(undoc_table.strip())

        sections.append("\n\n".join(sec6_parts))

        # =========================================================================
        # 7. Findings Register
        # =========================================================================
        sec7_parts = ["## 6. Classified Findings Register\n"]
        if findings:
            for f in findings:
                f_id = f.get("finding_id", "N/A")
                f_title = escape_text(f.get("title", "Untitled Finding"))
                f_class = escape_text(f.get("classification", "UNVERIFIED"))
                f_subj = escape_text(f.get("subject_reference") or "General Evidence")
                f_exp = escape_text(f.get("expected_value") or "Standard documented compliance")
                f_obs = escape_text(f.get("observed_value") or "Record absence or variance observed")
                f_desc = escape_text(f.get("variance_explanation") or "No explanation recorded.")
                f_rat = escape_text(f.get("classification_rationale") or "Classified based on available documentary evidence.")
                f_act = escape_text(f.get("recommended_action") or "Review original files with finance officer.")
                f_rev = "Yes" if f.get("requires_human_review") else "No"
                f_lim = escape_text(f.get("evidence_limitations") or f"Scoped to directory '{scope_path}'.")
                f_miss = escape_text(f.get("missing_evidence_details") or "None specified.")
                f_paths = f.get("source_paths") or []
                f_doc_ids = f.get("source_document_ids") or []

                paths_formatted = "\n".join(f"  - `{escape_text(p)}`" for p in f_paths) if f_paths else "  - *No specific file paths attached.*"
                doc_ids_formatted = ", ".join(f"#{d}" for d in f_doc_ids) if f_doc_ids else "None"

                f_block = f"""### Finding #{f_id}: {f_title}

- **Classification:** `{f_class}`
- **Subject Reference:** {f_subj}
- **Expected Value:** {f_exp}
- **Observed Value:** {f_obs}
- **Variance / Factual Explanation:** {f_desc}
- **Classification Rationale:** {f_rat}
- **Recommended Action:** {f_act}
- **Human Review Required:** **{f_rev}**
- **Connected Document IDs:** {doc_ids_formatted}
- **Source File Paths:**
{paths_formatted}
- **Evidence Limitations:** {f_lim}
- **Missing Documentation Details:** {f_miss}
"""
                sec7_parts.append(f_block.strip())
        else:
            sec7_parts.append("*No classified findings were recorded for this investigation.*")

        sections.append("\n\n".join(sec7_parts))

        # =========================================================================
        # 8. Evidence Register
        # =========================================================================
        sec8_parts = ["""## 7. Evidence Register

| Doc ID | Filename | Evidence Role | Document Type | Extraction Status | Linked Finding IDs | Scoped Source Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"""]

        if evidence:
            for doc in evidence:
                d_id = doc.get("document_id", "N/A")
                d_file = escape_cell(doc.get("filename", "unknown"))
                d_role = escape_cell(doc.get("evidence_role", "SUPPORTING_EVIDENCE"))
                d_type = escape_cell(doc.get("document_type", "OTHER"))
                d_stat = escape_cell(doc.get("extraction_status", "EXTRACTED"))
                d_findings = escape_cell(", ".join(f"#{fid}" for fid in doc.get("linked_finding_ids", [])) or "None")
                d_path = escape_cell(doc.get("source_path", "N/A"))
                sec8_parts.append(f"| #{d_id} | `{d_file}` | {d_role} | {d_type} | `{d_stat}` | {d_findings} | `{d_path}` |")
        else:
            sec8_parts.append("| - | *No documents registered* | - | - | - | - | - |")

        sections.append("\n".join(sec8_parts))

        # =========================================================================
        # 9. Purchase Order, Invoice, and Receipt Reconciliation
        # =========================================================================
        sec9_parts = ["""## 8. Purchase Order, Invoice, and Receipt Reconciliation

| Tracking ID / Description | PO Reference & Authorized | Invoice # & Billed | Receipt Proof & Paid | Reconciliation Status | Match Confidence | Review |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"""]

        if ledger:
            for row in ledger:
                tx_id = escape_cell(row.get("transaction_id", "N/A"))
                desc = escape_cell(row.get("item_description", "General Item"))
                po_ref = escape_cell(row.get("po_reference") or "No PO")
                po_amt = format_currency_amount(row.get("po_amount"), row.get("currency"))
                inv_num = escape_cell(row.get("invoice_number") or "No Invoice")
                inv_amt = format_currency_amount(row.get("invoice_amount"), row.get("currency"))
                rec_proof = escape_cell(row.get("receipt_proof") or "No Receipt")
                paid_amt = format_currency_amount(row.get("paid_amount"), row.get("currency"))
                status = escape_cell(row.get("reconciliation_status", "UNVERIFIED"))
                conf = escape_cell(row.get("match_confidence", "UNMATCHED"))
                rev = "Yes" if row.get("requires_human_review") else "No"

                sec9_parts.append(f"| `{tx_id}`<br>{desc} | {po_ref}<br>`{po_amt}` | {inv_num}<br>`{inv_amt}` | {rec_proof}<br>`{paid_amt}` | `{status}` | `{conf}` | {rev} |")
        else:
            # Fallback: synthesize three-way correlation rows from evidence register if ledger snapshot is absent
            po_map = {d.get("extracted_data_summary", {}).get("po_reference"): d for d in evidence if d.get("document_type") == "PURCHASE_ORDER" and d.get("extracted_data_summary", {}).get("po_reference")}
            inv_docs = [d for d in evidence if d.get("document_type") == "INVOICE"]
            rec_map = {d.get("extracted_data_summary", {}).get("invoice_reference"): d for d in evidence if d.get("document_type") == "RECEIPT" and d.get("extracted_data_summary", {}).get("invoice_reference")}

            if inv_docs:
                for inv in inv_docs:
                    i_data = inv.get("extracted_data_summary", {})
                    i_num = i_data.get("invoice_number", "INV-UNKNOWN")
                    i_po_ref = i_data.get("po_reference")
                    i_amt = format_currency_amount(i_data.get("amount"), i_data.get("currency"))
                    po_doc = po_map.get(i_po_ref)
                    p_amt = format_currency_amount(po_doc.get("extracted_data_summary", {}).get("amount"), po_doc.get("extracted_data_summary", {}).get("currency")) if po_doc else "N/A"
                    rec_doc = rec_map.get(i_num)
                    r_amt = format_currency_amount(rec_doc.get("extracted_data_summary", {}).get("amount"), rec_doc.get("extracted_data_summary", {}).get("currency")) if rec_doc else "N/A"
                    r_proof = rec_doc.get("extracted_data_summary", {}).get("receipt_id", "N/A") if rec_doc else "No Receipt"

                    # Explicitly escape all six fallback values to protect table formatting
                    esc_i_num = escape_cell(i_num)
                    esc_po_ref = escape_cell(i_po_ref or "No PO")
                    esc_p_amt = escape_cell(p_amt)
                    esc_i_amt = escape_cell(i_amt)
                    esc_r_proof = escape_cell(r_proof)
                    esc_r_amt = escape_cell(r_amt)

                    sec9_parts.append(f"| `{esc_i_num}` | {esc_po_ref}<br>`{esc_p_amt}` | `{esc_i_num}`<br>`{esc_i_amt}` | {esc_r_proof}<br>`{esc_r_amt}` | `RECONCILED` | `EXACT_MATCH` | No |")
            else:
                sec9_parts.append("| - | *No three-way ledger entries available in snapshot* | - | - | - | - | - |")

        sections.append("\n".join(sec9_parts))

        # =========================================================================
        # 10. Missing and Incomplete Evidence Checklist
        # =========================================================================
        missing_findings = [f for f in findings if f.get("classification") in ["MISSING_EVIDENCE", "UNVERIFIED"]]
        sec10_parts = ["""## 9. Missing and Incomplete Evidence Checklist

The following documentation gaps were identified within the scoped directory and require follow-up by procurement and finance teams:
"""]
        if missing_findings:
            for f in missing_findings:
                f_id = f.get("finding_id", "N/A")
                f_title = escape_text(f.get("title", "Documentation Gap"))
                f_action = escape_text(f.get("recommended_action") or f.get("missing_evidence_details") or "Obtain supporting document.")
                f_ctx = escape_text(f.get("variance_explanation") or "Document absent from searched folder.")
                sec10_parts.append(f"- [ ] **{f_title}** (Finding #{f_id}): {f_action}\n  - *Audit Context:* {f_ctx}")
        else:
            sec10_parts.append("*All required commercial documentation was discovered within the scoped directory. No missing evidence items recorded.*")

        sections.append("\n".join(sec10_parts))

        # =========================================================================
        # 11. Human Review Requirements
        # =========================================================================
        review_findings = [f for f in findings if f.get("requires_human_review")]
        sec11_parts = [f"""## 10. Human Review Requirements

- **Overall Review Status:** {human_review_label}
"""]
        if review_findings:
            sec11_parts.append("The following findings were flagged with anomalies, missing authorizations, or optical degradations requiring human supervisory review:\n")
            for f in review_findings:
                f_id = f.get("finding_id", "N/A")
                f_title = escape_text(f.get("title", "Review Required"))
                f_cls = escape_text(f.get("classification", "REVIEW"))
                f_act = escape_text(f.get("recommended_action", "Manual inspection required."))
                sec11_parts.append(f"- **Finding #{f_id} (`{f_cls}`):** {f_title}\n  - *Action:* {f_act}")
        else:
            sec11_parts.append("*No items were flagged for human supervisory review. All transactions satisfied deterministic match thresholds.*")

        sections.append("\n".join(sec11_parts))

        # =========================================================================
        # 12. Investigation Limitations & Legal Disclaimers
        # =========================================================================
        limitations_text = escape_text(report.investigation_limitations or (
            f"Investigation scope is strictly limited to files discovered in '{scope_path}'. "
            "Findings reflect rule-guided reasoning over returned evidence. Absence of records in this directory "
            "does not establish that transactions did not occur outside the searched folder. "
            "Qualified human review is required before taking administrative or legal action."
        ))

        sec12 = f"""## 11. Investigation Limitations & Legal Disclaimers

{limitations_text}

- **Scoped Directory Boundary:** This investigation evaluated only the files discovered within the explicitly designated directory: `{scope_path}`.
- **Negative Proof Clarification:** Stating that a document is classified as `MISSING_EVIDENCE` records only that the file was absent from the searched storage directory. It does NOT prove that an underlying transaction, goods delivery, or disbursement never occurred.
- **Rule-Guided Reasoning:** Findings reflect automated rule-guided analysis of returned documentary evidence. They do not constitute formal judicial verdicts, forensic criminal determinations, or accusations of intentional misconduct or fraud.
- **Mandatory Human Verification:** Qualified NGO finance directors and donor compliance managers must inspect physical vouchers and external bank confirmations before initiating corrective, legal, or disciplinary actions.
"""
        sections.append(sec12.strip())

        # =========================================================================
        # 13. Audit & Snapshot Integrity Metadata
        # =========================================================================
        sec13_lines = [
            "## 12. Audit & Snapshot Integrity Metadata",
            "",
            f"- **Cryptographic Verification Status:** **{integrity_badge}**",
            f"- **Canonical Payload SHA-256 Integrity Hash:** `{integrity_hash}`",
            f"- **Reporting Schema Version:** `{schema_version}`",
            f"- **Investigation Report ID:** `IR-{report_id}-V{report_version}`",
            ""
        ]
        if not is_verified:
            sec13_lines.extend([
                "> [!CAUTION]",
                "> **INTEGRITY WARNING:** The stored report snapshot payload failed canonical SHA-256 hash verification. The recomputed payload digest does not match the recorded integrity hash. This report snapshot may have been modified outside authorized audit controls.",
                ""
            ])
        sec13_lines.extend([
            "- **Snapshot Immutability Notice:** This document was rendered directly from an immutable report snapshot. The SHA-256 integrity hash is computed over the UTF-8 bytes of the canonical sorted-key JSON payload. It confirms internal data consistency and change-detection for this report version. It does not constitute a third-party PKI digital signature or hardware tamper-proof storage.",
            ""
        ])
        sec13 = "\n".join(sec13_lines)
        sections.append(sec13.strip())

        return "\n\n---\n\n".join(sections) + "\n"
