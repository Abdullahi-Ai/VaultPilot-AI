from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from app.schemas.finding import FindingOut
from app.schemas.ledger import EvidenceLedgerEntryOut
from app.schemas.document import DocumentOut

class InvestigationRunRequest(BaseModel):
    project_id: int = Field(..., gt=0, description="Positive integer project ID")
    folder_path: str = Field(..., min_length=1, max_length=1000, description="Target NAS folder path to investigate")
    title: Optional[str] = Field("Routine Project Evidence Audit", max_length=255, description="Investigation title")

    @field_validator("folder_path")
    @classmethod
    def validate_folder_path(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("folder_path cannot be empty or whitespace only.")
        if ".." in cleaned:
            raise ValueError("Directory traversal characters ('..') are not permitted in folder_path.")
        return cleaned

class InvestigationTriggerRequest(BaseModel):
    project_id: int
    scope_path: Optional[str] = None
    title: Optional[str] = "Routine Project Evidence Audit"

class InvestigationOut(BaseModel):
    id: int
    project_id: int
    title: str
    scope_path: str
    status: str
    summary: Optional[str] = None
    verified_totals: Dict[str, float] = {}
    document_count: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[FindingOut] = []
    ledger_entries: List[EvidenceLedgerEntryOut] = []
    documents: List[DocumentOut] = []

    model_config = ConfigDict(from_attributes=True)

class DashboardStats(BaseModel):
    total_projects: int
    total_investigations: int
    total_documents_analyzed: int
    verified_spend_by_currency: Dict[str, float]
    findings_by_classification: Dict[str, int]
    ledger_status_breakdown: Dict[str, int]
