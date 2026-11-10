"""
VaultPilot AI — Phase 3.2 Genuine Financial Document Extraction Tests
Tests genuine document parsing across PDF, CSV, TXT, JSON, and sidecars.
Verifies provenance, decimal precision, untrusted sidecar boundaries, and reconciliation integration.
"""

import os
import json
import pytest
from app.core.config import settings
from app.models.project import Project
from app.services.ugreen_bridge import FilesystemNASProvider, ugreen_bridge
from app.services.document_extractor import FinancialDocumentExtractor
from app.services.investigation_service import InvestigationService

def make_synthetic_pdf(text_lines):
    """Generates a minimal valid standard PDF 1.4 containing real machine-readable text."""
    stream = "BT\n/F1 12 Tf\n50 750 Td\n15 TL\n"
    for l in text_lines:
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

    xref = (
        f"xref\n0 6\n0000000000 65535 f \n"
        f"{pos1:010d} 00000 n \n{pos2:010d} 00000 n \n{pos3:010d} 00000 n \n"
        f"{pos4:010d} 00000 n \n{pos5:010d} 00000 n \n"
    )
    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"

    return header + o1 + o2 + o3 + o4 + o5 + xref.encode("latin1") + trailer.encode("latin1")


def test_pdf_machine_readable_text_extraction(tmp_path):
    """Verify machine-readable PDF extracts total amount, vendor, tax, and currency accurately."""
    pdf_path = tmp_path / "PO-2026-901.pdf"
    lines = [
        "PURCHASE ORDER: PO-2026-901",
        "Vendor: SolarTech Solutions",
        "Date: 2026-03-01",
        "Total Amount: 14500.50 USD",
        "Tax Amount: 725.00 USD"
    ]
    pdf_path.write_bytes(make_synthetic_pdf(lines))

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(pdf_path),
        doc_type="PURCHASE_ORDER",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    assert res["amount"] == 14500.50
    assert res["tax_amount"] == 725.00
    assert res["currency"] == "USD"
    assert res["vendor"] == "SolarTech Solutions"
    assert res["po_reference"] == "PO-2026-901"
    assert res["requires_human_verification"] is False
    assert res["provenance"]["extraction_method"] == "PDF_TEXT_LAYOUT"


def test_pdf_scanned_image_unverified_fallback(tmp_path):
    """Verify scanned PDF with no text stream gracefully falls back to UNVERIFIED."""
    pdf_path = tmp_path / "SCANNED-RECEIPT.pdf"
    # Write a PDF with an empty text stream
    pdf_path.write_bytes(make_synthetic_pdf([]))

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(pdf_path),
        doc_type="RECEIPT",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "UNVERIFIED"
    assert res["requires_human_verification"] is True
    assert "no machine-readable text" in res["error"].lower()


def test_csv_financial_extraction_and_itemization(tmp_path):
    """Verify CSV extraction itemizes rows and calculates exact totals and taxes."""
    csv_path = tmp_path / "INV-2026-CSV.csv"
    csv_content = (
        "Item,Quantity,Unit_Price,Amount,Tax,Currency,Date,Vendor,Invoice_Number,PO_Reference\n"
        "Water Pump 50HP,2,2500.00,5000.00,250.00,EUR,2026-02-15,AquaPure Industries,INV-2026-CSV,PO-2026-901\n"
        "Piping 100m,5,300.00,1500.00,75.00,EUR,2026-02-15,AquaPure Industries,INV-2026-CSV,PO-2026-901\n"
    )
    csv_path.write_text(csv_content)

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(csv_path),
        doc_type="INVOICE",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    assert res["amount"] == 6500.00
    assert res["tax_amount"] == 325.00
    assert res["currency"] == "EUR"
    assert res["vendor"] == "AquaPure Industries"
    assert res["invoice_number"] == "INV-2026-CSV"
    assert res["po_reference"] == "PO-2026-901"
    assert len(res["line_items"]) == 2
    assert res["requires_human_verification"] is False


def test_csv_missing_fields_remain_missing(tmp_path):
    """Verify missing currency, tax, and vendor are NOT defaulted or hallucinated."""
    csv_path = tmp_path / "MINIMAL-DATA.csv"
    csv_content = (
        "Description,Amount\n"
        "General Labor,850.00\n"
    )
    csv_path.write_text(csv_content)

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(csv_path),
        doc_type="EXPENSE_REPORT",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    assert res["amount"] == 850.00
    assert res["currency"] is None
    assert res["tax_amount"] is None
    assert res["vendor"] is None


def test_json_financial_document_extraction(tmp_path):
    """Verify native JSON financial documents extract all supported fields."""
    json_path = tmp_path / "VOUCH-7001.json"
    json_data = {
        "receipt_id": "VOUCH-7001",
        "invoice_reference": "INV-2026-CSV",
        "vendor": "AquaPure Industries",
        "date": "2026-02-28",
        "amount": 6500.00,
        "tax_amount": 325.00,
        "currency": "EUR",
        "payment_status": "PAID",
        "payment_reference": "WIRE-BNK-9901"
    }
    json_path.write_text(json.dumps(json_data))

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(json_path),
        doc_type="RECEIPT",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    assert res["amount"] == 6500.00
    assert res["currency"] == "EUR"
    assert res["payment_status"] == "PAID"
    assert res["payment_reference"] == "WIRE-BNK-9901"
    assert res["receipt_id"] == "VOUCH-7001"
    assert res["requires_human_verification"] is False


def test_txt_financial_document_extraction(tmp_path):
    """Verify structured text file extraction with key-value headers."""
    txt_path = tmp_path / "PO-TXT-01.txt"
    txt_content = (
        "PURCHASE ORDER\n"
        "PO Number: PO-TXT-01\n"
        "Supplier: MedSupply International\n"
        "Date: 2026-01-15\n"
        "Total Billed: 9800.00 USD\n"
        "Tax: 490.00 USD\n"
    )
    txt_path.write_text(txt_content)

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(txt_path),
        doc_type="PURCHASE_ORDER",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    assert res["amount"] == 9800.00
    assert res["tax_amount"] == 490.00
    assert res["currency"] == "USD"
    assert res["vendor"] == "MedSupply International"
    assert res["po_reference"] == "PO-TXT-01"


def test_invalid_or_corrupted_documents(tmp_path):
    """Verify corrupted JSON and invalid PDFs fail gracefully with error details."""
    corrupted_json = tmp_path / "bad.json"
    corrupted_json.write_text("{ this is malformed json syntax : 123 }")

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(corrupted_json),
        doc_type="INVOICE",
        nas_root=str(tmp_path)
    )
    assert res["status"] == "CORRUPTED"
    assert "Malformed JSON" in res["error"]

    corrupted_pdf = tmp_path / "bad.pdf"
    corrupted_pdf.write_bytes(b"%PDF-1.4 completely invalid garbage binary")
    res_pdf = FinancialDocumentExtractor.extract_document(
        file_path=str(corrupted_pdf),
        doc_type="INVOICE",
        nas_root=str(tmp_path)
    )
    assert res_pdf["status"] in ("UNVERIFIED", "CORRUPTED")


def test_untrusted_sidecar_metadata_marked_for_human_verification(tmp_path):
    """
    CRITICAL RULE TEST: A companion sidecar is untrusted metadata.
    Extraction must be marked UNVERIFIED / requires_human_verification=True.
    """
    img_path = tmp_path / "SCANNED-INVOICE.jpg"
    img_path.write_bytes(b"\xFF\xD8\xFF\xE0 Raw Scanned JPEG Image Bytes")

    sidecar_path = tmp_path / "SCANNED-INVOICE.jpg.json"
    sidecar_path.write_text(json.dumps({
        "invoice_number": "INV-UNTRUSTED-01",
        "po_reference": "PO-TXT-01",
        "amount": 9800.00,
        "currency": "USD",
        "vendor": "MedSupply International"
    }))

    res = FinancialDocumentExtractor.extract_document(
        file_path=str(img_path),
        doc_type="INVOICE",
        nas_root=str(tmp_path)
    )

    assert res["status"] == "EXTRACTED"
    assert res["amount"] == 9800.00
    # Must be marked untrusted and require human verification
    assert res["requires_human_verification"] is True
    assert res["provenance"]["extraction_method"] == "UNTRUSTED_SIDECAR"
    assert res["is_verified_evidence"] is False
    assert "untrusted" in res["error"].lower()


def test_provenance_and_sha256_preservation(tmp_path):
    """Verify SHA-256 evidence hash and file size are accurately preserved in provenance."""
    sample = tmp_path / "DOC-PROV.txt"
    sample.write_text("PO: PO-PROV Amount: 1000.00 USD")

    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    docs = provider.discover_documents(str(tmp_path))

    assert len(docs) == 1
    doc_meta = docs[0]
    assert len(doc_meta["sha256"]) == 64

    extracted = provider.extract_document(str(sample), "PURCHASE_ORDER")
    assert extracted["provenance"]["sha256"] == doc_meta["sha256"]
    assert extracted["provenance"]["file_size_bytes"] == len(sample.read_bytes())


def test_reconciliation_integration_with_genuine_pdf_and_csv(test_db, tmp_path, monkeypatch):
    """End-to-end reconciliation with genuine synthetic PDF (PO) and CSV (Invoice)."""
    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "real")
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", str(tmp_path))

    project = Project(
        name="Genuine Extraction Project",
        code="PRJ-GEN-2026",
        budget=20000.0,
        currency="USD",
        nas_folder_path=str(tmp_path)
    )
    test_db.add(project)
    test_db.commit()

    # 1. Purchase Order as PDF
    po_lines = [
        "PURCHASE ORDER: PO-REAL-001",
        "Vendor: CleanWater Systems",
        "Date: 2026-03-01",
        "Total Amount: 8500.00 USD"
    ]
    po_pdf = tmp_path / "PO-REAL-001.pdf"
    po_pdf.write_bytes(make_synthetic_pdf(po_lines))

    # 2. Invoice as CSV
    inv_csv = tmp_path / "INV-REAL-001.csv"
    inv_csv.write_text(
        "Item,Amount,Currency,Date,Vendor,Invoice_Number,PO_Reference\n"
        "Water Filtration Unit,8500.00,USD,2026-03-15,CleanWater Systems,INV-REAL-001,PO-REAL-001\n"
    )

    # 3. Receipt as JSON
    rec_json = tmp_path / "REC-REAL-001.json"
    rec_json.write_text(json.dumps({
        "receipt_id": "REC-REAL-001",
        "invoice_reference": "INV-REAL-001",
        "payee": "CleanWater Systems",
        "date": "2026-03-20",
        "amount": 8500.00,
        "currency": "USD",
        "payment_status": "PAID"
    }))

    inv = InvestigationService.run_investigation(
        db=test_db,
        project_id=project.id,
        scope_path=str(tmp_path),
        title="Genuine PDF + CSV + JSON 3-Way Audit"
    )

    assert inv.status == "COMPLETED"
    assert inv.document_count == 3
    assert len(inv.ledger_entries) == 1
    ledger = inv.ledger_entries[0]
    assert ledger.reconciliation_status == "RECONCILED_MATCH"
    assert ledger.po_amount == 8500.00
    assert ledger.invoice_amount == 8500.00
    assert ledger.paid_amount == 8500.00
    assert inv.verified_totals["USD"] == 8500.00


def test_reconciliation_with_untrusted_sidecar_requires_human_review(test_db, tmp_path, monkeypatch):
    """End-to-end reconciliation: Untrusted sidecar document is flagged UNVERIFIED for auditor review."""
    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "real")
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", str(tmp_path))

    project = Project(
        name="Untrusted Sidecar Project",
        code="PRJ-UNTRUST-2026",
        budget=10000.0,
        currency="USD",
        nas_folder_path=str(tmp_path)
    )
    test_db.add(project)
    test_db.commit()

    # Scanned image with untrusted companion sidecar
    img_inv = tmp_path / "INV-SCANNED.jpg"
    img_inv.write_bytes(b"\xFF\xD8\xFF\xE0 Raw Image")

    sidecar = tmp_path / "INV-SCANNED.jpg.json"
    sidecar.write_text(json.dumps({
        "invoice_number": "INV-SCANNED",
        "po_reference": "PO-GHOST",
        "amount": 4200.00,
        "currency": "USD"
    }))

    inv = InvestigationService.run_investigation(
        db=test_db,
        project_id=project.id,
        scope_path=str(tmp_path),
        title="Untrusted Metadata Audit"
    )

    assert inv.status == "COMPLETED"
    assert len(inv.findings) >= 1
    finding = inv.findings[0]
    # Critical invariant: must be UNVERIFIED and not counted in verified totals
    assert finding.classification == "UNVERIFIED"
    assert "USD" not in inv.verified_totals or inv.verified_totals["USD"] == 0.0
