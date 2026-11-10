import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field

class FieldReviewVerifyRequest(BaseModel):
    reviewer_id: Optional[str] = Field(None, description="Optional reviewer identifier (not authenticated account)")
    notes: Optional[str] = Field(None, description="Auditor review notes")

class FieldReviewCorrectRequest(BaseModel):
    corrected_value: Any = Field(..., description="Reviewed/corrected value replacing original extracted value")
    reviewer_id: Optional[str] = Field(None, description="Optional reviewer identifier")
    notes: Optional[str] = Field(None, description="Auditor explanation for correction")

class FieldReviewRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Mandatory audit justification for rejecting field value")
    reviewer_id: Optional[str] = Field(None, description="Optional reviewer identifier")

class FieldReviewClarifyRequest(BaseModel):
    clarification_question: str = Field(..., min_length=1, description="Information or documentation required from field team")
    reviewer_id: Optional[str] = Field(None, description="Optional reviewer identifier")

class FieldReviewOut(BaseModel):
    id: int
    document_id: int
    field_name: str
    original_value: Optional[Any] = None
    reviewed_value: Optional[Any] = None
    status: str
    reviewer_id: Optional[str] = None
    review_timestamp: Optional[datetime.datetime] = None
    reviewer_notes: Optional[str] = None
    source_provenance: Optional[Dict[str, Any]] = None
    extraction_method: Optional[str] = None
    original_document_sha256: Optional[str] = None
    extraction_version: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}

class FieldReviewAuditLogOut(BaseModel):
    id: int
    field_review_id: int
    document_id: int
    field_name: str
    action: str
    previous_status: Optional[str] = None
    new_status: str
    previous_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None
    action_timestamp: datetime.datetime
    document_sha256: Optional[str] = None

    model_config = {"from_attributes": True}

class DocumentReviewSummaryOut(BaseModel):
    document_id: int
    filename: str
    document_type: str
    extraction_status: str
    sha256: Optional[str] = None
    total_fields: int
    pending_count: int
    verified_count: int
    corrected_count: int
    rejected_count: int
    clarification_count: int
    is_fully_reviewed: bool
    fields: List[FieldReviewOut]

    model_config = {"from_attributes": True}
