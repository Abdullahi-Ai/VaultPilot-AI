from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.document import DocumentOut

class EvidenceLedgerEntryBase(BaseModel):
    transaction_id: Optional[str] = None
    item_description: str
    supplier_name: Optional[str] = None
    
    # Financial references and amounts
    po_reference: Optional[str] = None
    po_amount: Optional[float] = None
    invoice_number: Optional[str] = None
    invoice_amount: Optional[float] = None
    receipt_proof: Optional[str] = None
    receipt_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    approved_variation_amount: float = 0.0
    
    variance_amount: Optional[float] = None
    variance_reason: Optional[str] = None
    currency: Optional[str] = None
    
    reconciliation_status: str
    match_confidence: str = "EXACT_MATCH"
    requires_human_review: bool = False
    human_review_reason: Optional[str] = None
    
    multiple_invoices_breakdown: List[Dict[str, Any]] = []
    multiple_receipts_breakdown: List[Dict[str, Any]] = []
    project_report_reference: Optional[str] = None
    report_reconciled: bool = False
    
    source_file_paths: List[str] = []
    
    # Traceability IDs
    po_document_id: Optional[int] = None
    invoice_document_id: Optional[int] = None
    receipt_document_id: Optional[int] = None
    source_document_ids: List[int] = []
    matching_criteria: Dict[str, Any] = {}

class EvidenceLedgerEntryCreate(EvidenceLedgerEntryBase):
    investigation_id: int

class EvidenceLedgerEntryOut(EvidenceLedgerEntryBase):
    id: int
    investigation_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EvidenceLedgerEntryDetailOut(EvidenceLedgerEntryOut):
    po_document: Optional[DocumentOut] = None
    invoice_document: Optional[DocumentOut] = None
    receipt_document: Optional[DocumentOut] = None

    model_config = ConfigDict(from_attributes=True)
