import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class EvidenceLedgerEntry(Base):
    __tablename__ = "evidence_ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(String(100), nullable=True, index=True) # Unique transaction tracking ID
    item_description = Column(String(255), nullable=False)
    supplier_name = Column(String(255), nullable=True) # Supplier / vendor identity
    
    # Financial references and amounts
    po_reference = Column(String(100), nullable=True, index=True)
    po_amount = Column(Float, nullable=True) # Expected / authorized amount
    invoice_number = Column(String(100), nullable=True, index=True)
    invoice_amount = Column(Float, nullable=True) # Billed amount
    receipt_proof = Column(String(100), nullable=True)
    receipt_amount = Column(Float, nullable=True)
    paid_amount = Column(Float, nullable=True) # Supported disbursed amount (from single or multiple receipts)
    approved_variation_amount = Column(Float, default=0.0) # Approved variation / change order sum
    
    variance_amount = Column(Float, nullable=True) # Financial variance
    variance_reason = Column(String(500), nullable=True)
    currency = Column(String(10), nullable=True)
    
    # Reconciliation Status & Confidence
    reconciliation_status = Column(String(50), nullable=False) 
    # e.g., RECONCILED_MATCH, RECONCILED_WITH_VARIATION, PARTIAL_PAYMENT, MULTI_INVOICE_PO, 
    # MULTI_RECEIPT_INVOICE, VARIANCE_HOLD, MISSING_RECEIPT, MISSING_PO, UNVERIFIED, CONFLICTING_EVIDENCE
    
    match_confidence = Column(String(50), default="EXACT_MATCH") 
    # EXACT_MATCH, PROBABLE_MATCH, PARTIAL_MATCH, UNMATCHED, CONFLICTING_EVIDENCE
    
    requires_human_review = Column(Boolean, default=False)
    human_review_reason = Column(String(500), nullable=True)
    
    # Multi-document 1:N relations and breakdowns
    multiple_invoices_breakdown = Column(JSON, default=list) # [{invoice_number, amount, doc_id}]
    multiple_receipts_breakdown = Column(JSON, default=list) # [{receipt_id, amount, doc_id}]
    project_report_reference = Column(String(100), nullable=True) # Aggregate report tracking
    report_reconciled = Column(Boolean, default=False)
    
    # Provenance
    source_file_paths = Column(JSON, default=list)
    po_document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    invoice_document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    receipt_document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_document_ids = Column(JSON, default=list) # All connected Document IDs
    matching_criteria = Column(JSON, default=dict) # Match rules applied

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    investigation = relationship("Investigation", back_populates="ledger_entries")
    po_document = relationship("Document", foreign_keys=[po_document_id])
    invoice_document = relationship("Document", foreign_keys=[invoice_document_id])
    receipt_document = relationship("Document", foreign_keys=[receipt_document_id])
