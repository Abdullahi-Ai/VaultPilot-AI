from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.finding import Finding
from app.schemas.finding import FindingOut, FindingDetailOut

router = APIRouter()

@router.get("/", response_model=List[FindingOut])
def list_findings(
    investigation_id: Optional[int] = None,
    classification: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Finding)
    if investigation_id:
        query = query.filter(Finding.investigation_id == investigation_id)
    if classification:
        query = query.filter(Finding.classification == classification.upper())
    return query.order_by(Finding.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{finding_id}", response_model=FindingDetailOut)
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID {finding_id} not found."
        )
    return finding
