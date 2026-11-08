import html
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.models.report import InvestigationReport
from app.services.csv_exporter import (
    ReportIntegrityError,
    validate_financial_decimal,
    format_financial_decimal,
    is_currency_recognized,
    has_excessive_precision,
    RECOGNIZED_CURRENCIES
)

def escape_html(val: Any) -> str:
    """
    Safely sanitizes dynamic content for HTML presentation and attribute context.
    Escapes &, <, >, \", and ' to neutralize Stored XSS and attribute injection.
    """
    if val is None:
        return ""
    return html.escape(str(val), quote=True)

def format_html_currency(amt: Any, currency: Optional[str] = None) -> str:
    """
    Formats a validated monetary amount into a clean HTML presentation string.
    Preserves exact sub-cent digits for sub-cent values without rounding.
    Returns &mdash; for missing or invalid values.
    """
    if amt is None or amt == "":
        return "&mdash;"
    d = validate_financial_decimal(amt, currency=currency)
    if d is None:
        return escape_html(str(amt))
    
    val_str = str(d)
    curr_str = f" {escape_html(currency)}" if currency else ""
    return f"{val_str}{curr_str}"

class HTMLDossierRenderer:
    """
    Renders an audit-grade, publication-ready, self-contained printable HTML
    financial investigation dossier exclusively from an immutable InvestigationReport
    entity and its stored snapshot_payload.
    
    Enforces fail-closed cryptographic integrity verification before generating any content.
    Includes print-optimized CSS for browser-native PDF export via window.print().
    """

    @classmethod
    def render(cls, report: InvestigationReport) -> str:
        """
        Renders the report snapshot as a self-contained, printable HTML5 dossier.
        Refuses generation (raises ReportIntegrityError) if the snapshot fails SHA-256 verification.
        """
        if not report or not report.snapshot_payload or not report.snapshot_integrity_hash:
            raise ReportIntegrityError(
                "REPORT_INTEGRITY_VERIFICATION_FAILED: Report record has no cryptographic integrity hash or snapshot payload."
            )

        from app.services.report_service import ReportService
        if not ReportService.verify_report_integrity(report):
            raise ReportIntegrityError(
                "REPORT_INTEGRITY_VERIFICATION_FAILED: Stored snapshot payload failed SHA-256 integrity verification. "
                "HTML dossier generation refused."
            )

        snapshot = report.snapshot_payload or {}
        metadata = snapshot.get("metadata") or {}
        inv_summary = snapshot.get("investigation_summary") or {}
        findings = snapshot.get("findings_snapshot") or []
        evidence = snapshot.get("evidence_register_snapshot") or []
        financial = snapshot.get("financial_summary") or {}
        ledger = snapshot.get("reconciliation_ledger_snapshot") or []

        # Extract Report Metadata
        report_id = escape_html(report.id)
        report_title = escape_html(report.report_title or "Financial Evidence Investigation Dossier")
        report_version = escape_html(report.report_version)
        report_status = escape_html(report.report_status or "FINAL")
        generation_ts = report.generation_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if report.generation_timestamp else "N/A"
        schema_version = escape_html(report.reporting_schema_version or metadata.get("schema_version") or "1.0.0")
        methodology_version = escape_html(report.methodology_version or metadata.get("methodology_version") or "VaultPilot-Audit-Methodology-2.0")
        integrity_hash = escape_html(report.snapshot_integrity_hash)
        scope_path = escape_html(report.investigation_scope or inv_summary.get("investigation_scope") or "N/A")
        exec_summary = escape_html(report.executive_summary or inv_summary.get("investigation_title") or "Routine Financial Evidence Audit")

        project_name = escape_html(inv_summary.get("project_name") or "Unspecified Project")
        project_code = escape_html(inv_summary.get("project_code") or "N/A")
        donor = escape_html(inv_summary.get("donor") or "Unspecified Donor")
        inv_status = escape_html(inv_summary.get("investigation_status") or "COMPLETED")
        doc_count = inv_summary.get("document_count", len(evidence))
        doc_counts = inv_summary.get("document_counts_by_type") or {}

        # Financial Summary data
        by_curr = financial.get("by_currency") or {}
        undoc_entries = financial.get("undocumented_currency_entries") or []

        # Build Document Breakdown List
        doc_counts_html = "".join(
            f"<li><strong>{escape_html(k)}:</strong> {escape_html(v)} files</li>"
            for k, v in sorted(doc_counts.items())
        ) if doc_counts else "<li><em>No categorized breakdown available.</em></li>"

        currencies_audited_str = escape_html(', '.join(sorted(by_curr.keys())) if by_curr else 'None')
        if report.requires_human_review:
            review_status_badge = '<strong style="color:#b45309;">REQUIRED (Documentation gaps or anomalies detected)</strong>'
        else:
            review_status_badge = '<strong>NOT REQUIRED (All records reconciled cleanly)</strong>'
        verified_spend_items = []
        for c, item in sorted(by_curr.items()):
            if is_currency_recognized(c):
                v_exp = format_html_currency(item.get("verified_expenditure", 0.0), c)
                verified_spend_items.append(f"<li><strong>{escape_html(c)}:</strong> <code>{v_exp}</code></li>")
        verified_spend_html = "".join(verified_spend_items) if verified_spend_items else "<li><em>No verified matching expenditure recorded.</em></li>"

        # Build Currency Schedules HTML
        currency_schedules_html = cls._build_currency_schedules_html(by_curr, undoc_entries, ledger)

        # Build Findings Cards HTML
        findings_cards_html = cls._build_findings_cards_html(findings, scope_path)

        # Build Evidence Table HTML
        evidence_table_html = cls._build_evidence_table_html(evidence)

        # Build Reconciliation Matrix HTML
        reconciliation_matrix_html = cls._build_reconciliation_matrix_html(ledger, evidence)

        # Build Checklist HTML
        missing_checklist_html = cls._build_missing_checklist_html(findings)

        # Build Review Requirements HTML
        review_reqs_html = cls._build_review_requirements_html(findings, report.requires_human_review)

        # Build Full HTML5 Document
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none'; frame-ancestors 'none'; base-uri 'none';">
    <title>VaultPilot AI — Audit Dossier #{report_id} (v{report_version})</title>
    <style>
        /* =========================================================================
           1. System Typography & Core Resets
           ========================================================================= */
        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        html, body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #0f172a;
            background-color: #f8fafc;
            line-height: 1.5;
            font-size: 14px;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        .container {{
            max-width: 1040px;
            margin: 24px auto;
            background: #ffffff;
            padding: 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }}

        /* =========================================================================
           2. Print Button Banner (Screen Only)
           ========================================================================= */
        .action-banner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            padding: 12px 20px;
            border-radius: 6px;
            margin-bottom: 24px;
        }}
        .action-banner p {{
            font-size: 13px;
            color: #475569;
        }}
        .print-btn {{
            background: #0f172a;
            color: #ffffff;
            border: none;
            padding: 8px 18px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .print-btn:hover {{
            background: #1e293b;
        }}

        /* =========================================================================
           3. Dossier Header & Metadata
           ========================================================================= */
        header.dossier-header {{
            border-bottom: 2px solid #0f172a;
            padding-bottom: 20px;
            margin-bottom: 28px;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        .brand-title {{
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.02em;
        }}
        .brand-subtitle {{
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .report-h1 {{
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            margin-top: 8px;
        }}
        
        .integrity-banner {{
            display: inline-flex;
            align-items: center;
            background: #ecfdf5;
            color: #065f46;
            border: 1px solid #a7f3d0;
            padding: 6px 14px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            margin-top: 10px;
            letter-spacing: 0.02em;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 16px;
            border-radius: 6px;
            margin-top: 16px;
        }}
        .meta-item {{
            font-size: 12px;
        }}
        .meta-label {{
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.05em;
            display: block;
            margin-bottom: 2px;
        }}
        .meta-value {{
            font-weight: 600;
            color: #0f172a;
        }}

        /* =========================================================================
           4. Section Layouts & Typography
           ========================================================================= */
        section.dossier-section {{
            margin-bottom: 32px;
        }}
        h2.section-heading {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 6px;
            margin-bottom: 14px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        h3.subsection-heading {{
            font-size: 14px;
            font-weight: 600;
            color: #1e293b;
            margin: 16px 0 8px 0;
        }}
        p, li {{
            color: #334155;
            font-size: 13px;
        }}
        ul {{
            padding-left: 20px;
            margin: 8px 0;
        }}
        code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            background: #f1f5f9;
            color: #0f172a;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 12px;
            border: 1px solid #e2e8f0;
        }}

        /* =========================================================================
           5. Tables & Registers
           ========================================================================= */
        table.dossier-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin: 12px 0;
        }}
        table.dossier-table th {{
            background: #f1f5f9;
            color: #334155;
            font-weight: 600;
            text-align: left;
            padding: 8px 10px;
            border: 1px solid #cbd5e1;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        table.dossier-table td {{
            padding: 7px 10px;
            border: 1px solid #e2e8f0;
            color: #1e293b;
            vertical-align: top;
        }}
        table.dossier-table tr:nth-child(even) {{
            background: #fafafa;
        }}

        /* =========================================================================
           6. Status Badges & Pill Styling
           ========================================================================= */
        .pill {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }}
        .pill-reconciled {{ background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }}
        .pill-discrepancy {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
        .pill-anomaly {{ background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }}
        .pill-missing {{ background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
        .pill-unverified {{ background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; }}

        /* =========================================================================
           7. Finding Cards
           ========================================================================= */
        .finding-card {{
            border: 1px solid #cbd5e1;
            border-left: 4px solid #0f172a;
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 16px;
            background: #ffffff;
        }}
        .finding-card.discrepancy {{ border-left-color: #dc2626; }}
        .finding-card.anomaly {{ border-left-color: #d97706; }}
        .finding-card.missing {{ border-left-color: #475569; }}
        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 8px;
        }}
        .finding-title {{
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
        }}
        .finding-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px 16px;
            font-size: 12px;
        }}
        .finding-full {{
            grid-column: span 2;
            font-size: 12px;
            margin-top: 4px;
        }}

        /* =========================================================================
           8. Warning & Notice Callouts
           ========================================================================= */
        .callout-warning {{
            background: #fffbeb;
            border-left: 4px solid #d97706;
            padding: 12px 16px;
            border-radius: 0 4px 4px 0;
            margin: 14px 0;
            font-size: 12px;
            color: #92400e;
        }}
        .callout-warning strong {{
            color: #78350f;
        }}

        /* =========================================================================
           9. Attestation & Signature Blocks
           ========================================================================= */
        .signature-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
            margin-top: 24px;
            padding-top: 16px;
        }}
        .signature-box {{
            border-top: 1px solid #0f172a;
            padding-top: 8px;
        }}
        .signature-title {{
            font-weight: 600;
            font-size: 12px;
            color: #0f172a;
        }}
        .signature-sub {{
            font-size: 11px;
            color: #64748b;
        }}

        /* =========================================================================
           10. Print Optimization Rules (@media print)
           ========================================================================= */
        @page {{
            size: A4 portrait;
            margin: 15mm 15mm 15mm 15mm;
        }}
        @media print {{
            html, body {{
                background: #ffffff !important;
                color: #0f172a !important;
                font-size: 9.5pt;
                line-height: 1.35;
            }}
            .container {{
                max-width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                box-shadow: none !important;
                border-radius: 0 !important;
            }}
            .no-print {{
                display: none !important;
            }}
            .avoid-break, .finding-card, .meta-grid, tr, .signature-box {{
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }}
            thead {{
                display: table-header-group !important;
            }}
            h1, h2, h3, h4 {{
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            .page-break-before {{
                page-break-before: always !important;
                break-before: always !important;
            }}
        }}
    </style>
</head>
<body>

<div class="container">

    <!-- Screen Action Banner -->
    <div class="action-banner no-print">
        <div>
            <strong>VaultPilot AI &mdash; Official Audit Dossier</strong>
            <p>Formatted for executive presentation, internal compliance review, and browser-native printing to PDF.</p>
        </div>
        <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
    </div>

    <!-- 1. Dossier Header & Report Metadata -->
    <header class="dossier-header">
        <div class="header-top">
            <div>
                <div class="brand-title">VaultPilot AI</div>
                <div class="brand-subtitle">Intelligent Financial Evidence Investigation Dossier</div>
                <div class="report-h1">{report_title}</div>
            </div>
            <div>
                <span class="integrity-banner">
                    &#10004; SNAPSHOT INTEGRITY: VERIFIED
                </span>
            </div>
        </div>

        <div class="meta-grid">
            <div class="meta-item">
                <span class="meta-label">Report ID</span>
                <span class="meta-value">IR-{report_id}-V{report_version}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Investigation ID</span>
                <span class="meta-value">#{escape_html(report.investigation_id)}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Report Status</span>
                <span class="meta-value">{report_status}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Generated Timestamp</span>
                <span class="meta-value">{generation_ts}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Project Code</span>
                <span class="meta-value">{project_code}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Donor / Grantor</span>
                <span class="meta-value">{donor}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Methodology Version</span>
                <span class="meta-value">{methodology_version}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Schema Version</span>
                <span class="meta-value">{schema_version}</span>
            </div>
        </div>
    </header>

    <!-- 2. Executive Summary -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">1. Executive Summary</h2>
        <p>{exec_summary}</p>
    </section>

    <!-- 3. Investigation Scope -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">2. Investigation Scope &amp; Documentary Universe</h2>
        <p><strong>Project Name:</strong> {project_name} (Code: <code>{project_code}</code>)</p>
        <p><strong>Authorized Scope Path:</strong> <code>{scope_path}</code></p>
        <p><strong>Execution Status:</strong> <code>{inv_status}</code> &mdash; Total Documents Discovered: <strong>{doc_count}</strong></p>
        <h3 class="subsection-heading">Document Distribution by Role & Type</h3>
        <ul>
            {doc_counts_html}
        </ul>
    </section>

    <!-- 4. Investigation Methodology -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">3. Investigation Methodology</h2>
        <p>This investigation report was compiled adhering strictly to the <strong>{methodology_version}</strong> standard:</p>
        <ul>
            <li><strong>Bounded Discovery:</strong> Records evaluated were gathered exclusively within authorized scope <code>{scope_path}</code> without external network lookups or speculative path traversal.</li>
            <li><strong>Evidence Provenance:</strong> Every transaction amount requires verifiable documentary backing; every finding links directly to primary extracted documents.</li>
            <li><strong>Three-Way Documentary Reconciliation:</strong> Commercial commitments were cross-referenced across three tiers: Purchase Orders (authorization) &harr; Invoices (billing claims) &harr; Payment Receipts/Vouchers (disbursement proof).</li>
            <li><strong>Conservative Classification:</strong> Findings are classified under an objective four-tier taxonomy: <code>CONFIRMED_DISCREPANCY</code>, <code>POTENTIAL_ANOMALY</code>, <code>MISSING_EVIDENCE</code>, and <code>UNVERIFIED</code>. No accusations of intentional misconduct or criminal fraud are made.</li>
            <li><strong>Multi-Currency Segregation:</strong> Disparate currencies are maintained strictly segregated. Unverified cross-currency conversions are disallowed.</li>
            <li><strong>Immutable Snapshotting:</strong> Report evidence is compiled from an immutable payload cryptographically sealed with a SHA-256 hash.</li>
        </ul>
    </section>

    <!-- 5. Financial Reconciliation Summary -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">4. Financial Reconciliation Summary</h2>
        <p><strong>Currencies Audited:</strong> {currencies_audited_str}</p>
        <p><strong>Human Supervisory Review:</strong> {review_status_badge}</p>
        <h3 class="subsection-heading">Verified Matching Expenditure (Fully Reconciled 3-Way Match)</h3>
        <ul>
            {verified_spend_html}
        </ul>
    </section>

    <!-- 6. Currency-Separated Expenditure Schedules -->
    <section class="dossier-section">
        <h2 class="section-heading">5. Currency-Separated Expenditure Schedules</h2>
        {currency_schedules_html}
    </section>

    <!-- 7. Classified Findings Register -->
    <section class="dossier-section">
        <h2 class="section-heading">6. Classified Findings Register</h2>
        {findings_cards_html}
    </section>

    <!-- 8. Evidence Register -->
    <section class="dossier-section">
        <h2 class="section-heading">7. Primary Evidence Register</h2>
        {evidence_table_html}
    </section>

    <!-- 9. Three-Way Reconciliation Matrix -->
    <section class="dossier-section">
        <h2 class="section-heading">8. Three-Way Documentary Reconciliation Matrix</h2>
        {reconciliation_matrix_html}
    </section>

    <!-- 10. Missing Evidence Checklist -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">9. Missing and Incomplete Evidence Checklist</h2>
        {missing_checklist_html}
    </section>

    <!-- 11. Human Supervisory Review Requirements -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">10. Human Supervisory Review Requirements</h2>
        {review_reqs_html}
    </section>

    <!-- 12. Investigation Limitations & Disclaimers -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">11. Investigation Limitations &amp; Legal Disclaimers</h2>
        <p>Investigation scope is strictly limited to records discovered in <code>{scope_path}</code>. Findings reflect rule-guided reasoning over returned evidence.</p>
        <ul>
            <li><strong>Negative Proof Clarification:</strong> Classifying an item as <code>MISSING_EVIDENCE</code> confirms only that the file was absent from the authorized storage folder. It does not establish that underlying goods deliveries or payments never occurred.</li>
            <li><strong>Non-Accusatory Rule-Guided Reasoning:</strong> Automated findings do not constitute judicial verdicts, criminal accusations, or conclusions of intentional malfeasance.</li>
            <li><strong>Mandatory Human Governance:</strong> Qualified NGO finance directors, donor compliance officers, and internal auditors must inspect physical documentation before initiating administrative or legal action.</li>
        </ul>
    </section>

    <!-- 13. Cryptographic Verification & Audit Trail -->
    <section class="dossier-section avoid-break">
        <h2 class="section-heading">12. Cryptographic Integrity &amp; Attestation Sign-Off</h2>
        <p><strong>Canonical Snapshot SHA-256 Digest:</strong> <code>{integrity_hash}</code></p>
        <p><strong>Verification Status:</strong> <span class=\"pill pill-reconciled\">VERIFIED (MATCH)</span> &mdash; Report Snapshot Payload matches canonical digest.</p>
        <p style=\"font-size: 11px; color: #64748b; margin-top: 6px;\">
            This document was rendered directly from an immutable report snapshot. The SHA-256 integrity hash is computed over the UTF-8 bytes of the canonical sorted JSON payload.
        </p>

        <div class="signature-grid">
            <div class="signature-box">
                <div class="signature-title">Lead Financial Investigator</div>
                <div class="signature-sub">VaultPilot AI Automated Audit Engine</div>
                <div class="signature-sub">Attestation Date: {generation_ts}</div>
            </div>
            <div class="signature-box">
                <div class="signature-title">NGO Finance Director / Compliance Officer</div>
                <div class="signature-sub">Supervisory Review & Sign-Off</div>
                <div class="signature-sub">Approval Date: ________________________</div>
            </div>
        </div>
    </section>

</div>

</body>
</html>
"""
        return html_doc

    @classmethod
    def render_bytes(cls, report: InvestigationReport) -> bytes:
        """Exports the rendered HTML dossier as UTF-8 encoded bytes."""
        text = cls.render(report)
        return text.encode("utf-8")

    # =========================================================================
    # Internal Section Builders
    # =========================================================================

    @classmethod
    def _build_currency_schedules_html(
        cls,
        by_curr: Dict[str, Any],
        undoc: List[Dict[str, Any]],
        ledger: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        parts: List[str] = []

        # Audit ledger for excessive precision or unsupported currencies
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

        if by_curr:
            for c, item in sorted(by_curr.items()):
                if not is_currency_recognized(c):
                    # Unsupported currency
                    unsupp_amt = item.get("verified_expenditure", 0.0) + item.get("unverified_amounts", 0.0)
                    parts.append(f"""
                    <div class="callout-warning avoid-break">
                        <strong>Unsupported Currency Disclosure ({escape_html(c)}):</strong>
                        Amount <code>{format_html_currency(unsupp_amt, c)}</code> is not an ISO 4217 recognized currency.
                        Excluded from verified expenditure totals pending compliance review.
                    </div>
                    """)
                    continue

                tx_count = item.get("transaction_count", 0)

                # Clean verified expenditure excluding excessive precision
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

                v_exp = format_html_currency(clean_verified, c)
                u_rec = format_html_currency(item.get("unapplied_receipts", 0.0), c)
                v_hold = format_html_currency(item.get("variance_hold_amounts", 0.0), c)
                p_anom = format_html_currency(item.get("potential_anomaly_amounts", 0.0), c)
                unver = format_html_currency(item.get("unverified_amounts", 0.0), c)

                table_html = f"""
                <div class="avoid-break" style="margin-bottom: 20px;">
                    <h3 class="subsection-heading">Schedule: {escape_html(c)} Financial Summary</h3>
                    <table class="dossier-table">
                        <thead>
                            <tr>
                                <th>Category / Metric</th>
                                <th>Amount ({escape_html(c)})</th>
                                <th>Accounting Interpretation & Audit Guidance</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Verified Matching Expenditure</strong></td>
                                <td><code>{v_exp}</code></td>
                                <td>Fully reconciled three-way match (PO &harr; Invoice &harr; Receipt)</td>
                            </tr>
                            <tr>
                                <td><strong>Unapplied Payment Receipts</strong></td>
                                <td><code>{u_rec}</code></td>
                                <td>Disbursement voucher with no matching PO/invoice in scoped directory</td>
                            </tr>
                            <tr>
                                <td><strong>Variance Holds</strong></td>
                                <td><code>{v_hold}</code></td>
                                <td>Billed variance or overpayment held pending contract amendment</td>
                            </tr>
                            <tr>
                                <td><strong>Potential Anomaly Amounts</strong></td>
                                <td><code>{p_anom}</code></td>
                                <td>Partial payments, timing variances, or retention milestone deltas</td>
                            </tr>
                """
                if c in excessive_by_curr and excessive_by_curr[c]["total_excessive"] > Decimal(0):
                    exc_amt = format_html_currency(excessive_by_curr[c]["total_excessive"], c)
                    table_html += f"""
                            <tr>
                                <td style="color: #b45309;"><strong>Amounts Exceeding Currency Precision</strong></td>
                                <td><code>{exc_amt}</code></td>
                                <td>Monetary amounts exceeding ISO 4217 minor-unit precision; held for review</td>
                            </tr>
                    """

                table_html += f"""
                            <tr>
                                <td><strong>Unverified Amounts</strong></td>
                                <td><code>{unver}</code></td>
                                <td>Incomplete extraction or low-resolution scan</td>
                            </tr>
                            <tr>
                                <td><strong>Audited Transaction Items</strong></td>
                                <td><strong>{tx_count} items</strong></td>
                                <td>Total distinct commercial transactions audited in {escape_html(c)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """
                parts.append(table_html)
        else:
            parts.append("<p><em>No standardized currency expenditure schedules recorded.</em></p>")

        # Undocumented / missing currency table
        if undoc:
            rows = []
            for u in undoc:
                amt = format_html_currency(u.get("unverified_amount"))
                reason = escape_html(u.get("reason", "Missing currency code"))
                rows.append(f"""
                <tr>
                    <td><code>UNDOCUMENTED</code></td>
                    <td><code>{amt}</code></td>
                    <td>{reason}</td>
                </tr>
                """)
            parts.append(f"""
            <div class="callout-warning avoid-break">
                <strong>Undocumented / Missing Currency Disclosures</strong>
                <p>The following transactions lacked an ISO currency code and were excluded from verified totals:</p>
                <table class="dossier-table" style="margin-top: 8px;">
                    <thead>
                        <tr>
                            <th>Identifier</th>
                            <th>Amount</th>
                            <th>Withholding Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
            """)

        return "".join(parts)

    @classmethod
    def _build_findings_cards_html(cls, findings: List[Dict[str, Any]], scope_path: str) -> str:
        if not findings:
            return "<p><em>No classified findings recorded for this investigation.</em></p>"

        cards: List[str] = []
        for f in findings:
            f_id = escape_html(f.get("finding_id", "N/A"))
            f_title = escape_html(f.get("title", "Untitled Finding"))
            f_class = escape_html(f.get("classification", "UNVERIFIED"))
            f_subj = escape_html(f.get("subject_reference") or "General Evidence")
            f_exp = escape_html(f.get("expected_value") or "Standard documented compliance")
            f_obs = escape_html(f.get("observed_value") or "Record absence or variance observed")
            f_desc = escape_html(f.get("variance_explanation") or "No explanation recorded.")
            f_rat = escape_html(f.get("classification_rationale") or "Classified based on available documentary evidence.")
            f_act = escape_html(f.get("recommended_action") or "Review original files with finance officer.")
            f_rev = "Yes" if f.get("requires_human_review") else "No"
            f_lim = escape_html(f.get("evidence_limitations") or f"Scoped to directory '{scope_path}'.")
            f_miss = escape_html(f.get("missing_evidence_details") or "None specified.")
            f_paths = f.get("source_paths") or []
            f_doc_ids = f.get("source_document_ids") or []

            card_class = "discrepancy" if f_class == "CONFIRMED_DISCREPANCY" else ("anomaly" if f_class == "POTENTIAL_ANOMALY" else "missing")
            pill_class = "pill-discrepancy" if f_class == "CONFIRMED_DISCREPANCY" else ("pill-anomaly" if f_class == "POTENTIAL_ANOMALY" else "pill-missing")

            paths_html = "".join(f"<li><code>{escape_html(p)}</code></li>" for p in f_paths) if f_paths else "<li><em>No source files attached.</em></li>"
            doc_ids_html = ", ".join(f"#{escape_html(d)}" for d in f_doc_ids) if f_doc_ids else "None"

            card = f"""
            <div class="finding-card {card_class} avoid-break">
                <div class="finding-header">
                    <span class="finding-title">Finding #{f_id}: {f_title}</span>
                    <span class="pill {pill_class}">{f_class}</span>
                </div>
                <div class="finding-grid">
                    <div><strong>Subject Reference:</strong> {f_subj}</div>
                    <div><strong>Human Review Required:</strong> <strong>{f_rev}</strong></div>
                    <div><strong>Expected Compliance Value:</strong> {f_exp}</div>
                    <div><strong>Observed Reality:</strong> {f_obs}</div>
                    <div class="finding-full"><strong>Variance Explanation:</strong> {f_desc}</div>
                    <div class="finding-full"><strong>Classification Rationale:</strong> {f_rat}</div>
                    <div class="finding-full"><strong>Recommended Corrective Action:</strong> {f_act}</div>
                    <div class="finding-full"><strong>Connected Document IDs:</strong> {doc_ids_html}</div>
                    <div class="finding-full">
                        <strong>Source File Paths:</strong>
                        <ul style="margin: 4px 0 0 16px;">
                            {paths_html}
                        </ul>
                    </div>
                    <div class="finding-full"><strong>Scope Limitations:</strong> {f_lim}</div>
                    <div class="finding-full"><strong>Missing Documentation:</strong> {f_miss}</div>
                </div>
            </div>
            """
            cards.append(card)

        return "".join(cards)

    @classmethod
    def _build_evidence_table_html(cls, evidence: List[Dict[str, Any]]) -> str:
        if not evidence:
            return "<p><em>No primary documents registered in evidence snapshot.</em></p>"

        rows: List[str] = []
        for doc in evidence:
            d_id = escape_html(doc.get("document_id", "N/A"))
            d_file = escape_html(doc.get("filename", "unknown"))
            d_role = escape_html(doc.get("evidence_role", "SUPPORTING_EVIDENCE"))
            d_type = escape_html(doc.get("document_type", "OTHER"))
            d_stat = escape_html(doc.get("extraction_status", "EXTRACTED"))
            d_fids = ", ".join(f"#{escape_html(fid)}" for fid in doc.get("linked_finding_ids", [])) or "None"
            d_path = escape_html(doc.get("source_path", "N/A"))

            rows.append(f"""
            <tr>
                <td>#{d_id}</td>
                <td><strong>{d_file}</strong></td>
                <td><span class=\"pill pill-unverified\">{d_role}</span></td>
                <td>{d_type}</td>
                <td><code>{d_stat}</code></td>
                <td>{d_fids}</td>
                <td><code>{d_path}</code></td>
            </tr>
            """)

        return f"""
        <table class="dossier-table">
            <thead>
                <tr>
                    <th>Doc ID</th>
                    <th>Filename</th>
                    <th>Evidence Role</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Linked Findings</th>
                    <th>Scoped Source Path</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """

    @classmethod
    def _build_reconciliation_matrix_html(
        cls,
        ledger: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]]
    ) -> str:
        rows: List[str] = []

        if ledger:
            for row in ledger:
                tx_id = escape_html(row.get("transaction_id", "N/A"))
                desc = escape_html(row.get("item_description", "General Item"))
                curr = row.get("currency")
                po_ref = escape_html(row.get("po_reference") or "No PO")
                po_amt = format_html_currency(row.get("po_amount"), curr)
                inv_num = escape_html(row.get("invoice_number") or "No Invoice")
                inv_amt = format_html_currency(row.get("invoice_amount"), curr)
                rec_proof = escape_html(row.get("receipt_proof") or "No Receipt")
                paid_amt = format_html_currency(row.get("paid_amount"), curr)
                status = escape_html(row.get("reconciliation_status", "UNVERIFIED"))
                conf = escape_html(row.get("match_confidence", "UNMATCHED"))
                rev = "Yes" if row.get("requires_human_review") else "No"

                pill_cls = "pill-reconciled" if status in ("RECONCILED", "RECONCILED_MATCH") else "pill-anomaly"

                rows.append(f"""
                <tr>
                    <td><code>{tx_id}</code><br><span style="font-size:11px;color:#64748b;">{desc}</span></td>
                    <td>{po_ref}<br><code>{po_amt}</code></td>
                    <td>{inv_num}<br><code>{inv_amt}</code></td>
                    <td>{rec_proof}<br><code>{paid_amt}</code></td>
                    <td><span class=\"pill {pill_cls}\">{status}</span></td>
                    <td><code>{conf}</code></td>
                    <td><strong>{rev}</strong></td>
                </tr>
                """)
        else:
            # Fallback legacy matching
            pos = [d for d in evidence if d.get("document_type") == "PURCHASE_ORDER"]
            invs = [d for d in evidence if d.get("document_type") == "INVOICE"]
            recs = [d for d in evidence if d.get("document_type") == "RECEIPT"]

            po_map = {p.get("extracted_data_summary", {}).get("po_reference"): p for p in pos if p.get("extracted_data_summary", {}).get("po_reference")}
            rec_map = {r.get("extracted_data_summary", {}).get("invoice_reference"): r for r in recs if r.get("extracted_data_summary", {}).get("invoice_reference")}

            if invs:
                for inv in invs:
                    i_data = inv.get("extracted_data_summary") or {}
                    i_num = escape_html(i_data.get("invoice_number") or f"INV-UNKNOWN-{inv.get('document_id')}")
                    i_po_ref = i_data.get("po_reference")
                    i_curr = i_data.get("currency")
                    i_amt = format_html_currency(i_data.get("amount"), i_curr)

                    po_doc = po_map.get(i_po_ref) if i_po_ref else None
                    p_amt = format_html_currency(po_doc.get("extracted_data_summary", {}).get("amount"), i_curr) if po_doc else "&mdash;"
                    po_ref_display = escape_html(i_po_ref) if i_po_ref else "No PO"

                    rec_doc = rec_map.get(i_data.get("invoice_number"))
                    r_amt = format_html_currency(rec_doc.get("extracted_data_summary", {}).get("amount"), i_curr) if rec_doc else "&mdash;"
                    r_proof = escape_html(rec_doc.get("extracted_data_summary", {}).get("receipt_id") or "No Receipt") if rec_doc else "No Receipt"

                    status = "RECONCILED" if (po_doc and rec_doc) else "PARTIAL_MATCH"
                    pill_cls = "pill-reconciled" if status == "RECONCILED" else "pill-missing"

                    rows.append(f"""
                    <tr>
                        <td><code>{i_num}</code><br><span style="font-size:11px;color:#64748b;">Invoiced Procurement</span></td>
                        <td>{po_ref_display}<br><code>{p_amt}</code></td>
                        <td>{i_num}<br><code>{i_amt}</code></td>
                        <td>{r_proof}<br><code>{r_amt}</code></td>
                        <td><span class=\"pill {pill_cls}\">{status}</span></td>
                        <td><code>EXACT_MATCH</code></td>
                        <td>{'No' if status == 'RECONCILED' else 'Yes'}</td>
                    </tr>
                    """)
            else:
                rows.append("""
                <tr>
                    <td colspan="7" style="text-align: center; color: #64748b;">No three-way ledger entries available in snapshot.</td>
                </tr>
                """)

        return f"""
        <table class="dossier-table">
            <thead>
                <tr>
                    <th>Tracking ID / Item</th>
                    <th>PO Reference & Authorized</th>
                    <th>Invoice & Billed</th>
                    <th>Receipt Proof & Disbursed</th>
                    <th>Status</th>
                    <th>Confidence</th>
                    <th>Review</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """

    @classmethod
    def _build_missing_checklist_html(cls, findings: List[Dict[str, Any]]) -> str:
        missing = [f for f in findings if f.get("classification") in ("MISSING_EVIDENCE", "UNVERIFIED")]
        if not missing:
            return "<p><em>All required commercial documentation was discovered within the scoped directory. No documentation gaps recorded.</em></p>"

        items: List[str] = []
        for f in missing:
            f_id = escape_html(f.get("finding_id", "N/A"))
            f_title = escape_html(f.get("title", "Documentation Gap"))
            f_act = escape_html(f.get("recommended_action") or f.get("missing_evidence_details") or "Obtain supporting voucher.")
            f_ctx = escape_html(f.get("variance_explanation") or "File absent from searched folder.")

            items.append(f"""
            <li style="margin-bottom: 8px;">
                <input type="checkbox" disabled style="margin-right: 6px;">
                <strong>{f_title}</strong> (Finding #{f_id}): {f_act}
                <div style="font-size: 11px; color: #64748b; margin-left: 22px;">Audit Context: {f_ctx}</div>
            </li>
            """)

        return f"<ul style=\"list-style: none; padding-left: 0;\">{''.join(items)}</ul>"

    @classmethod
    def _build_review_requirements_html(cls, findings: List[Dict[str, Any]], requires_review: bool) -> str:
        flagged = [f for f in findings if f.get("requires_human_review")]
        if not flagged:
            return "<p><em>No items flagged for human supervisory review. All commercial transactions satisfied deterministic verification thresholds.</em></p>"

        items: List[str] = []
        for f in flagged:
            f_id = escape_html(f.get("finding_id", "N/A"))
            f_title = escape_html(f.get("title", "Review Required"))
            f_cls = escape_html(f.get("classification", "REVIEW"))
            f_act = escape_html(f.get("recommended_action", "Inspect physical records."))

            items.append(f"""
            <li style="margin-bottom: 8px;">
                <strong>Finding #{f_id} (<code>{f_cls}</code>):</strong> {f_title}
                <div style="font-size: 11px; color: #475569; margin-left: 8px;">Recommended Action: {f_act}</div>
            </li>
            """)

        return f"<ul>{''.join(items)}</ul>"
