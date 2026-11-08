from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.investigation import Investigation
from app.models.project import Project
from app.schemas.investigation import InvestigationRunRequest, InvestigationTriggerRequest, InvestigationOut
from app.services.investigation_service import InvestigationService
from app.services.ugreen_bridge import (
    NASSecurityViolationError,
    NASInvalidPathError,
    NASFileMutationError,
    NASStorageUnavailableError,
    NASPathNotFoundError,
    NASPathUnreachableError
)

router = APIRouter()

@router.get("/", response_model=List[InvestigationOut])
def list_investigations(project_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Investigation)
    if project_id:
        query = query.filter(Investigation.project_id == project_id)
    return query.order_by(Investigation.created_at.desc()).offset(skip).limit(limit).all()

@router.post("/run", response_model=InvestigationOut, status_code=status.HTTP_201_CREATED)
def run_investigation(req: InvestigationRunRequest, db: Session = Depends(get_db)):
    # Explicit validation of project_id and folder_path
    if not req.folder_path or not req.folder_path.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="folder_path is required and cannot be empty or whitespace only."
        )

    if ".." in req.folder_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Directory traversal characters ('..') are not permitted in folder_path."
        )

    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {req.project_id} does not exist."
        )

    try:
        investigation = InvestigationService.run_investigation(
            db=db,
            project_id=req.project_id,
            scope_path=req.folder_path,
            title=req.title or f"Audit of {project.name}"
        )
        return investigation
    except NASSecurityViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security violation: {str(e)}"
        )
    except NASInvalidPathError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path: {str(e)}"
        )
    except NASStorageUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NAS storage unavailable: {str(e)}"
        )
    except NASPathNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target directory not found: {str(e)}"
        )
    except NASPathUnreachableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NAS path unreachable: {str(e)}"
        )
    except NASFileMutationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Evidence file was concurrently mutated: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation execution failed: {str(e)}"
        )

@router.post("/trigger", response_model=InvestigationOut, status_code=status.HTTP_201_CREATED)
def trigger_investigation(req: InvestigationRunRequest, db: Session = Depends(get_db)):
    """Backward compatibility alias for /run"""
    return run_investigation(req, db)

@router.get("/{investigation_id}", response_model=InvestigationOut)
def get_investigation(investigation_id: int, db: Session = Depends(get_db)):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found.")
    return investigation
