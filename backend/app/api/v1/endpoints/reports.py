from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.investigation import Investigation
from app.schemas.report import ReportCreateRequest, InvestigationReportOut, InvestigationReportSummaryOut
from app.services.report_service import ReportService
from app.services.csv_exporter import ReportIntegrityError

router = APIRouter()

@router.post("/investigations/{investigation_id}/reports", response_model=InvestigationReportOut, status_code=status.HTTP_201_CREATED)
def create_investigation_report(
    investigation_id: int,
    req: ReportCreateRequest = ReportCreateRequest(),
    db: Session = Depends(get_db)
):
    """
    Creates an immutable report snapshot for the specified investigation.
    Captures findings, evidence register, and currency-segregated financial summaries.
    """
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID {investigation_id} not found."
        )

    try:
        report = ReportService.create_report_snapshot(
            db=db,
            investigation_id=investigation_id,
            title=req.title,
            report_status=req.report_status or "FINAL"
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report snapshot creation failed: {str(e)}"
        )

@router.get("/investigations/{investigation_id}/reports", response_model=List[InvestigationReportSummaryOut])
def list_investigation_reports(
    investigation_id: int,
    db: Session = Depends(get_db)
):
    """
    Lists all report snapshot versions for an investigation.
    """
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID {investigation_id} not found."
        )

    return ReportService.list_reports_for_investigation(db=db, investigation_id=investigation_id)

@router.get("/reports/{report_id}", response_model=InvestigationReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves a stored report snapshot by report ID.
    Data is served directly from the immutable stored snapshot without recomputing.
    """
    report = ReportService.get_report(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found."
        )
    return report

@router.get("/reports/{report_id}/markdown", response_class=Response)
def get_report_markdown(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Renders an audit-grade Markdown dossier exclusively from the immutable stored snapshot payload.
    Returns text/markdown with UTF-8 encoding.
    """
    try:
        markdown_text = ReportService.get_report_markdown(db=db, report_id=report_id)
        return Response(
            content=markdown_text,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'inline; filename="audit_dossier_report_{report_id}.md"'
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/investigations/{investigation_id}/reports/{report_id}/markdown", response_class=Response)
def get_investigation_report_markdown(
    investigation_id: int,
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Renders an audit-grade Markdown dossier for a specific investigation report.
    Validates investigation ID matches the report record.
    """
    report = ReportService.get_report(db=db, report_id=report_id)
    if not report or report.investigation_id != investigation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found for investigation {investigation_id}."
        )
    return get_report_markdown(report_id=report_id, db=db)

@router.get("/investigations/{investigation_id}/reports/{report_id}/html", response_class=Response)
def get_investigation_report_html(
    investigation_id: int,
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    Renders a publication-ready, printable HTML5 audit dossier for a specific investigation report.
    Enforces strict investigation ownership and fail-closed cryptographic snapshot integrity gating.
    Delivers HTTP Content-Security-Policy headers including frame-ancestors 'none'.
    """
    # 1. Verify existence and investigation ownership
    report = ReportService.get_report(db=db, report_id=report_id)
    if not report or report.investigation_id != investigation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found for investigation {investigation_id}."
        )

    # 2. Render through service with fail-closed integrity gating
    try:
        html_content = ReportService.get_report_html(db=db, report_id=report_id)
        version = report.report_version
        filename = f"audit_dossier_report_{report_id}_v{version}.html"

        csp_header = (
            "default-src 'none'; "
            "style-src 'unsafe-inline'; "
            "img-src data:; "
            "frame-ancestors 'none'; "
            "base-uri 'none'; "
            "form-action 'none';"
        )

        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Security-Policy": csp_header,
                "X-Frame-Options": "DENY",
                "X-Content-Type-Options": "nosniff"
            }
        )
    except ReportIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/investigations/{investigation_id}/reports/{report_id}/csv", response_class=Response)
def get_investigation_report_csv(
    investigation_id: int,
    report_id: int,
    schedule: str = Query("reconciliation", description="Schedule type: reconciliation, summary, findings, evidence"),
    include_metadata_header: bool = Query(False, description="Whether to include # audit comment header lines"),
    db: Session = Depends(get_db)
):
    """
    Exports a specific financial schedule from an immutable report snapshot in spreadsheet-safe CSV format.
    Enforces strict investigation ownership, fail-closed cryptographic snapshot integrity gating,
    formula-injection protection, and exact decimal preservation with UTF-8 BOM.
    """
    # 1. Verify existence and investigation ownership
    report = ReportService.get_report(db=db, report_id=report_id)
    if not report or report.investigation_id != investigation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found for investigation {investigation_id}."
        )

    # 2. Validate schedule parameter
    schedule_clean = schedule.lower().strip()
    valid_schedules = ("reconciliation", "summary", "findings", "evidence")
    if schedule_clean not in valid_schedules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid schedule '{schedule}'. Must be one of: {', '.join(valid_schedules)}."
        )

    # 3. Export through service with fail-closed integrity gating
    try:
        csv_text = ReportService.get_report_csv(
            db=db,
            report_id=report_id,
            schedule=schedule_clean,
            include_metadata_header=include_metadata_header
        )
        version = report.report_version
        filename = f"audit_report_{report_id}_{schedule_clean}_v{version}.csv"

        return Response(
            content=csv_text,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Content-Type-Options": "nosniff"
            }
        )
    except ReportIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
