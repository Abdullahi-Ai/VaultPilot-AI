import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for finding to source documents traceability
finding_documents = Table(
    "finding_documents",
    Base.metadata,
    Column("finding_id", Integer, ForeignKey("findings.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
)

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    classification = Column(String(50), nullable=False) # CONFIRMED_DISCREPANCY, POTENTIAL_ANOMALY, MISSING_EVIDENCE, UNVERIFIED
    subject_reference = Column(String(255), nullable=True)
    source_paths = Column(JSON, default=list) # List of original source file paths
    expected_value = Column(String(255), nullable=True)
    observed_value = Column(String(255), nullable=True)
    variance_explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    
    # Phase 2.1 Evidence Provenance & Explainability
    source_document_ids = Column(JSON, default=list) # Database IDs of linked Document records
    extracted_fields_used = Column(JSON, default=dict) # Dict of fields/values used in finding
    comparison_details = Column(JSON, default=dict) # Calculation, mathematical variance, and compared fields
    evidence_limitations = Column(Text, nullable=True) # Confidence limits & directory scope boundaries
    missing_evidence_details = Column(Text, nullable=True) # Specific missing documents/records
    classification_rationale = Column(Text, nullable=True) # Reason why classification was assigned

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    investigation = relationship("Investigation", back_populates="findings")
    documents = relationship("Document", secondary=finding_documents, backref="linked_findings")
