from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict

from app.core.database import get_db
from app.models.project import Project
from app.models.document import Document
from app.models.investigation import Investigation
from app.models.finding import Finding
from app.models.ledger import EvidenceLedgerEntry
from app.schemas.investigation import DashboardStats

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_projects = db.query(Project).count()
    total_investigations = db.query(Investigation).count()
    total_documents = db.query(Document).count()

    # Findings breakdown
    finding_counts = (
        db.query(Finding.classification, func.count(Finding.id))
        .group_by(Finding.classification)
        .all()
    )
    findings_by_classification = {
        "CONFIRMED_DISCREPANCY": 0,
        "POTENTIAL_ANOMALY": 0,
        "MISSING_EVIDENCE": 0,
        "UNVERIFIED": 0,
    }
    for classification, count in finding_counts:
        findings_by_classification[classification] = count

    # Ledger breakdown
    ledger_counts = (
        db.query(EvidenceLedgerEntry.reconciliation_status, func.count(EvidenceLedgerEntry.id))
        .group_by(EvidenceLedgerEntry.reconciliation_status)
        .all()
    )
    ledger_status_breakdown = {
        "RECONCILED_MATCH": 0,
        "VARIANCE_HOLD": 0,
        "MISSING_RECEIPT": 0,
        "MISSING_PO": 0,
        "UNVERIFIED": 0,
    }
    for status, count in ledger_counts:
        ledger_status_breakdown[status] = count

    # Verified spend aggregation across completed investigations
    verified_spend_by_currency: Dict[str, float] = {}
    investigations = db.query(Investigation).filter(Investigation.status == "COMPLETED").all()
    for inv in investigations:
        if isinstance(inv.verified_totals, dict):
            for curr, amount in inv.verified_totals.items():
                verified_spend_by_currency[curr] = verified_spend_by_currency.get(curr, 0.0) + amount

    return DashboardStats(
        total_projects=total_projects,
        total_investigations=total_investigations,
        total_documents_analyzed=total_documents,
        verified_spend_by_currency=verified_spend_by_currency,
        findings_by_classification=findings_by_classification,
        ledger_status_breakdown=ledger_status_breakdown
    )
