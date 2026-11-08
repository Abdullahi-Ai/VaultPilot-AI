import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), default="OTHER") # INVOICE, RECEIPT, PURCHASE_ORDER, EXPENSE_REPORT, OTHER
    extraction_status = Column(String(50), default="EXTRACTED") # EXTRACTED, UNAVAILABLE, UNVERIFIED
    extracted_data = Column(JSON, nullable=True) # Vendor, PO ref, Invoice #, amount, date, line items
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="documents")
    investigation = relationship("Investigation", backref="documents")
