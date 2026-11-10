import datetime
import hashlib
import json
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.document import Document
from app.models.review import DocumentFieldReview, FieldReviewAuditLog, ReviewStatus

REVIEWABLE_FINANCIAL_FIELDS = [
    "amount",
    "currency",
    "vendor",
    "date",
    "po_reference",
    "invoice_number",
    "receipt_id",
    "tax_amount",
    "payment_reference",
    "payment_status",
]

class EvidenceReviewService:

    @classmethod
    def initialize_document_reviews(cls, db: Session, document: Document) -> List[DocumentFieldReview]:
        """
        Extracts reviewable fields from document.extracted_data and seeds DocumentFieldReview
        records in PENDING status without marking any as verified automatically.
        """
        extracted = document.extracted_data or {}
        provenance = extracted.get("provenance") or {}
        field_prov = extracted.get("field_provenance") or {}
        doc_sha256 = extracted.get("sha256") or provenance.get("sha256")
        ext_method = provenance.get("extraction_method") or "UNKNOWN"

        try:
            ext_ver = hashlib.sha256(json.dumps(extracted, sort_keys=True, default=str).encode()).hexdigest()[:16]
        except Exception:
            ext_ver = "v1"

        existing_reviews = {
            r.field_name: r for r in db.query(DocumentFieldReview).filter(DocumentFieldReview.document_id == document.id).all()
        }

        created_reviews = []
        now = datetime.datetime.utcnow()

        for field_name in REVIEWABLE_FINANCIAL_FIELDS:
            # We include fields if they exist in extracted data or field_provenance
            if field_name in extracted or field_name in field_prov:
                original_val = extracted.get(field_name)
                # If already present, don't overwrite
                if field_name in existing_reviews:
                    created_reviews.append(existing_reviews[field_name])
                    continue

                source_p = field_prov.get(field_name) or provenance

                review = DocumentFieldReview(
                    document_id=document.id,
                    field_name=field_name,
                    original_value=original_val,
                    reviewed_value=original_val,
                    status=ReviewStatus.PENDING,
                    reviewer_id=None,
                    review_timestamp=None,
                    reviewer_notes=None,
                    source_provenance=source_p,
                    extraction_method=ext_method,
                    original_document_sha256=doc_sha256,
                    extraction_version=ext_ver,
                    created_at=now,
                    updated_at=now
                )
                db.add(review)
                db.flush()

                # Add initial audit log
                audit = FieldReviewAuditLog(
                    field_review_id=review.id,
                    document_id=document.id,
                    field_name=field_name,
                    action="INITIALIZED",
                    previous_status=None,
                    new_status=ReviewStatus.PENDING,
                    previous_value=None,
                    new_value=original_val,
                    reviewer_id=None,
                    notes="Initialized from document extraction payload.",
                    action_timestamp=now,
                    document_sha256=doc_sha256
                )
                db.add(audit)
                created_reviews.append(review)

        db.commit()
        return created_reviews

    @classmethod
    def get_or_initialize_reviews(cls, db: Session, document_id: int) -> List[DocumentFieldReview]:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID {document_id} not found.")

        reviews = db.query(DocumentFieldReview).filter(DocumentFieldReview.document_id == document_id).all()
        if not reviews:
            reviews = cls.initialize_document_reviews(db, doc)
        return reviews

    @classmethod
    def get_field_review(cls, db: Session, document_id: int, field_name: str) -> DocumentFieldReview:
        cls.get_or_initialize_reviews(db, document_id)
        review = db.query(DocumentFieldReview).filter(
            DocumentFieldReview.document_id == document_id,
            DocumentFieldReview.field_name == field_name
        ).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Field '{field_name}' not found for document {document_id}."
            )
        return review

    @classmethod
    def verify_field(
        cls,
        db: Session,
        document_id: int,
        field_name: str,
        reviewer_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> DocumentFieldReview:
        review = cls.get_field_review(db, document_id, field_name)
        now = datetime.datetime.utcnow()
        prev_status = review.status
        prev_value = review.reviewed_value

        review.status = ReviewStatus.VERIFIED
        # Verified explicitly accepts the original value
        review.reviewed_value = review.original_value
        review.reviewer_id = reviewer_id
        review.review_timestamp = now
        review.reviewer_notes = notes
        review.updated_at = now

        audit = FieldReviewAuditLog(
            field_review_id=review.id,
            document_id=document_id,
            field_name=field_name,
            action="VERIFIED",
            previous_status=prev_status,
            new_status=ReviewStatus.VERIFIED,
            previous_value=prev_value,
            new_value=review.reviewed_value,
            reviewer_id=reviewer_id,
            notes=notes,
            action_timestamp=now,
            document_sha256=review.original_document_sha256
        )
        db.add(audit)
        db.commit()
        db.refresh(review)
        return review

    @classmethod
    def correct_field(
        cls,
        db: Session,
        document_id: int,
        field_name: str,
        corrected_value: Any,
        reviewer_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> DocumentFieldReview:
        review = cls.get_field_review(db, document_id, field_name)
        now = datetime.datetime.utcnow()
        prev_status = review.status
        prev_value = review.reviewed_value

        # STRICT: original_value is NEVER overwritten!
        review.status = ReviewStatus.CORRECTED
        review.reviewed_value = corrected_value
        review.reviewer_id = reviewer_id
        review.review_timestamp = now
        review.reviewer_notes = notes
        review.updated_at = now

        audit = FieldReviewAuditLog(
            field_review_id=review.id,
            document_id=document_id,
            field_name=field_name,
            action="CORRECTED",
            previous_status=prev_status,
            new_status=ReviewStatus.CORRECTED,
            previous_value=prev_value,
            new_value=corrected_value,
            reviewer_id=reviewer_id,
            notes=notes,
            action_timestamp=now,
            document_sha256=review.original_document_sha256
        )
        db.add(audit)
        db.commit()
        db.refresh(review)
        return review

    @classmethod
    def reject_field(
        cls,
        db: Session,
        document_id: int,
        field_name: str,
        reviewer_id: Optional[str] = None,
        reason: str = ""
    ) -> DocumentFieldReview:
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rejection requires an explicit audit reason/explanation."
            )

        review = cls.get_field_review(db, document_id, field_name)
        now = datetime.datetime.utcnow()
        prev_status = review.status
        prev_value = review.reviewed_value

        # Rejected values are excluded from calculations (reviewed_value = None)
        review.status = ReviewStatus.REJECTED
        review.reviewed_value = None
        review.reviewer_id = reviewer_id
        review.review_timestamp = now
        review.reviewer_notes = reason
        review.updated_at = now

        audit = FieldReviewAuditLog(
            field_review_id=review.id,
            document_id=document_id,
            field_name=field_name,
            action="REJECTED",
            previous_status=prev_status,
            new_status=ReviewStatus.REJECTED,
            previous_value=prev_value,
            new_value=None,
            reviewer_id=reviewer_id,
            notes=reason,
            action_timestamp=now,
            document_sha256=review.original_document_sha256
        )
        db.add(audit)
        db.commit()
        db.refresh(review)
        return review

    @classmethod
    def request_clarification(
        cls,
        db: Session,
        document_id: int,
        field_name: str,
        reviewer_id: Optional[str] = None,
        clarification_question: str = ""
    ) -> DocumentFieldReview:
        if not clarification_question or not clarification_question.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Clarification request requires an explicit question or documentation inquiry."
            )

        review = cls.get_field_review(db, document_id, field_name)
        now = datetime.datetime.utcnow()
        prev_status = review.status
        prev_value = review.reviewed_value

        review.status = ReviewStatus.REQUIRES_CLARIFICATION
        review.reviewer_id = reviewer_id
        review.review_timestamp = now
        review.reviewer_notes = clarification_question
        review.updated_at = now

        audit = FieldReviewAuditLog(
            field_review_id=review.id,
            document_id=document_id,
            field_name=field_name,
            action="REQUESTED_CLARIFICATION",
            previous_status=prev_status,
            new_status=ReviewStatus.REQUIRES_CLARIFICATION,
            previous_value=prev_value,
            new_value=prev_value,
            reviewer_id=reviewer_id,
            notes=clarification_question,
            action_timestamp=now,
            document_sha256=review.original_document_sha256
        )
        db.add(audit)
        db.commit()
        db.refresh(review)
        return review

    @classmethod
    def list_pending_reviews(
        cls,
        db: Session,
        project_id: Optional[int] = None,
        investigation_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentFieldReview]:
        query = db.query(DocumentFieldReview).join(Document, DocumentFieldReview.document_id == Document.id)
        if project_id:
            query = query.filter(Document.project_id == project_id)
        if investigation_id:
            query = query.filter(Document.investigation_id == investigation_id)
        if status_filter:
            query = query.filter(DocumentFieldReview.status == status_filter.upper())
        else:
            query = query.filter(DocumentFieldReview.status == ReviewStatus.PENDING)

        return query.order_by(DocumentFieldReview.created_at.desc()).offset(skip).limit(limit).all()

    @classmethod
    def get_document_review_summary(cls, db: Session, document_id: int) -> Dict[str, Any]:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID {document_id} not found.")

        reviews = cls.get_or_initialize_reviews(db, document_id)
        total = len(reviews)
        pending = sum(1 for r in reviews if r.status == ReviewStatus.PENDING)
        verified = sum(1 for r in reviews if r.status == ReviewStatus.VERIFIED)
        corrected = sum(1 for r in reviews if r.status == ReviewStatus.CORRECTED)
        rejected = sum(1 for r in reviews if r.status == ReviewStatus.REJECTED)
        clarification = sum(1 for r in reviews if r.status == ReviewStatus.REQUIRES_CLARIFICATION)

        extracted = doc.extracted_data or {}
        sha = extracted.get("sha256") or (extracted.get("provenance") or {}).get("sha256")

        return {
            "document_id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "extraction_status": doc.extraction_status,
            "sha256": sha,
            "total_fields": total,
            "pending_count": pending,
            "verified_count": verified,
            "corrected_count": corrected,
            "rejected_count": rejected,
            "clarification_count": clarification,
            "is_fully_reviewed": (pending == 0 and clarification == 0) and total > 0,
            "fields": reviews
        }

    @classmethod
    def get_document_review_history(cls, db: Session, document_id: int) -> List[FieldReviewAuditLog]:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID {document_id} not found.")

        return db.query(FieldReviewAuditLog).filter(
            FieldReviewAuditLog.document_id == document_id
        ).order_by(FieldReviewAuditLog.action_timestamp.desc(), FieldReviewAuditLog.id.desc()).all()

    @classmethod
    def get_effective_document_data(cls, doc: Document, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Calculates the effective extracted financial data view for reconciliation.
        Overlay review decisions without modifying doc.extracted_data or doc model in DB.
        """
        original_data = dict(doc.extracted_data or {})
        effective_data = dict(original_data)

        # Check reviews if db is available
        reviews = []
        if db:
            reviews = db.query(DocumentFieldReview).filter(DocumentFieldReview.document_id == doc.id).all()
        elif hasattr(doc, "field_reviews") and doc.field_reviews:
            reviews = doc.field_reviews

        if not reviews:
            return effective_data

        reviewed_overlay: Dict[str, Any] = {}
        has_pending = False
        has_rejected = False
        reviewed_fields_count = 0

        for r in reviews:
            fld = r.field_name
            if r.status == ReviewStatus.VERIFIED:
                val = r.original_value
                if fld in ("amount", "paid_amount", "po_amount", "invoice_amount", "budget", "total_amount") and val is not None:
                    try:
                        val = float(str(val).replace(",", "").replace("$", "").strip())
                    except (ValueError, TypeError):
                        pass
                effective_data[fld] = val
                reviewed_overlay[fld] = {
                    "status": "VERIFIED",
                    "original_value": r.original_value,
                    "effective_value": val,
                    "reviewer_id": r.reviewer_id,
                    "review_timestamp": r.review_timestamp.isoformat() if r.review_timestamp else None
                }
                reviewed_fields_count += 1
            elif r.status == ReviewStatus.CORRECTED:
                # Value is replaced by corrected value for calculations
                val = r.reviewed_value
                if fld in ("amount", "paid_amount", "po_amount", "invoice_amount", "budget", "total_amount") and val is not None:
                    try:
                        val = float(str(val).replace(",", "").replace("$", "").strip())
                    except (ValueError, TypeError):
                        pass
                effective_data[fld] = val
                effective_data[f"_original_{fld}"] = r.original_value
                reviewed_overlay[fld] = {
                    "status": "CORRECTED",
                    "original_value": r.original_value,
                    "effective_value": val,
                    "reviewer_id": r.reviewer_id,
                    "review_timestamp": r.review_timestamp.isoformat() if r.review_timestamp else None,
                    "notes": r.reviewer_notes
                }
                reviewed_fields_count += 1
            elif r.status == ReviewStatus.REJECTED:
                # Excluded from verified financial calculations
                effective_data[fld] = None
                effective_data[f"_rejected_{fld}"] = r.original_value
                has_rejected = True
                reviewed_overlay[fld] = {
                    "status": "REJECTED",
                    "original_value": r.original_value,
                    "effective_value": None,
                    "reviewer_id": r.reviewer_id,
                    "notes": r.reviewer_notes
                }
                reviewed_fields_count += 1
            elif r.status in (ReviewStatus.PENDING, ReviewStatus.REQUIRES_CLARIFICATION):
                has_pending = True

        effective_data["_human_review_overlay"] = reviewed_overlay

        # If primary financial fields (amount and currency) are human-verified or corrected:
        amt_review = next((r for r in reviews if r.field_name == "amount"), None)
        curr_review = next((r for r in reviews if r.field_name == "currency"), None)

        if amt_review and amt_review.status in (ReviewStatus.VERIFIED, ReviewStatus.CORRECTED):
            if curr_review and curr_review.status in (ReviewStatus.VERIFIED, ReviewStatus.CORRECTED):
                # Critical fields have been verified by human auditor
                effective_data["requires_human_verification"] = False
                effective_data["is_human_verified"] = True

        return effective_data
