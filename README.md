# VaultPilot AI — Autonomous Financial Evidence Investigation for UGREEN AI NAS

[![UGREEN Hackathon 2026](https://img.shields.io/badge/UGREEN%20Hackathon-2026-00C853?style=flat-square)](https://ai.ugreen.com)
[![Track: Automate Your Workflow](https://img.shields.io/badge/Track-Automate%20Your%20Workflow-blue?style=flat-square)](https://ai.ugreen.com)
[![Uliya Skill Kit](https://img.shields.io/badge/Uliya%20Skill-v2.0.0%20Static%20Pass-brightgreen?style=flat-square)](https://ai.ugreen.com)
[![Tests Passing](https://img.shields.io/badge/Tests-183%20Passed-success?style=flat-square)](backend/tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

> **"Every transaction needs evidence. Every finding needs a source."**

VaultPilot AI is a NAS-native financial evidence investigation platform designed for international non-governmental organizations (NGOs), development agencies, and compliance officers. Operating **100% locally on UGREEN AI NAS (UGOS Pro)**, VaultPilot automates forensic three-way reconciliation across purchase orders, vendor invoices, payment receipts, and bank vouchers without sending a single byte of sensitive financial data to public cloud AI.

---

## Quick Navigation for Hackathon Judges

- [Quickstart: Run in 3 Minutes](#quickstart-run-in-3-minutes)
- [Architecture & Repository Structure](#architecture--repository-structure)
- [How to Run Automated Tests (183 Tests)](#how-to-run-automated-tests)
- [How to Validate the UGREEN Skill Package](#how-to-validate-the-ugreen-skill-package)
- [UGOS Container Station Deployment (Docker Compose)](#ugos-container-station-deployment)
- [Security & Forensic Integrity Architecture](#security--forensic-integrity-architecture)
- [Complete Documentation Index](#complete-documentation-index)
- [Transparent Hardware Status Disclosure](#transparent-hardware-status-disclosure)

---

## Quickstart: Run in 3 Minutes

Independent judges can run and evaluate VaultPilot AI immediately using the local demo environment without requiring access to physical NAS hardware.

### Option A: One-Command Demonstration Launcher (Recommended)

The automated demo launcher configures an isolated demo database (`demo_vaultpilot.db`), starts the backend API on port 8000, and launches the React frontend on port 5173:

```bash
# Clone the repository
git clone https://github.com/Abdullahi-Ai/VaultPilot-AI.git
cd VaultPilot-AI

# Run the automated demo launcher
bash scripts/run_demo.sh
```

Open your browser to **`http://localhost:5173`** to access the complete application.

---

### Option B: Manual Step-by-Step Setup

#### 1. Backend REST API Setup (FastAPI)
```bash
cd backend

# Create and activate Python 3.10 virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server with isolated demonstration database
export DATABASE_URL="sqlite:///./demo_vaultpilot.db"
export UGREEN_NAS_MODE="emulated"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*Backend API documentation is available at `http://localhost:8000/docs`.*

#### 2. Frontend Web Interface Setup (React + Vite + Tailwind CSS)
```bash
# In a new terminal window:
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
*Frontend interface is available at `http://localhost:5173`.*

---

## Architecture & Repository Structure

VaultPilot AI enforces clean architectural decoupling between the **declarative UGREEN Skill package** and the **full-stack investigation application**:

```
VaultPilot-AI/
├── README.md                      # Primary project overview & judge quickstart manual
├── docker-compose.nas.yml         # Hardened UGOS Container Station deployment file
├── .env.example                   # Environment configuration template for UGREEN NAS
├── vaultpilot/                    # Official UGREEN Skill Package Source (Uliya v2.0.0)
│   ├── SKILL.md                   # Skill entry point & agentic capability orchestration
│   └── references/                # Auditing taxonomies & submission disclosures
├── backend/                       # Forensic Investigation REST API (Python/FastAPI)
│   ├── Dockerfile                 # Hardened unprivileged containerfile (UID 1000)
│   ├── requirements.txt           # Python backend dependencies
│   ├── app/                       # FastAPI endpoints, ORM models, reconciliation logic
│   └── tests/                     # 183 automated unit, integration, and security tests
├── frontend/                      # Forensic Investigation UI (React 18 / TypeScript / Vite)
│   ├── Dockerfile                 # Multi-stage containerfile (Node build -> Nginx Alpine)
│   ├── nginx.conf                 # Hardened Nginx reverse proxy configuration
│   └── src/                       # Dashboard, Evidence Ledger, Review Drawer, Findings
├── dist/                          # Distributable Skill packages
│   ├── vaultpilot-skill.zip       # Original Round 1 submitted Skill package
│   └── vaultpilot-skill-round2-candidate.zip # Round 2 verified candidate package
├── scripts/                       # DevOps, packaging, and QA automation utilities
│   ├── run_demo.sh                # Isolated demonstration launcher
│   └── package_skill.py           # Skill packaging and static compliance auditor
└── docs/                          # Comprehensive technical reports and audit guides
```

---

## How to Run Automated Tests

The backend test suite contains **183 automated tests across 19 modules**, covering 3-way reconciliation, fail-closed accounting, path confinement, TOCTOU defense, FIFO rejection, and Tri-Mode storage:

```bash
# From repository root:
backend/venv/bin/pytest backend/tests/ -v
```

*Expected output: `183 passed, 5 warnings in ~23 seconds`.*

---

## How to Validate the UGREEN Skill Package

The `vaultpilot` Skill conforms strictly to the **Uliya Skill Development Standard v2.0.0**:

### 1. Using the Official Uliya Static Checker:
```bash
node /tmp/uliya-skill-kit/uliya-skill-kit/scripts/check-skill.mjs vaultpilot
```
*Expected output: `"status": "static-pass"`, 0 errors, 0 warnings.*

### 2. Using the Automated Packaging Auditor:
```bash
python3 scripts/package_skill.py
```
*Validates YAML frontmatter, audits file boundaries, runs the official static checker, and builds a deterministic package in `dist/vaultpilot-skill-round2-candidate.zip`.*

---

## UGOS Container Station Deployment

For physical UGREEN AI NAS hardware (`iDX6011 Pro` running UGOS Pro):

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate a secure random token for audit attestation
sed -i 's/change-this-to-a-secure-random-token-for-production-nas/'"$(openssl rand -hex 32)"'/g' .env

# 3. Launch via Container Station / Docker Compose
docker compose -f docker-compose.nas.yml up -d --build
```

### Container Security Profile:
- **Read-Only Root Filesystem:** Both containers configure `read_only: true`.
- **Unprivileged Non-Root User:** Runs strictly under UID `1000:1000`.
- **Dropped Linux Capabilities:** `cap_drop: [ALL]` removes all kernel capabilities.
- **Kernel-Enforced Read-Only Mount:** NAS source documents (`/volume1/NGO_Projects`) are bind-mounted with `:ro`.
- **No Residual Ingestion Leaks:** Ingestion scratch buffers use an in-memory `tmpfs` constrained to 64MB.

---

## Security & Forensic Integrity Architecture

1. **Deterministic 3-Way Reconciliation:** Unlike LLMs that hallucinate arithmetic, VaultPilot uses Python's exact `Decimal` engine to cross-examine Purchase Orders $\longleftrightarrow$ Invoices $\longleftrightarrow$ Payment Proofs.
2. **Conservative 4-Tier Audit Taxonomy:** Findings are categorized objectively into *Confirmed Discrepancy*, *Potential Anomaly*, *Missing Evidence*, and *Unverified Finding*. Corrupted or blurry scans credit \$0.00 project spend.
3. **Cryptographic Audit Attestation & Tamper Evidence:** Human auditor adjustments in the Evidence Review drawer are cryptographically signed using **HMAC-SHA256**, preserving raw extraction history and authenticating reviewer actions.
4. **Local Path Confinement:** Strictly confines file discovery to the authorized scope directory, rejecting directory traversal (`..`), symlink escapes, and non-regular special files (FIFOs/device nodes).
5. **TOCTOU Defense:** Measures file descriptor nanosecond timestamps (`mtime_ns`) and sizes before and after streaming SHA-256 calculation to abort if concurrent modification occurs.

---

## Complete Documentation Index

All technical guides and competition reports are available in the [`docs/`](docs/) directory:

| Document | Description |
|---|---|
| [`ROUND2_REPOSITORY_READINESS_AUDIT.md`](docs/ROUND2_REPOSITORY_READINESS_AUDIT.md) | Master repository readiness audit for hackathon judges. |
| [`ROUND2_CLEAN_CLONE_TEST_REPORT.md`](docs/ROUND2_CLEAN_CLONE_TEST_REPORT.md) | Reproducibility report from an isolated clean worktree. |
| [`ROUND2_REMAINING_WORK_PLAN.md`](docs/ROUND2_REMAINING_WORK_PLAN.md) | Prioritized remaining work plan and hardware onboarding protocol. |
| [`ROUND2_DEMO_VIDEO_SCRIPT.md`](docs/ROUND2_DEMO_VIDEO_SCRIPT.md) | 2m 50s timed video demo script for public submission. |
| [`ROUND2_VIDEO_SHOT_LIST.md`](docs/ROUND2_VIDEO_SHOT_LIST.md) | 15-shot camera matrix with Devpost screenshot references. |
| [`ROUND2_VIDEO_PRODUCTION_CHECKLIST.md`](docs/ROUND2_VIDEO_PRODUCTION_CHECKLIST.md) | Audio normalization, subtitle (.srt), and YouTube metadata specs. |
| [`ROUND2_COMPETITION_READINESS.md`](docs/ROUND2_COMPETITION_READINESS.md) | 11-criteria judge evaluation scorecard & competitive advantages. |
| [`ROUND2_SECURITY_AND_PRIVACY_AUDIT.md`](docs/ROUND2_SECURITY_AND_PRIVACY_AUDIT.md) | Local security controls, path confinement, and threat analysis. |
| [`ROUND2_UGREEN_INTEGRATION_PLAN.md`](docs/ROUND2_UGREEN_INTEGRATION_PLAN.md) | Tri-Mode Storage Architecture and UGOS Container Station deployment. |
| [`ROUND2_AGENTIC_WORKFLOW.md`](docs/ROUND2_AGENTIC_WORKFLOW.md) | 15-stage investigation lifecycle & Uliya capability contracts. |
| [`ROUND2_TESTING_AND_VALIDATION_REPORT.md`](docs/ROUND2_TESTING_AND_VALIDATION_REPORT.md) | Automated test execution matrix and verification evidence. |
| [`ROUND2_PHYSICAL_NAS_TEST_PROTOCOL.md`](docs/ROUND2_PHYSICAL_NAS_TEST_PROTOCOL.md) | Protocol for assigned physical hardware testing (Nov 22–28). |

---

## Transparent Hardware Status Disclosure

In accordance with official UGREEN Hackathon submission ethics:
- **Verified Offline Emulation:** The core financial investigation engine, 3-way reconciliation, REST API, React frontend, and Uliya schema validators have been tested and verified locally.
- **Physical UGREEN NAS Hardware Status:** Testing on genuine physical UGREEN AI NAS hardware (`iDX6011 Pro` running UGOS Pro) is scheduled for the official physical testing window (**November 22–28, 2026**). Zero fabricated claims of prior physical hardware execution are made.

---

## Competition Metadata

- **Competition:** UGREEN Hackathon 2026 on AI NAS
- **Track:** Automate Your Workflow
- **Skill Identifier:** `vaultpilot`
- **GitHub Repository:** [https://github.com/Abdullahi-Ai/VaultPilot-AI](https://github.com/Abdullahi-Ai/VaultPilot-AI)
- **Devpost Project:** [https://devpost.com/software/vaultpilot-ai](https://devpost.com/software/vaultpilot-ai)
