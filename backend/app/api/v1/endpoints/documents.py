from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentOut

router = APIRouter()

@router.get("/", response_model=List[DocumentOut])
def list_documents(
    project_id: Optional[int] = None,
    investigation_id: Optional[int] = None,
    document_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if project_id:
        query = query.filter(Document.project_id == project_id)
    if investigation_id:
        query = query.filter(Document.investigation_id == investigation_id)
    if document_type:
        query = query.filter(Document.document_type == document_type.upper())
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )
    return doc
