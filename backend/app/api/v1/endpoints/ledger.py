from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.ledger import EvidenceLedgerEntry
from app.schemas.ledger import EvidenceLedgerEntryOut, EvidenceLedgerEntryDetailOut

router = APIRouter()

@router.get("/", response_model=List[EvidenceLedgerEntryOut])
def list_ledger_entries(
    investigation_id: Optional[int] = None,
    reconciliation_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(EvidenceLedgerEntry)
    if investigation_id:
        query = query.filter(EvidenceLedgerEntry.investigation_id == investigation_id)
    if reconciliation_status:
        query = query.filter(EvidenceLedgerEntry.reconciliation_status == reconciliation_status.upper())
    return query.order_by(EvidenceLedgerEntry.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{entry_id}", response_model=EvidenceLedgerEntryDetailOut)
def get_ledger_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(EvidenceLedgerEntry).filter(EvidenceLedgerEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence ledger entry with ID {entry_id} not found."
        )
    return entry
