from fastapi import APIRouter
from app.api.v1.endpoints import projects, investigations, findings, ledger, dashboard, documents, reports

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(investigations.router, prefix="/investigations", tags=["Investigations"])
api_router.include_router(findings.router, prefix="/findings", tags=["Findings"])
api_router.include_router(ledger.router, prefix="/ledger", tags=["Evidence Ledger"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(reports.router, tags=["Reports"])
