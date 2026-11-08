import pytest
import re
from app.models.project import Project
from app.models.investigation import Investigation
from app.models.document import Document
from app.models.finding import Finding
from app.models.ledger import EvidenceLedgerEntry
from app.models.report import InvestigationReport
from app.services.report_service import ReportService
from app.services.csv_exporter import ReportIntegrityError
from app.services.html_renderer import HTMLDossierRenderer

@pytest.fixture
def rich_investigation_setup(test_db):
    """Creates a complete populated investigation environment with multiple currencies and findings."""
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
        summary="Audit of medical supplies procurement.",
        document_count=3
    )
    test_db.add(inv)
    test_db.flush()

    doc_po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-9001.pdf",
        file_path="/volume1/finance/EMSP-2026/orders/PO-9001.pdf",
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-9001", "amount": 12500.0, "currency": "USD", "vendor": "MedEquip Ltd"}
    )
    doc_inv = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-ME-4001.pdf",
        file_path="/volume1/finance/EMSP-2026/invoices/INV-ME-4001.pdf",
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_number": "INV-ME-4001", "po_reference": "PO-9001", "amount": 12500.0, "currency": "USD", "vendor": "MedEquip Ltd"}
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
    test_db.add_all([doc_po, doc_inv, doc_rec])
    test_db.flush()

    f1 = Finding(
        investigation_id=inv.id,
        title="Overbilled Logistics Surcharge",
        classification="CONFIRMED_DISCREPANCY",
        subject_reference="PO-9001 vs INV-ME-4001",
        source_paths=[doc_po.file_path, doc_inv.file_path],
        expected_value="Authorized budget limit",
        observed_value="Billed surcharge in excess of contract",
        variance_explanation="Billed variance of 450.00 USD without change order approval.",
        recommended_action="Recover 450.00 USD excess billing from next disbursement.",
        source_document_ids=[doc_po.id, doc_inv.id],
        missing_evidence_details="Signed variation authorization missing.",
        evidence_limitations="Scope limited to EMSP-2026.",
        classification_rationale="Classified as CONFIRMED_DISCREPANCY because contract limits were breached."
    )
    test_db.add(f1)

    entry1 = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-USD-001",
        item_description="Surgical Diagnostics & Patient Monitors",
        supplier_name="MedEquip Ltd",
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
        variance_amount=0.0,
        source_file_paths=[doc_po.file_path, doc_inv.file_path, doc_rec.file_path],
        source_document_ids=[doc_po.id, doc_inv.id, doc_rec.id]
    )

    entry2 = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-USD-002",
        item_description="Vendor Volume Rebate Discount",
        supplier_name="MedEquip Ltd",
        invoice_number="CR-ME-002",
        invoice_amount=-1500.0,
        paid_amount=-1500.0,
        currency="USD",
        variance_amount=-25.50,
        variance_reason="Rebate credit note adjustment",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH"
    )

    entry_eur = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-EUR-001",
        item_description="Cold-Chain Vaccine Chillers",
        supplier_name="BioKlima AG",
        po_reference="PO-EUR-77",
        po_amount=8400.0,
        invoice_number="INV-BK-202",
        invoice_amount=8400.0,
        receipt_proof="REC-EUR-33",
        paid_amount=8400.0,
        currency="EUR",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH"
    )

    entry_undoc = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-UNDOC-99",
        item_description="Field Clinic Waste Management",
        invoice_number="INV-UNK-99",
        invoice_amount=350.0,
        paid_amount=350.0,
        currency=None,
        reconciliation_status="UNVERIFIED",
        match_confidence="UNMATCHED",
        requires_human_review=True,
        human_review_reason="Missing currency code on invoice."
    )

    test_db.add_all([entry1, entry2, entry_eur, entry_undoc])
    test_db.commit()

    return {
        "project": project,
        "investigation": inv,
        "docs": [doc_po, doc_inv, doc_rec],
        "findings": [f1],
        "entries": [entry1, entry2, entry_eur, entry_undoc]
    }


def test_html_renderer_generates_all_13_sections(test_db, rich_investigation_setup):
    """Verify HTML renderer generates a complete HTML5 document containing all 13 required sections."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    html_text = HTMLDossierRenderer.render(report)

    # 1. HTML5 Doctype & Core Tags
    assert "<!DOCTYPE html>" in html_text
    assert "<html lang=\"en\">" in html_text
    assert "</html>" in html_text

    # 2. Section 1: Header & Metadata
    assert "VaultPilot AI" in html_text
    assert f"IR-{report.id}-V1" in html_text
    assert "SNAPSHOT INTEGRITY: VERIFIED" in html_text
    assert report.snapshot_integrity_hash in html_text

    # 3. Section 2: Executive Summary
    assert "1. Executive Summary" in html_text

    # 4. Section 3: Investigation Scope & Documentary Universe
    assert "2. Investigation Scope &amp; Documentary Universe" in html_text
    assert "EMSP-2026" in html_text

    # 5. Section 4: Methodology
    assert "3. Investigation Methodology" in html_text
    assert "VaultPilot-Audit-Methodology-2.0" in html_text

    # 6. Section 5: Financial Summary
    assert "4. Financial Reconciliation Summary" in html_text

    # 7. Section 6: Currency Expenditure Schedules
    assert "5. Currency-Separated Expenditure Schedules" in html_text
    assert "Schedule: USD Financial Summary" in html_text
    assert "Schedule: EUR Financial Summary" in html_text

    # 8. Section 7: Classified Findings Register
    assert "6. Classified Findings Register" in html_text
    assert "Finding #1: Overbilled Logistics Surcharge" in html_text
    assert "CONFIRMED_DISCREPANCY" in html_text

    # 9. Section 8: Primary Evidence Register
    assert "7. Primary Evidence Register" in html_text
    assert "PO-9001.pdf" in html_text

    # 10. Section 9: Three-Way Reconciliation Matrix
    assert "8. Three-Way Documentary Reconciliation Matrix" in html_text
    assert "TXN-USD-001" in html_text

    # 11. Section 10: Missing Evidence Checklist
    assert "9. Missing and Incomplete Evidence Checklist" in html_text

    # 12. Section 11: Human Supervisory Review Requirements
    assert "10. Human Supervisory Review Requirements" in html_text

    # 13. Section 12: Scope Limitations & Legal Disclaimers
    assert "11. Investigation Limitations &amp; Legal Disclaimers" in html_text
    assert "Negative Proof Clarification" in html_text

    # 14. Section 13: Attestation & Signature Blocks
    assert "12. Cryptographic Integrity &amp; Attestation Sign-Off" in html_text
    assert "Lead Financial Investigator" in html_text
    assert "NGO Finance Director / Compliance Officer" in html_text


def test_html_zero_external_scripts_or_images(test_db, rich_investigation_setup):
    """Verify that generated HTML contains zero external scripts, stylesheets, or remote images."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    html_text = HTMLDossierRenderer.render(report)

    # Disallow remote asset requests
    assert "http://" not in html_text
    assert "https://" not in html_text
    assert "<script src=" not in html_text
    assert "<link rel=\"stylesheet\"" not in html_text


def test_html_csp_header_present(test_db, rich_investigation_setup):
    """Verify Content Security Policy meta tag is strictly enforced."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    html_text = HTMLDossierRenderer.render(report)
    assert "<meta http-equiv=\"Content-Security-Policy\"" in html_text
    assert "default-src 'none'" in html_text
    assert "style-src 'unsafe-inline'" in html_text


def test_html_escaping_xss_protection(test_db, rich_investigation_setup):
    """Verify malicious Stored XSS vectors are neutralized via HTML entity escaping."""
    inv = rich_investigation_setup["investigation"]

    # Inject finding with XSS payloads
    xss_finding = Finding(
        investigation_id=inv.id,
        title="<script>alert('XSS')</script>",
        classification="CONFIRMED_DISCREPANCY",
        subject_reference="<img src=x onerror=alert(1)>",
        expected_value="\" onfocus=\"alert('XSS')\"",
        observed_value="'; DROP TABLE findings; --",
        variance_explanation="<b>Bold Attack</b>",
        classification_rationale="<iframe src=\"javascript:alert(1)\"></iframe>",
        recommended_action="<a href=\"javascript:void(0)\">Click Me</a>"
    )
    test_db.add(xss_finding)
    test_db.commit()

    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)
    html_text = HTMLDossierRenderer.render(report)

    # Ensure dangerous tags are not rendered as raw HTML
    assert "<script>" not in html_text
    assert "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;" in html_text
    assert "<img src=x onerror=alert(1)>" not in html_text
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_text
    assert "<iframe" not in html_text
    assert "&lt;iframe src=&quot;javascript:alert(1)&quot;&gt;&lt;/iframe&gt;" in html_text
    assert "<a href=\"javascript:" not in html_text


def test_html_integrity_gating_fail_closed(test_db, rich_investigation_setup):
    """Verify tampered snapshot fails closed and raises ReportIntegrityError."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    # Mutate snapshot payload directly (simulating unauthorized DB tampering)
    tampered_payload = dict(report.snapshot_payload)
    tampered_payload["unauthorized_edit"] = "tampered_value"
    report.snapshot_payload = tampered_payload

    with pytest.raises(ReportIntegrityError) as exc_info:
        HTMLDossierRenderer.render(report)

    assert "REPORT_INTEGRITY_VERIFICATION_FAILED" in str(exc_info.value)
    assert "HTML dossier generation refused" in str(exc_info.value)


def test_html_missing_hash_or_payload_refuses_render():
    """Verify missing hash, missing payload, or None report raises ReportIntegrityError."""
    with pytest.raises(ReportIntegrityError):
        HTMLDossierRenderer.render(None)

    empty_rep = InvestigationReport(id=1, snapshot_payload=None, snapshot_integrity_hash="abc")
    with pytest.raises(ReportIntegrityError):
        HTMLDossierRenderer.render(empty_rep)

    no_hash_rep = InvestigationReport(id=2, snapshot_payload={"k": "v"}, snapshot_integrity_hash=None)
    with pytest.raises(ReportIntegrityError):
        HTMLDossierRenderer.render(no_hash_rep)


def test_html_print_css_presence(test_db, rich_investigation_setup):
    """Verify presence of print-optimized CSS rules for browser printing to PDF."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    html_text = HTMLDossierRenderer.render(report)

    assert "@media print" in html_text
    assert "@page" in html_text
    assert "display: table-header-group" in html_text
    assert "page-break-inside: avoid" in html_text
    assert "page-break-after: avoid" in html_text


def test_html_currency_segregation_and_undocumented_disclosure(test_db, rich_investigation_setup):
    """Verify currency schedules maintain segregation and isolate undocumented currency."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    html_text = HTMLDossierRenderer.render(report)

    # Both USD and EUR schedules present
    assert "Schedule: USD Financial Summary" in html_text
    assert "Schedule: EUR Financial Summary" in html_text

    # Undocumented currency isolated
    assert "Undocumented / Missing Currency Disclosures" in html_text
    assert "currency code" in html_text


def test_html_render_bytes_helper(test_db, rich_investigation_setup):
    """Verify render_bytes returns valid UTF-8 encoded bytes."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    html_bytes = HTMLDossierRenderer.render_bytes(report)
    assert isinstance(html_bytes, bytes)
    assert b"<!DOCTYPE html>" in html_bytes
    assert b"VaultPilot AI" in html_bytes


def test_report_service_get_report_html(test_db, rich_investigation_setup):
    """Verify ReportService.get_report_html retrieves snapshot and renders HTML."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    rendered_html = ReportService.get_report_html(db=test_db, report_id=report.id)
    assert "<!DOCTYPE html>" in rendered_html
    assert f"IR-{report.id}-V1" in rendered_html
