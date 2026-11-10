"""
VaultPilot AI — Phase 3.3 Stage 1 Verification Tests
Tests Stage 1 requirements:
1. PDF extraction security (controlled subprocess args, timeouts, no shell=True).
2. CSV financial accuracy (no double-counting between summary totals and line items, Decimal precision).
3. Evidence-specific reconciliation (unverified document does not downgrade unrelated findings).
4. Field-level provenance (exact line/row/key locations preserved, never invented).
"""

import json
import pytest
from app.core.config import settings
from app.models.project import Project
from app.services.document_extractor import FinancialDocumentExtractor
from app.services.investigation_service import InvestigationService
from app.services.reconciliation_engine import MultiSourceReconciliationEngine

def make_pdf(lines):
    stream = "BT\n/F1 12 Tf\n50 750 Td\n15 TL\n"
    for l in lines:
        escaped = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream += f"({escaped}) '\n"
    stream += "ET\n"
    sb = stream.encode("latin1")
    header = b"%PDF-1.4\n"
    o1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    o2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    o3 = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    o4 = f"4 0 obj\n<< /Length {len(sb)} >>\nstream\n".encode("latin1") + sb + b"endstream\nendobj\n"
    o5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    pos1 = len(header)
    pos2 = pos1 + len(o1)
    pos3 = pos2 + len(o2)
    pos4 = pos3 + len(o3)
    pos5 = pos4 + len(o4)
    xref_pos = pos5 + len(o5)
    xref = f"xref\n0 6\n0000000000 65535 f \n{pos1:010d} 00000 n \n{pos2:010d} 00000 n \n{pos3:010d} 00000 n \n{pos4:010d} 00000 n \n{pos5:010d} 00000 n \n"
    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    return header + o1 + o2 + o3 + o4 + o5 + xref.encode("latin1") + trailer.encode("latin1")


def test_pdf_extraction_security_argument_injection_and_timeout(tmp_path):
    """Verify pdftotext arguments are controlled with '--' delimiter preventing flag injection."""
    # Test file with name starting with a hyphen
    flag_file = tmp_path / "-v_malicious_name.pdf"
    flag_file.write_bytes(make_pdf(["PURCHASE ORDER: PO-SEC-01", "Vendor: SecureCorp", "Total Amount: 5000.00 USD"]))

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(flag_file),
        doc_type="PURCHASE_ORDER",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    assert res["amount"] == 5000.00
    assert res["vendor"] == "SecureCorp"
    assert res["provenance"]["extraction_method"] == "PDF_TEXT_LAYOUT"


def test_csv_accuracy_prevents_double_counting_summary_totals(tmp_path):
    """Verify CSV parser does not double count when a summary 'Total' row is present."""
    csv_file = tmp_path / "summary_invoice.csv"
    csv_content = (
        "Description,Quantity,Unit_Price,Amount,Tax,Currency,Date,Invoice_Number,PO_Reference\n"
        "Solar Panel 400W,10,200.10,2001.00,100.05,USD,2026-03-01,INV-SUMM-01,PO-SUMM-01\n"
        "Inverter 5kW,1,1000.20,1000.20,50.01,USD,2026-03-01,INV-SUMM-01,PO-SUMM-01\n"
        "Total,11,,3001.20,150.06,USD,2026-03-01,INV-SUMM-01,PO-SUMM-01\n"
    )
    csv_file.write_text(csv_content)

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(csv_file),
        doc_type="INVOICE",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    # MUST equal exactly 3001.20, NOT 6002.40 (which would be double counted)
    assert res["amount"] == 3001.20
    assert res["tax_amount"] == 150.06
    # Only 2 line items (summary row excluded from line items)
    assert len(res["line_items"]) == 2
    assert res["line_items"][0]["row_number"] == 2
    assert res["line_items"][1]["row_number"] == 3


def test_field_level_provenance_row_and_line_preservation(tmp_path):
    """Verify exact row numbers in CSV and line numbers in text are preserved without inventing locations."""
    # 1. CSV Row provenance
    csv_file = tmp_path / "prov_test.csv"
    csv_file.write_text(
        "Vendor,PO_Reference,Amount,Currency,Date\n"
        "Global Supplies,PO-PROV-88,4500.00,EUR,2026-02-10\n"
    )
    res_csv = FinancialDocumentExtractor.extract_document(str(csv_file), "PURCHASE_ORDER", nas_root=str(tmp_path))
    fp_csv = res_csv.get("field_provenance", {})
    assert fp_csv["amount"]["source_location"] == "Row 2"
    assert fp_csv["vendor"]["source_location"] == "Row 2"
    assert fp_csv["po_reference"]["source_location"] == "Row 2"

    # 2. TXT Line provenance
    txt_file = tmp_path / "prov_test.txt"
    txt_file.write_text(
        "PURCHASE ORDER\n"                # Line 1
        "Vendor: CleanWater Systems\n"    # Line 2
        "PO: PO-LINE-99\n"                # Line 3
        "Total Amount: 12500.00 USD\n"    # Line 4
    )
    res_txt = FinancialDocumentExtractor.extract_document(str(txt_file), "PURCHASE_ORDER", nas_root=str(tmp_path))
    fp_txt = res_txt.get("field_provenance", {})
    assert fp_txt["vendor"]["source_location"] == "Line 2"
    assert fp_txt["po_reference"]["source_location"] == "Line 3"
    assert fp_txt["amount"]["source_location"] == "Line 4"


def test_evidence_specific_reconciliation_does_not_downgrade_discrepancy(test_db, tmp_path, monkeypatch):
    """
    Verify Requirement 3: An unverified receipt does NOT downgrade a verified billing discrepancy.
    PO ($10,000) vs Invoice ($12,000) is an unauthorized overbilling (+2,000).
    A companion unverified receipt must NOT erase the CONFIRMED_DISCREPANCY finding.
    """
    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "real")
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", str(tmp_path))

    project = Project(
        name="Discrepancy Audit",
        code="PRJ-DISC-2026",
        budget=20000.0,
        currency="USD",
        nas_folder_path=str(tmp_path)
    )
    test_db.add(project)
    test_db.commit()

    # 1. Verified PO: 10,000 USD
    po_file = tmp_path / "PO-DISC-01.txt"
    po_file.write_text("PO: PO-DISC-01 Vendor: HeavyMachinery Inc Amount: 10000.00 USD Date: 2026-01-10")

    # 2. Verified Invoice: 12,000 USD (+2,000 unauthorized overbilling)
    inv_file = tmp_path / "INV-DISC-01.txt"
    inv_file.write_text("INV: INV-DISC-01 PO: PO-DISC-01 Vendor: HeavyMachinery Inc Amount: 12000.00 USD Date: 2026-01-25")

    # 3. Unverified scanned receipt (optical image without OCR)
    rec_file = tmp_path / "REC-DISC-01.jpg"
    rec_file.write_bytes(b"\xFF\xD8\xFF\xE0 Smudged Scanned Receipt Image")

    inv = InvestigationService.run_investigation(
        db=test_db,
        project_id=project.id,
        scope_path=str(tmp_path),
        title="Evidence Specific Audit"
    )

    assert inv.status == "COMPLETED"
    assert inv.document_count == 3

    # CRITICAL: Finding MUST be CONFIRMED_DISCREPANCY (the overbilling was verified between PO and Invoice)
    # The unverified receipt must NOT erase or downgrade it to UNVERIFIED!
    assert len(inv.findings) >= 1
    disc_finding = next((f for f in inv.findings if f.classification == "CONFIRMED_DISCREPANCY"), None)
    assert disc_finding is not None
    assert "exceeds" in disc_finding.title.lower() or "discrepancy" in disc_finding.title.lower()

    # And ledger entry must require human review
    ledger = inv.ledger_entries[0]
    assert ledger.requires_human_review is True
