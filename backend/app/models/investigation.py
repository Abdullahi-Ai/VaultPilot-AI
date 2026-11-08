import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    scope_path = Column(String(500), nullable=False)
    status = Column(String(50), default="COMPLETED") # PENDING, IN_PROGRESS, COMPLETED, FAILED
    summary = Column(Text, nullable=True)
    verified_totals = Column(JSON, default=dict) # e.g. {"USD": 12500.0, "EUR": 3200.0}
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="investigations")
    findings = relationship("Finding", back_populates="investigation", cascade="all, delete-orphan")
    ledger_entries = relationship("EvidenceLedgerEntry", back_populates="investigation", cascade="all, delete-orphan")
