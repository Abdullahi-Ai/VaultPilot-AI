import pytest
from fastapi import HTTPException
from app.core.security import (
    sign_audit_action,
    verify_audit_signature,
    get_current_auditor,
    require_auditor_role,
    UserRole,
    AuditorIdentity
)
from app.core.config import settings

def test_sign_and_verify_audit_action():
    """Verify cryptographic HMAC-SHA256 signature validates genuine reviewer intervention."""
    reviewer_id = "auditor_smith"
    doc_id = 109
    field = "amount"
    val = "12000.00"

    sig_block = sign_audit_action(reviewer_id, doc_id, field, val)
    assert "|" in sig_block
    assert len(sig_block.split("|")[1]) == 64  # SHA-256 hex digest

    valid = verify_audit_signature(reviewer_id, doc_id, field, val, sig_block)
    assert valid is True

def test_tampered_signature_rejected():
    """Verify tampered field value fails signature verification."""
    reviewer_id = "auditor_smith"
    doc_id = 109
    field = "amount"
    val = "12000.00"
    tampered_val = "15000.00"

    sig_block = sign_audit_action(reviewer_id, doc_id, field, val)
    valid = verify_audit_signature(reviewer_id, doc_id, field, tampered_val, sig_block)
    assert valid is False

def test_auditor_token_authentication():
    """Verify X-Auditor-Key header grants AUDITOR role identity."""
    identity = get_current_auditor(x_auditor_key="auditor-lead-token")
    assert identity.role == UserRole.AUDITOR
    assert identity.username == "Senior Lead Auditor"

    checked = require_auditor_role(identity)
    assert checked.role == UserRole.AUDITOR

def test_viewer_token_read_only_restriction():
    """Verify VIEWER role is blocked from executing auditor mutations."""
    identity = get_current_auditor(x_auditor_key="viewer-readonly-token")
    assert identity.role == UserRole.VIEWER

    with pytest.raises(HTTPException) as exc_info:
        require_auditor_role(identity)
    assert exc_info.value.status_code == 403
    assert "requires AUDITOR role" in exc_info.value.detail

def test_demo_mode_transparent_auditor_fallback(monkeypatch):
    """Verify demo mode transparently provides default auditor without requiring manual headers."""
    monkeypatch.setattr(settings, "STORAGE_MODE", "emulated_nas")
    monkeypatch.setattr(settings, "UGREEN_NAS_MODE", "emulated")

    identity = get_current_auditor(x_auditor_key=None, authorization=None)
    assert identity.role == UserRole.AUDITOR
    assert "Elena Vance" in identity.username
