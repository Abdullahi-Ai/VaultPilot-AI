#!/usr/bin/env bash
# ==============================================================================
# VaultPilot AI — Offline Local Emulation Demonstration Launcher
# Strictly isolates demonstration runtime from production database & storage.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DEMO_DB_PATH="${PROJECT_ROOT}/backend/demo_vaultpilot.db"
PRODUCTION_DB_PATH="${PROJECT_ROOT}/backend/vaultpilot.db"

echo "======================================================================"
echo "  VAULTPILOT AI — LOCAL EMULATION DEMONSTRATION WORKSPACE"
echo "  Standard: UGREEN UGOS / Uliya v0.7.3 (Offline Demonstration Mode)"
echo "======================================================================"

# --- 1. Mandatory Safety & Database Isolation Checks ---
DEMO_DATABASE_URL="sqlite:///${DEMO_DB_PATH}"

# Check environment override
REQUESTED_DB="${DATABASE_URL:-$DEMO_DATABASE_URL}"

# Resolve canonical paths to ensure zero accidental production mutation
if [[ "${REQUESTED_DB}" == *"backend/vaultpilot.db"* ]] || [[ "${REQUESTED_DB}" == *"sqlite:///./vaultpilot.db"* ]]; then
    echo "[SECURITY ERROR] Refusing to start demo: Target database points to production 'vaultpilot.db'!"
    echo "The demonstration must strictly run against an isolated disposable database."
    exit 1
fi

export DATABASE_URL="${DEMO_DATABASE_URL}"
export UGREEN_NAS_MODE="emulated"

echo "[Demo Setup] Mode: ${UGREEN_NAS_MODE} (EmulatedNASProvider active)"
echo "[Demo Setup] Isolated Database: ${DEMO_DB_PATH}"
echo "[Demo Setup] Production DB Protected: ${PRODUCTION_DB_PATH}"

# --- 2. Database Initialization (Clean Migration to Head) ---
echo "[Demo Setup] Applying database schema migrations to demo database..."
cd "${PROJECT_ROOT}/backend"
PYTHONPATH=. venv/bin/alembic upgrade head > /dev/null 2>&1

# --- 3. Seed Demo Project ---
PYTHONPATH=. venv/bin/python -c '
from app.core.database import SessionLocal
from app.models.project import Project
from app.models.investigation import Investigation
import os

db = SessionLocal()
try:
    existing = db.query(Project).filter(Project.code == "PRJ-DEMO-2026").first()
    if not existing:
        proj = Project(
            name="Solar Water & Medical Clinic Aid (Demo Project)",
            code="PRJ-DEMO-2026",
            budget=50000.0,
            currency="USD",
            nas_folder_path="/volume1/NGO_Projects/Water_Health_2026"
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)
        print(f"[Demo Setup] Seeded demo project ID: {proj.id} (Code: {proj.code})")
    else:
        print(f"[Demo Setup] Demo project ready (ID: {existing.id})")
finally:
    db.close()
'

echo "======================================================================"
echo "  DEMONSTRATION SCENARIOS AVAILABLE (EmulatedNASProvider):"
echo "  1. Complete Match:     PO-2026-081 (\$8.5k) == INV-SP-1092 (\$8.5k) == REC-BNK-993 (\$8.5k)"
echo "  2. Overbilling:        PO-MED-441 (\$12k) vs INV-MED-7712 (\$14.5k) (+\$2.5k Discrepancy)"
echo "     * Resolution:       Auditor reviews Credit Memo CM-01 and corrects invoice to \$12k"
echo "  3. Missing Evidence:   INV-UNSUPP-902 (\$2.4k) lacking purchase order and receipt"
echo "  4. Degraded Scan:      IMG_7781_blurry.jpg classified as UNVERIFIED (fail-closed)"
echo "======================================================================"
echo "Starting Backend API (http://localhost:8000)..."
echo "Starting Frontend Web (http://localhost:5173)..."
echo "Press Ctrl+C to terminate demonstration."

# Launch backend in background
PYTHONPATH=. venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Launch frontend
cd "${PROJECT_ROOT}/frontend"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; echo '[Demo Shutdown] Demonstration terminated.'" EXIT

wait
