import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class InvestigationReport(Base):
    __tablename__ = "investigation_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    report_version = Column(Integer, nullable=False, default=1)
    report_status = Column(String(50), nullable=False, default="FINAL") # FINAL, DRAFT, SUPERSEDED
    report_title = Column(String(255), nullable=False)
    generation_timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    reporting_schema_version = Column(String(50), default="1.0.0", nullable=False)
    methodology_version = Column(String(100), default="VaultPilot-Audit-Methodology-2.0", nullable=False)
    investigation_scope = Column(String(500), nullable=False)
    executive_summary = Column(Text, nullable=True)
    financial_summary = Column(JSON, default=dict, nullable=False)
    investigation_limitations = Column(Text, nullable=True)
    requires_human_review = Column(Boolean, default=False)
    snapshot_payload = Column(JSON, nullable=False)
    snapshot_integrity_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", backref="reports")
    investigation = relationship("Investigation", backref="reports")

    __table_args__ = (
        Index("ix_reports_investigation_version", "investigation_id", "report_version", unique=True),
    )
