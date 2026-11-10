from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.review_service import EvidenceReviewService
from app.schemas.review import (
    FieldReviewOut,
    FieldReviewAuditLogOut,
    DocumentReviewSummaryOut,
    FieldReviewVerifyRequest,
    FieldReviewCorrectRequest,
    FieldReviewRejectRequest,
    FieldReviewClarifyRequest
)

router = APIRouter()

@router.get("/reviews/pending", response_model=List[FieldReviewOut], tags=["Evidence Review"])
@router.get("/reviews", response_model=List[FieldReviewOut], tags=["Evidence Review"])
def list_pending_field_reviews(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    investigation_id: Optional[int] = Query(None, description="Filter by investigation ID"),
    status: Optional[str] = Query(None, description="Filter by review status (PENDING, VERIFIED, CORRECTED, REJECTED, REQUIRES_CLARIFICATION)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List extracted financial fields awaiting review across documents.
    """
    return EvidenceReviewService.list_pending_reviews(
        db=db,
        project_id=project_id,
        investigation_id=investigation_id,
        status_filter=status,
        skip=skip,
        limit=limit
    )

@router.get("/documents/{document_id}/reviews", response_model=DocumentReviewSummaryOut, tags=["Evidence Review"])
def get_document_reviews(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve current field review status, counts, and field breakdowns for a document.
    """
    return EvidenceReviewService.get_document_review_summary(db=db, document_id=document_id)

@router.post("/documents/{document_id}/reviews/initialize", response_model=List[FieldReviewOut], tags=["Evidence Review"])
def initialize_document_reviews(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Explicitly initialize or sync field review entries from the document's extraction payload.
    """
    return EvidenceReviewService.get_or_initialize_reviews(db=db, document_id=document_id)

@router.get("/documents/{document_id}/reviews/history", response_model=List[FieldReviewAuditLogOut], tags=["Evidence Review"])
def get_document_review_history(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve the immutable audit history of all review actions on a document.
    """
    return EvidenceReviewService.get_document_review_history(db=db, document_id=document_id)

@router.get("/documents/{document_id}/reviews/{field_name}", response_model=FieldReviewOut, tags=["Evidence Review"])
def get_field_review(
    document_id: int,
    field_name: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve review status and provenance details for a specific field.
    """
    return EvidenceReviewService.get_field_review(db=db, document_id=document_id, field_name=field_name)

@router.post("/documents/{document_id}/reviews/{field_name}/verify", response_model=FieldReviewOut, tags=["Evidence Review"])
def verify_extracted_field(
    document_id: int,
    field_name: str,
    payload: FieldReviewVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify an extracted field as accurate without modifying the original extracted value.
    """
    return EvidenceReviewService.verify_field(
        db=db,
        document_id=document_id,
        field_name=field_name,
        reviewer_id=payload.reviewer_id,
        notes=payload.notes
    )

@router.post("/documents/{document_id}/reviews/{field_name}/correct", response_model=FieldReviewOut, tags=["Evidence Review"])
def correct_extracted_field(
    document_id: int,
    field_name: str,
    payload: FieldReviewCorrectRequest,
    db: Session = Depends(get_db)
):
    """
    Store an auditor-corrected field value while preserving the original extracted value untouched.
    """
    return EvidenceReviewService.correct_field(
        db=db,
        document_id=document_id,
        field_name=field_name,
        corrected_value=payload.corrected_value,
        reviewer_id=payload.reviewer_id,
        notes=payload.notes
    )

@router.post("/documents/{document_id}/reviews/{field_name}/reject", response_model=FieldReviewOut, tags=["Evidence Review"])
def reject_extracted_field(
    document_id: int,
    field_name: str,
    payload: FieldReviewRejectRequest,
    db: Session = Depends(get_db)
):
    """
    Reject an erroneous extracted field value. Excludes the field from verified financial calculations.
    """
    return EvidenceReviewService.reject_field(
        db=db,
        document_id=document_id,
        field_name=field_name,
        reviewer_id=payload.reviewer_id,
        reason=payload.reason
    )

@router.post("/documents/{document_id}/reviews/{field_name}/clarify", response_model=FieldReviewOut, tags=["Evidence Review"])
def request_field_clarification(
    document_id: int,
    field_name: str,
    payload: FieldReviewClarifyRequest,
    db: Session = Depends(get_db)
):
    """
    Flag an extracted field as requiring clarification from the field team or procurement officer.
    """
    return EvidenceReviewService.request_clarification(
        db=db,
        document_id=document_id,
        field_name=field_name,
        reviewer_id=payload.reviewer_id,
        clarification_question=payload.clarification_question
    )

@router.post("/documents/{document_id}/reconcile", tags=["Evidence Review"])
def trigger_document_re_reconciliation(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Trigger reconciliation re-evaluation for the investigation containing this document,
    updating live findings, ledger entries, and verified totals based on review decisions.
    """
    from app.models.document import Document
    from app.models.investigation import Investigation
    from app.services.investigation_service import InvestigationService

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found.")

    inv_id = doc.investigation_id
    if not inv_id:
        # Find latest investigation for this project
        latest_inv = db.query(Investigation).filter(Investigation.project_id == doc.project_id).order_by(Investigation.created_at.desc()).first()
        if latest_inv:
            inv_id = latest_inv.id

    if not inv_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No investigation associated with this document or its project.")

    inv = InvestigationService.reconcile_investigation(db=db, investigation_id=inv_id)
    return {
        "status": "SUCCESS",
        "investigation_id": inv.id,
        "document_id": document_id,
        "verified_totals": inv.verified_totals,
        "summary": inv.summary
    }
