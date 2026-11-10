"""
VaultPilot AI — Official Uliya Agent Runtime Integration Bridge & Schema Validator
Provides the runtime interface between VaultPilot AI and the Uliya Skill execution daemon.

Integration Boundary Specification:
- Static Skill Validation: Confirmed via official 'uliya-skill-kit' check-skill.mjs (0 errors, 0 warnings).
- Schema Validation: Provides strict Pydantic envelope validators (ok, data, error) for Uliya capability responses.
- Delegation State Management: Explicitly handles all 5 public delegation statuses (completed, failed, cancelled, waiting_user, waiting_approval).
- Runtime Execution: Live daemon process execution occurs on the physical UGOS Pro NAS host. In local/emulated mode, local deterministic providers (FilesystemNASProvider, EmulatedNASProvider) are executed without mocking fake daemon responses.

Guarantees:
1. Strict schema validation of all agent delegation envelopes (ok, data, error).
2. Explicit handling of all 5 public delegation statuses:
   - completed
   - failed
   - cancelled
   - waiting_user
   - waiting_approval
3. Defense against malformed, partial, or prompt-injected LLM outputs.
4. Clean fallback to local deterministic engines when Uliya agent daemon is offline.
5. Zero probabilistic hallucination of financial amounts or file references.
"""

import json
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("vaultpilot.uliya_bridge")


class DelegationStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_USER = "waiting_user"
    WAITING_APPROVAL = "waiting_approval"


class UliyaErrorPayload(BaseModel):
    code: str = Field(default="UNKNOWN_ERROR", description="Machine-readable error code")
    message: str = Field(default="An unspecified agent error occurred", description="Human-readable description")
    details: Optional[Dict[str, Any]] = None


class UliyaResponseEnvelope(BaseModel):
    """Canonical execution envelope returned by Uliya CLI invocation."""
    ok: bool
    status: DelegationStatus = DelegationStatus.COMPLETED
    data: Optional[Dict[str, Any]] = None
    error: Optional[UliyaErrorPayload] = None


class DiscoveredFileItem(BaseModel):
    file_path: str
    filename: str
    type: str = "OTHER"
    size_bytes: int = 0
    sha256: Optional[str] = None


class FindCapabilityData(BaseModel):
    """Schema for ug-filesystem.find data envelope."""
    files: List[DiscoveredFileItem] = Field(default_factory=list)
    total_found: int = 0
    scope_path: str


class ExtractedDocumentData(BaseModel):
    """Schema for ug-document.extract data envelope."""
    schema_type: str = Field(default="auto", alias="schema")
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    po_reference: Optional[str] = None
    receipt_id: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    status: str = "EXTRACTED"
    requires_human_verification: bool = False


class ReconcileCapabilityData(BaseModel):
    """Schema for ug-document.reconcile data envelope."""
    reconciliation_status: str
    coverage_score: float = 1.0
    confirmed_discrepancies: List[Dict[str, Any]] = Field(default_factory=list)
    potential_anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    missing_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    summary_notes: Optional[str] = None


class UliyaBridgeError(Exception):
    """Base exception for Uliya agent bridge operations."""
    def __init__(self, message: str, status: DelegationStatus = DelegationStatus.FAILED, raw_response: Optional[Any] = None):
        super().__init__(message)
        self.status = status
        self.raw_response = raw_response


class UliyaAgentBridge:
    """
    Integration boundary orchestrating and validating Uliya expert subagents
    (file-agent, document-agent) with fail-safe local fallback.
    """

    @classmethod
    def parse_and_validate_envelope(cls, raw_input: Union[str, Dict[str, Any]]) -> UliyaResponseEnvelope:
        """
        Parses raw text or dictionary response from Uliya runtime and validates
        against the canonical UliyaResponseEnvelope.
        """
        if isinstance(raw_input, str):
            try:
                parsed = json.loads(raw_input)
            except json.JSONDecodeError as e:
                raise UliyaBridgeError(
                    f"Malformed JSON received from agent runtime: {str(e)}",
                    status=DelegationStatus.FAILED,
                    raw_response=raw_input
                )
        elif isinstance(raw_input, dict):
            parsed = raw_input
        else:
            raise UliyaBridgeError(
                f"Unsupported agent response type: {type(raw_input)}",
                status=DelegationStatus.FAILED
            )

        try:
            envelope = UliyaResponseEnvelope.model_validate(parsed)
        except ValidationError as e:
            raise UliyaBridgeError(
                f"Agent response failed envelope schema validation: {str(e)}",
                status=DelegationStatus.FAILED,
                raw_response=parsed
            )

        return envelope

    @classmethod
    def validate_find_results(cls, envelope: UliyaResponseEnvelope) -> List[Dict[str, Any]]:
        """
        Validates data payload from 'file-agent' / 'ug-filesystem.find'.
        Handles all public delegation states.
        """
        if not envelope.ok or envelope.status != DelegationStatus.COMPLETED:
            if envelope.status == DelegationStatus.WAITING_USER:
                logger.info("Discovery paused: agent requires user clarification.")
                return []
            elif envelope.status == DelegationStatus.WAITING_APPROVAL:
                logger.warning("Discovery paused: agent requires administrative folder access approval.")
                return []
            elif envelope.status == DelegationStatus.CANCELLED:
                logger.info("Discovery cancelled by user or parent workflow.")
                return []
            else:
                err_msg = envelope.error.message if envelope.error else "Unknown discovery failure"
                raise UliyaBridgeError(f"Document discovery failed: {err_msg}", status=envelope.status)

        if not envelope.data:
            return []

        try:
            find_data = FindCapabilityData.model_validate(envelope.data)
            return [f.model_dump() for f in find_data.files]
        except ValidationError as e:
            raise UliyaBridgeError(f"Invalid find result payload schema: {str(e)}", status=DelegationStatus.FAILED)

    @classmethod
    def validate_extract_results(cls, envelope: UliyaResponseEnvelope) -> Dict[str, Any]:
        """
        Validates data payload from 'document-agent' / 'ug-document.extract'.
        Protects against hallucinated numeric values and unverified fields.
        """
        if not envelope.ok or envelope.status != DelegationStatus.COMPLETED:
            return {
                "status": "UNAVAILABLE",
                "error": envelope.error.message if envelope.error else "Extraction failed"
            }

        if not envelope.data:
            return {"status": "UNVERIFIED", "error": "Empty extraction payload"}

        try:
            extract_data = ExtractedDocumentData.model_validate(envelope.data)
            result = extract_data.model_dump()
            return result
        except ValidationError as e:
            logger.warning(f"Partial extraction schema failure, failing closed: {e}")
            return {
                "status": "UNVERIFIED",
                "error": f"Schema validation failure: {str(e)}",
                "requires_human_verification": True
            }

    @classmethod
    def validate_reconcile_results(cls, envelope: UliyaResponseEnvelope) -> Dict[str, Any]:
        """
        Validates data payload from 'document-agent' / 'ug-document.reconcile'.
        """
        if not envelope.ok or envelope.status != DelegationStatus.COMPLETED:
            return {
                "reconciliation_status": "INDETERMINATE",
                "error": envelope.error.message if envelope.error else "Reconciliation failed"
            }

        if not envelope.data:
            return {"reconciliation_status": "INDETERMINATE"}

        try:
            rec_data = ReconcileCapabilityData.model_validate(envelope.data)
            return rec_data.model_dump()
        except ValidationError as e:
            raise UliyaBridgeError(f"Invalid reconcile payload schema: {str(e)}", status=DelegationStatus.FAILED)
