import pytest
from app.services.uliya_agent_bridge import (
    UliyaAgentBridge,
    UliyaResponseEnvelope,
    DelegationStatus,
    UliyaBridgeError
)

def test_parse_valid_json_envelope():
    """Verify valid JSON string parses into canonical UliyaResponseEnvelope."""
    raw = '{"ok": true, "status": "completed", "data": {"scope_path": "/volume1/NGO", "files": []}}'
    env = UliyaAgentBridge.parse_and_validate_envelope(raw)
    assert env.ok is True
    assert env.status == DelegationStatus.COMPLETED
    assert env.data["scope_path"] == "/volume1/NGO"

def test_parse_malformed_json_raises_bridge_error():
    """Verify malformed JSON raises UliyaBridgeError with FAILED status."""
    raw = '{"ok": true, "status": "completed", broken json...'
    with pytest.raises(UliyaBridgeError) as exc_info:
        UliyaAgentBridge.parse_and_validate_envelope(raw)
    assert "Malformed JSON" in str(exc_info.value)
    assert exc_info.value.status == DelegationStatus.FAILED

def test_parse_invalid_envelope_schema_raises_error():
    """Verify envelope missing 'ok' boolean field fails validation."""
    raw = '{"status": "completed", "data": {}}'
    with pytest.raises(UliyaBridgeError) as exc_info:
        UliyaAgentBridge.parse_and_validate_envelope(raw)
    assert "failed envelope schema validation" in str(exc_info.value)

def test_validate_find_results_success():
    """Verify ug-filesystem.find payload validation extracts clean file list."""
    envelope = UliyaResponseEnvelope(
        ok=True,
        status=DelegationStatus.COMPLETED,
        data={
            "scope_path": "/volume1/NGO_Projects/WASH",
            "total_found": 2,
            "files": [
                {
                    "file_path": "/volume1/NGO_Projects/WASH/PO-01.pdf",
                    "filename": "PO-01.pdf",
                    "type": "PURCHASE_ORDER",
                    "size_bytes": 1024,
                    "sha256": "abcdef1234567890" * 4
                },
                {
                    "file_path": "/volume1/NGO_Projects/WASH/INV-01.pdf",
                    "filename": "INV-01.pdf",
                    "type": "INVOICE",
                    "size_bytes": 2048,
                    "sha256": "123456abcdef7890" * 4
                }
            ]
        }
    )
    files = UliyaAgentBridge.validate_find_results(envelope)
    assert len(files) == 2
    assert files[0]["filename"] == "PO-01.pdf"
    assert files[0]["type"] == "PURCHASE_ORDER"
    assert files[1]["filename"] == "INV-01.pdf"

def test_validate_find_results_waiting_approval_pauses():
    """Verify status='waiting_approval' safely halts without raising an unhandled exception."""
    envelope = UliyaResponseEnvelope(
        ok=False,
        status=DelegationStatus.WAITING_APPROVAL,
        error={"code": "APPROVAL_REQUIRED", "message": "Admin authorization needed for /volume1/Secret"}
    )
    files = UliyaAgentBridge.validate_find_results(envelope)
    assert files == []

def test_validate_find_results_cancelled_stops():
    """Verify status='cancelled' cleanly returns empty list without failure."""
    envelope = UliyaResponseEnvelope(
        ok=False,
        status=DelegationStatus.CANCELLED
    )
    files = UliyaAgentBridge.validate_find_results(envelope)
    assert files == []

def test_validate_extract_results_valid_invoice():
    """Verify ug-document.extract parses clean financial metadata payload."""
    envelope = UliyaResponseEnvelope(
        ok=True,
        status=DelegationStatus.COMPLETED,
        data={
            "schema": "invoice",
            "vendor": "CleanWater Global Ltd",
            "invoice_number": "INV-9901",
            "po_reference": "PO-4410",
            "date": "2026-03-15",
            "amount": 12500.00,
            "currency": "USD",
            "status": "EXTRACTED"
        }
    )
    extracted = UliyaAgentBridge.validate_extract_results(envelope)
    assert extracted["status"] == "EXTRACTED"
    assert extracted["vendor"] == "CleanWater Global Ltd"
    assert extracted["amount"] == 12500.00
    assert extracted["currency"] == "USD"
    assert extracted["invoice_number"] == "INV-9901"

def test_validate_extract_results_failed_envelope():
    """Verify failed envelope returns UNAVAILABLE status gracefully."""
    envelope = UliyaResponseEnvelope(
        ok=False,
        status=DelegationStatus.FAILED,
        error={"code": "FILE_CORRUPTED", "message": "Corrupted PDF header"}
    )
    extracted = UliyaAgentBridge.validate_extract_results(envelope)
    assert extracted["status"] == "UNAVAILABLE"
    assert "Corrupted PDF header" in extracted["error"]

def test_validate_reconcile_results_success():
    """Verify ug-document.reconcile envelope parses match and discrepancy lists."""
    envelope = UliyaResponseEnvelope(
        ok=True,
        status=DelegationStatus.COMPLETED,
        data={
            "reconciliation_status": "VARIANCE_HOLD",
            "coverage_score": 0.85,
            "confirmed_discrepancies": [
                {"type": "PRICE_VARIANCE", "variance_amount": 2500.00, "currency": "USD"}
            ],
            "potential_anomalies": [],
            "missing_evidence": []
        }
    )
    rec = UliyaAgentBridge.validate_reconcile_results(envelope)
    assert rec["reconciliation_status"] == "VARIANCE_HOLD"
    assert len(rec["confirmed_discrepancies"]) == 1
    assert rec["confirmed_discrepancies"][0]["variance_amount"] == 2500.00
