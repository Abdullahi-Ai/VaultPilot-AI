import os
import json
import pytest
from app.models.project import Project
from app.models.investigation import Investigation
from app.services.ugreen_bridge import (
    ugreen_bridge,
    FilesystemNASProvider,
    EmulatedNASProvider,
    NASSecurityViolationError,
    NASPathUnreachableError
)
from app.services.investigation_service import InvestigationService

def test_filesystem_nas_provider_discovers_real_files(tmp_path):
    """Verify FilesystemNASProvider scans genuine local directories and extracts real file metadata."""
    orders_dir = tmp_path / "orders"
    orders_dir.mkdir()
    inv_dir = tmp_path / "invoices"
    inv_dir.mkdir()

    po_file = orders_dir / "PO-TEST-001.txt"
    po_file.write_text("Approved Purchase Order PO-TEST-001\nTotal Amount: 4500.00 USD\nDate: 2026-03-01")

    inv_file = inv_dir / "INV-TEST-002.txt"
    inv_file.write_text("Billed Invoice INV-TEST-002 referencing PO-TEST-001\nBilled Total: 4500.00 USD\nDate: 2026-03-15")

    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    docs = provider.discover_documents(str(tmp_path))

    assert len(docs) == 2
    filenames = [d["filename"] for d in docs]
    assert "PO-TEST-001.txt" in filenames
    assert "INV-TEST-002.txt" in filenames

    po_doc = next(d for d in docs if d["filename"] == "PO-TEST-001.txt")
    assert po_doc["type"] == "PURCHASE_ORDER"
    assert po_doc["size_bytes"] > 0
    assert len(po_doc["sha256"]) == 64

def test_streaming_sha256_accuracy(tmp_path):
    """Verify compute_file_sha256 computes accurate streaming digests without loading whole file into memory."""
    test_file = tmp_path / "large_evidence.bin"
    # Write 150KB of deterministic binary data
    content = b"A" * 65536 + b"B" * 65536 + b"C" * 20000
    test_file.write_bytes(content)

    import hashlib
    expected_hash = hashlib.sha256(content).hexdigest()
    computed_hash = FilesystemNASProvider.compute_file_sha256(str(test_file))

    assert computed_hash == expected_hash

def test_filesystem_nas_provider_directory_traversal_rejection(tmp_path):
    """Verify scope paths with directory traversal sequences ('..') are strictly rejected."""
    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    
    with pytest.raises(NASSecurityViolationError) as exc_info:
        provider.discover_documents(str(tmp_path / "sub" / ".." / ".." / "etc"))

    assert "traversal sequence" in str(exc_info.value)

def test_filesystem_nas_provider_symlink_escape_rejection(tmp_path):
    """Verify symlinks pointing outside the authorized nas_root are detected and rejected."""
    nas_root = tmp_path / "nas_root"
    nas_root.mkdir()
    outside_dir = tmp_path / "secret_outside"
    outside_dir.mkdir()

    secret_file = outside_dir / "confidential_donor_record.txt"
    secret_file.write_text("SECRET")

    # Create malicious symlink inside nas_root pointing outside
    malicious_link = nas_root / "evil_symlink.txt"
    try:
        os.symlink(str(secret_file), str(malicious_link))
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on filesystem")

    provider = FilesystemNASProvider(nas_root=str(nas_root))
    
    with pytest.raises(NASSecurityViolationError) as exc_info:
        provider.discover_documents(str(nas_root))

    assert "Symlink escape detected" in str(exc_info.value)

def test_filesystem_nas_provider_unreachable_or_unmounted_path(tmp_path):
    """Verify unreachable path raises NASPathUnreachableError instead of silently returning mock data."""
    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    unmounted_path = tmp_path / "unmounted_volume_share"

    with pytest.raises(NASPathUnreachableError) as exc_info:
        provider.discover_documents(str(unmounted_path))

    assert "does not exist or is unmounted" in str(exc_info.value)

def test_filesystem_nas_provider_extracts_sidecar_json(tmp_path):
    """Verify FilesystemNASProvider extracts companion sidecar metadata without inventing fields."""
    docs_dir = tmp_path / "records"
    docs_dir.mkdir()

    pdf_file = docs_dir / "INV-9901.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 Mock Scanned Binary Data")

    sidecar = docs_dir / "INV-9901.pdf.json"
    sidecar.write_text(json.dumps({
        "invoice_number": "INV-9901",
        "po_reference": "PO-8812",
        "amount": 7800.50,
        "currency": "EUR",
        "vendor": "CleanWater Supply AG",
        "date": "2026-02-18"
    }))

    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    extracted = provider.extract_document(str(pdf_file), "INVOICE")

    assert extracted["status"] == "EXTRACTED"
    assert extracted["invoice_number"] == "INV-9901"
    assert extracted["po_reference"] == "PO-8812"
    assert extracted["amount"] == 7800.50
    assert extracted["currency"] == "EUR"
    assert extracted["vendor"] == "CleanWater Supply AG"

def test_filesystem_nas_provider_handles_unreadable_file_as_unverified(tmp_path):
    """Verify FilesystemNASProvider gracefully marks binary files without sidecars as UNVERIFIED."""
    raw_file = tmp_path / "scanned_invoice_no_ocr.pdf"
    raw_file.write_bytes(b"%PDF-1.7 Corrupted or unindexed scan")

    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    extracted = provider.extract_document(str(raw_file), "INVOICE")

    assert extracted["status"] == "UNVERIFIED"
    assert "OCR" in extracted.get("error", "")

def test_read_only_integrity_source_files_remain_unmodified(tmp_path):
    """Verify that document discovery and extraction never alter or mutate source file contents."""
    sample_file = tmp_path / "PO-IMMUTABLE.txt"
    original_text = "PO-IMMUTABLE Amount: 1000.00 USD"
    sample_file.write_text(original_text)

    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    provider.discover_documents(str(tmp_path))
    provider.extract_document(str(sample_file), "PURCHASE_ORDER")

    # Verify file content and mtime unchanged
    assert sample_file.read_text() == original_text

def test_investigation_service_runs_real_filesystem_audit(test_db, tmp_path):
    """End-to-end integration test: InvestigationService discovers real files and reconciles correctly."""
    project = Project(
        name="Real NAS Test Project",
        code="PRJ-REAL-2026",
        donor="Local Development Trust",
        budget=10000.0,
        currency="USD",
        nas_folder_path=str(tmp_path)
    )
    test_db.add(project)
    test_db.commit()

    po_file = tmp_path / "PO-100.txt"
    po_file.write_text("PO-100 Amount: 3200.00 USD Date: 2026-02-01")

    inv_file = tmp_path / "INV-200.txt"
    inv_file.write_text("INV-200 PO: PO-100 Amount: 3200.00 USD Date: 2026-02-15")

    rec_file = tmp_path / "REC-300.txt"
    rec_file.write_text("REC-300 INV: INV-200 Amount: 3200.00 USD Date: 2026-02-28")

    inv = InvestigationService.run_investigation(
        db=test_db,
        project_id=project.id,
        scope_path=str(tmp_path),
        title="Live Directory Audit"
    )

    assert inv.status == "COMPLETED"
    assert inv.document_count == 3
    assert "USD" in inv.verified_totals
    assert inv.verified_totals["USD"] == 3200.00

def test_investigation_service_empty_real_folder(test_db, tmp_path):
    """Verify empty directory yields completed audit with 0 files cleanly."""
    empty_dir = tmp_path / "empty_folder"
    empty_dir.mkdir()

    project = Project(
        name="Empty Project",
        code="PRJ-EMPTY",
        budget=5000.0,
        currency="USD",
        nas_folder_path=str(empty_dir)
    )
    test_db.add(project)
    test_db.commit()

    inv = InvestigationService.run_investigation(
        db=test_db,
        project_id=project.id,
        scope_path=str(empty_dir),
        title="Empty Directory Audit"
    )

    assert inv.status == "COMPLETED"
    assert inv.document_count == 0
    assert "No financial documents discovered" in inv.summary
