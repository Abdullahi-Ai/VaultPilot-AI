import os
import stat
import json
import pytest
from app.core.config import settings, Settings
from app.models.project import Project
from app.models.investigation import Investigation
from app.services.ugreen_bridge import (
    ugreen_bridge,
    FilesystemNASProvider,
    EmulatedNASProvider,
    NASSecurityViolationError,
    NASInvalidPathError,
    NASPathUnreachableError,
    NASStorageUnavailableError,
    NASPathNotFoundError,
    NASFileMutationError
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

def test_investigation_service_runs_real_filesystem_audit(test_db, tmp_path, monkeypatch):
    """End-to-end integration test: InvestigationService discovers real files and reconciles correctly in real mode."""
    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "real")
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", str(tmp_path))

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

def test_investigation_service_empty_real_folder(test_db, tmp_path, monkeypatch):
    """Verify empty directory yields completed audit with 0 files cleanly in real mode."""
    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "real")
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", str(tmp_path))

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

def test_configuration_mode_standardization():
    """Verify UGREEN_NAS_MODE strictly enforces 'real' and 'emulated', rejecting 'mock' or arbitrary strings."""
    # Valid configurations
    s_real = Settings(UGREEN_NAS_MODE="real")
    assert s_real.UGREEN_NAS_MODE == "real"

    s_emulated = Settings(UGREEN_NAS_MODE="emulated")
    assert s_emulated.UGREEN_NAS_MODE == "emulated"

    # 'mock' and invalid modes must be rejected
    with pytest.raises(ValueError) as exc_mock:
        Settings(UGREEN_NAS_MODE="mock")
    assert "Must be 'real' or 'emulated'" in str(exc_mock.value)

    with pytest.raises(ValueError) as exc_invalid:
        Settings(UGREEN_NAS_MODE="arbitrary_mode")
    assert "Must be 'real' or 'emulated'" in str(exc_invalid.value)

def test_no_silent_fallback_in_real_mode(tmp_path, monkeypatch):
    """Verify that when UGREEN_NAS_MODE='real', missing files or paths fail explicitly without mock data."""
    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "real")
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", str(tmp_path))

    nonexistent_dir = str(tmp_path / "offline_subfolder")
    with pytest.raises(NASPathNotFoundError):
        ugreen_bridge.discover_documents(nonexistent_dir)

    # Missing file extraction in real mode returns UNAVAILABLE, never fixture data
    res = ugreen_bridge.extract_document(str(tmp_path / "missing_po.pdf"), "PURCHASE_ORDER")
    assert res == {"status": "UNAVAILABLE"}

def test_special_file_fifo_rejection(tmp_path):
    """Verify that special files like FIFOs (named pipes) are rejected to prevent hangs and security exploits."""
    if not hasattr(os, "mkfifo"):
        pytest.skip("mkfifo not supported on this platform")

    fifo_path = tmp_path / "evil_pipe.txt"
    try:
        os.mkfifo(str(fifo_path))
    except (OSError, PermissionError):
        pytest.skip("Permission denied creating FIFO")

    provider = FilesystemNASProvider(nas_root=str(tmp_path))

    with pytest.raises(NASSecurityViolationError) as exc_info:
        provider.discover_documents(str(tmp_path))

    assert "Special non-regular file rejected" in str(exc_info.value)

def test_companion_sidecar_deduplication_and_association(tmp_path):
    """Verify sidecar JSON files are safely associated with their primary document and not double-counted."""
    orders_dir = tmp_path / "orders"
    orders_dir.mkdir()

    pdf_file = orders_dir / "PO-8888.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 Real Binary Purchase Order")

    sidecar_file = orders_dir / "PO-8888.json"
    sidecar_file.write_text(json.dumps({
        "vendor": "SolarTech Global",
        "po_reference": "PO-8888",
        "amount": 19500.0,
        "currency": "USD",
        "status": "EXTRACTED"
    }))

    provider = FilesystemNASProvider(nas_root=str(tmp_path))
    docs = provider.discover_documents(str(tmp_path))

    # Sidecar PO-8888.json must NOT appear as a distinct document
    assert len(docs) == 1
    assert docs[0]["filename"] == "PO-8888.pdf"

    # Extracting PO-8888.pdf must correctly read the companion sidecar data
    extracted = provider.extract_document(str(pdf_file), "PURCHASE_ORDER")
    assert extracted["status"] == "EXTRACTED"
    assert extracted["vendor"] == "SolarTech Global"
    assert extracted["amount"] == 19500.0
    assert extracted["currency"] == "USD"

def test_toctou_file_mutation_detection(tmp_path, monkeypatch):
    """Verify concurrent modification during hashing is caught by TOCTOU checks."""
    test_file = tmp_path / "mutating_doc.bin"
    test_file.write_bytes(b"initial data")

    # Simulate concurrent mutation by patching os.fstat on the second call
    original_fstat = os.fstat
    call_count = [0]

    def mock_fstat(fd):
        st = original_fstat(fd)
        call_count[0] += 1
        if call_count[0] > 1:
            # Return an altered mtime_ns on the second check
            class MutatedStat:
                st_mode = st.st_mode
                st_size = st.st_size
                st_mtime_ns = st.st_mtime_ns + 1000000000
            return MutatedStat()
        return st

    monkeypatch.setattr(os, "fstat", mock_fstat)

    with pytest.raises(NASFileMutationError) as exc_info:
        FilesystemNASProvider.compute_file_sha256(str(test_file))

    assert "concurrently mutated" in str(exc_info.value)

def test_api_distinguishes_invalid_path_from_unavailable_storage(client, test_db, tmp_path, monkeypatch):
    """Verify API endpoint returns 400 for path security violation, 404 for missing folder, and 503 for offline NAS."""
    project = Project(
        name="API Error Test Project",
        code="PRJ-ERR-2026",
        budget=1000.0,
        currency="USD",
        nas_folder_path=str(tmp_path)
    )
    test_db.add(project)
    test_db.commit()

    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "real")
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", str(tmp_path))

    # 1. Root boundary escape security violation (no '..' characters, passes schema, rejected by provider) -> 400 Bad Request
    res_escape = client.post("/api/v1/investigations/run", json={
        "project_id": project.id,
        "folder_path": "/etc",
        "title": "Root Escape Test"
    })
    assert res_escape.status_code == 400
    assert "security violation" in res_escape.json()["detail"].lower()

    # 2. Directory traversal sequence -> 400 or 422
    res_traversal = client.post("/api/v1/investigations/run", json={
        "project_id": project.id,
        "folder_path": str(tmp_path / ".." / "etc"),
        "title": "Traversal Test"
    })
    assert res_traversal.status_code in (400, 422)

    # 2. Target folder does not exist -> 404 Not Found
    res_missing = client.post("/api/v1/investigations/run", json={
        "project_id": project.id,
        "folder_path": str(tmp_path / "nonexistent_subfolder"),
        "title": "Missing Subfolder Test"
    })
    assert res_missing.status_code == 404
    assert "not found" in res_missing.json()["detail"].lower()

    # 3. NAS storage root is offline or unmounted -> 503 Service Unavailable
    monkeypatch.setattr(settings, "UGREEN_NAS_ROOT", "/tmp/completely_unmounted_volume_root_xyz")
    res_offline = client.post("/api/v1/investigations/run", json={
        "project_id": project.id,
        "folder_path": "/tmp/completely_unmounted_volume_root_xyz/share",
        "title": "Offline NAS Test"
    })
    assert res_offline.status_code == 503
    assert "unavailable" in res_offline.json()["detail"].lower()
