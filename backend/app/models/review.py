import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from app.core.database import Base

class ReviewStatus:
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"
    REQUIRES_CLARIFICATION = "REQUIRES_CLARIFICATION"

    ALL = {PENDING, VERIFIED, CORRECTED, REJECTED, REQUIRES_CLARIFICATION}


class DocumentFieldReview(Base):
    """
    Stores human verification, correction, and review status of an individual
    extracted financial field, preserving the original extracted value untouched.
    """
    __tablename__ = "document_field_reviews"
    __table_args__ = (
        UniqueConstraint("document_id", "field_name", name="uq_document_field_review"),
    )

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    original_value = Column(JSON, nullable=True)
    reviewed_value = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default=ReviewStatus.PENDING, index=True)
    reviewer_id = Column(String(100), nullable=True)
    review_timestamp = Column(DateTime, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    source_provenance = Column(JSON, nullable=True)
    extraction_method = Column(String(100), nullable=True)
    original_document_sha256 = Column(String(64), nullable=True)
    extraction_version = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", backref=backref("field_reviews", cascade="all, delete-orphan"))
    audit_history = relationship(
        "FieldReviewAuditLog",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="FieldReviewAuditLog.action_timestamp.desc()"
    )


class FieldReviewAuditLog(Base):
    """
    Immutable, append-only audit trail recording every state transition,
    correction, verification, and rejection action on extracted fields.
    """
    __tablename__ = "field_review_history"

    id = Column(Integer, primary_key=True, index=True)
    field_review_id = Column(Integer, ForeignKey("document_field_reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    reviewer_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    action_timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    document_sha256 = Column(String(64), nullable=True)

    # Relationships
    review = relationship("DocumentFieldReview", back_populates="audit_history")
    document = relationship("Document", backref=backref("review_audit_logs", cascade="all, delete-orphan"))
