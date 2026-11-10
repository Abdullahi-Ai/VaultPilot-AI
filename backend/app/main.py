from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models import Project
from app.services.investigation_service import InvestigationService
from app.api.v1.router import api_router

def init_db_and_seed():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Seed initial demonstration data if empty
    db = SessionLocal()
    try:
        if db.query(Project).count() == 0:
            demo_project = Project(
                name="Solar Water Sanitation Initiative",
                code="PRJ-WASH-2026",
                donor="Global Humanitarian Water Fund",
                budget=50000.0,
                currency="USD",
                nas_folder_path="/volume1/NGO_Projects/Solar_Water_2026",
                description="Community clean water solar pump installation across rural primary schools."
            )
            db.add(demo_project)
            db.commit()
            db.refresh(demo_project)

            demo_project_2 = Project(
                name="Rural Mobile Health Clinic",
                code="PRJ-MED-2026",
                donor="International Health Partnership",
                budget=75000.0,
                currency="USD",
                nas_folder_path="/volume1/NGO_Projects/Clinic_Rehab",
                description="Mobile clinical outreach units and basic pharmaceutical supplies."
            )
            db.add(demo_project_2)
            db.commit()
            db.refresh(demo_project_2)

            # Auto-run baseline demo investigation if storage is reachable
            try:
                InvestigationService.run_investigation(
                    db=db,
                    project_id=demo_project.id,
                    title="Baseline Financial Evidence Audit"
                )
            except Exception as e:
                # In physical NAS mode, storage volume may not yet be mounted at initial startup
                pass
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and seeds
    init_db_and_seed()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Financial Evidence Investigation REST API for NGOs & Development Agencies",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root check
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "standard": "Uliya NAS Integration Compliant"
    }

# API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
