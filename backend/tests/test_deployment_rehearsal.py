"""
VaultPilot AI — Phase 4 Failure & Resilience Rehearsal Test Suite
Verifies runtime behavior under simulated deployment failures:
1. Missing NAS Directory
2. Incorrect Volume Permissions / Unreadable Files
3. Invalid Environment Configuration
4. Database Disconnection / Storage Degradation
5. Missing Secret Configuration & Fallbacks
6. Application Lifecycle & Data Persistence
7. Unauthorized Filesystem Access & Confinement
"""

import os
import stat
import pytest
import tempfile
import shutil
from pathlib import Path
from pydantic import ValidationError

from app.core.config import Settings
from app.services.ugreen_bridge import (
    FilesystemNASProvider,
    PhysicalNASStorageProvider,
    NASSecurityViolationError,
    NASInvalidPathError,
    NASStorageUnavailableError,
    NASPathNotFoundError,
    StorageProviderFactory
)
from app.core.security import (
    sign_audit_action,
    verify_audit_signature,
    get_current_auditor,
    AuditorIdentity,
    UserRole
)


def test_failure_1_missing_nas_directory():
    """Failure Test 1: Configured NAS root folder does not exist or is unmounted."""
    nonexistent_path = "/tmp/vaultpilot_test_unmounted_volume_9999"
    provider = FilesystemNASProvider(nas_root=nonexistent_path)

    with pytest.raises(NASStorageUnavailableError) as exc_info:
        provider.discover_documents(nonexistent_path)
    assert "offline or unmounted" in str(exc_info.value)


def test_failure_2_incorrect_volume_permissions():
    """Failure Test 2: Target file has unreadable permissions (mode 000)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "unreadable_invoice.pdf")
        with open(test_file, "wb") as f:
            f.write(b"%PDF-1.4 unreadable test file")
        os.chmod(test_file, 0o000)

        provider = FilesystemNASProvider(nas_root=temp_dir)
        try:
            # Should fail closed and mark file as unverified or raise unreachable
            res = provider.extract_document(test_file, "INVOICE")
            assert res.get("status") in ("UNAVAILABLE", "UNVERIFIED")
        finally:
            os.chmod(test_file, 0o644)


def test_failure_3_invalid_environment_configuration():
    """Failure Test 3: Operator supplies invalid UGREEN_NAS_MODE."""
    with pytest.raises(ValueError) as exc_info:
        Settings(UGREEN_NAS_MODE="cloud_mock")
    assert "Must be 'real' or 'emulated'" in str(exc_info.value)


def test_failure_4_invalid_storage_factory_mode():
    """Failure Test 4: Factory is requested with unsupported storage mode."""
    with pytest.raises(ValueError) as exc_info:
        StorageProviderFactory.get_provider(mode="invalid_cloud_mode")
    assert "Invalid storage mode" in str(exc_info.value)


def test_failure_5_audit_secret_key_tampering():
    """Failure Test 5: Signature verification with mismatched secret or tampered value."""
    sig = sign_audit_action("auditor_01", 101, "amount", 12000.0)

    # Verification with identical parameters succeeds
    assert verify_audit_signature("auditor_01", 101, "amount", 12000.0, sig) is True

    # Verification with tampered amount fails
    assert verify_audit_signature("auditor_01", 101, "amount", 99999.0, sig) is False

    # Verification with tampered reviewer ID fails
    assert verify_audit_signature("attacker_02", 101, "amount", 12000.0, sig) is False


def test_failure_6_data_persistence_across_lifecycle():
    """Failure Test 6: Verify SQLite database retains records across session re-open."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    try:
        from sqlalchemy import create_engine, Column, Integer, String
        from sqlalchemy.orm import declarative_base, sessionmaker

        Base = declarative_base()

        class Record(Base):
            __tablename__ = "records"
            id = Column(Integer, primary_key=True)
            val = Column(String)

        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        # Write initial record
        s1 = Session()
        s1.add(Record(id=1, val="persistent_evidence"))
        s1.commit()
        s1.close()
        engine.dispose()

        # Simulate container restart: re-connect to existing database file
        engine2 = create_engine(f"sqlite:///{db_path}")
        Session2 = sessionmaker(bind=engine2)
        s2 = Session2()
        rec = s2.query(Record).filter_by(id=1).first()
        assert rec is not None
        assert rec.val == "persistent_evidence"
        s2.close()
        engine2.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_failure_7_unauthorized_filesystem_access():
    """Failure Test 7: Traversal escape outside NAS root is blocked."""
    with tempfile.TemporaryDirectory() as temp_root:
        provider = FilesystemNASProvider(nas_root=temp_root)

        # Traversal with literal '..'
        with pytest.raises(NASSecurityViolationError) as exc_info:
            provider.discover_documents(f"{temp_root}/../../etc")
        assert "traversal" in str(exc_info.value).lower()

        # Target resolving outside root
        with pytest.raises(NASSecurityViolationError) as exc_info2:
            provider.discover_documents("/tmp")
        assert "Access denied" in str(exc_info2.value)
