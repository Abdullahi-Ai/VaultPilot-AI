from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.document import DocumentOut

class FindingBase(BaseModel):
    title: str
    classification: str # CONFIRMED_DISCREPANCY, POTENTIAL_ANOMALY, MISSING_EVIDENCE, UNVERIFIED
    subject_reference: Optional[str] = None
    source_paths: List[str] = []
    expected_value: Optional[str] = None
    observed_value: Optional[str] = None
    variance_explanation: str
    recommended_action: str
    
    # Phase 2.1 Traceability fields
    source_document_ids: List[int] = []
    extracted_fields_used: Dict[str, Any] = {}
    comparison_details: Dict[str, Any] = {}
    evidence_limitations: Optional[str] = None
    missing_evidence_details: Optional[str] = None
    classification_rationale: Optional[str] = None

class FindingCreate(FindingBase):
    investigation_id: int

class FindingOut(FindingBase):
    id: int
    investigation_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FindingDetailOut(FindingOut):
    documents: List[DocumentOut] = []

    model_config = ConfigDict(from_attributes=True)
