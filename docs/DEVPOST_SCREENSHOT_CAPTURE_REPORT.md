# VaultPilot AI — Official Devpost Screenshot Capture Report

**Document Status:** Final Audit & Deliverable Verification  
**Date:** November 10, 2026  
**Auditor / Specialist:** Senior QA Engineer & Product Presentation Specialist  
**Target Repository:** `/home/osama/VaultPilot-AI`  
**Output Directory:** `docs/devpost/screenshots/`  
**Capture Engine:** Headless Google Chrome (v148.0.7778.167)  
**Viewport Resolution:** 1920 × 1080 (Desktop Full HD, Device Scale Factor: 1.0)  
**Runtime Mode:** Offline Local Emulation (`UGREEN_NAS_MODE=emulated`, `EmulatedNASProvider`)  
**Database Isolation:** Disposable Demo Database (`backend/demo_vaultpilot.db`) — Production Database Protected

---

## 1. Executive Summary

Six genuine, high-resolution screenshots of the **VaultPilot AI** application have been captured directly from the live running web client and backend API.

All screenshots were generated from the real browser interface without any fabrication, mockups, synthetic overlays, or AI enhancement. The captured images depict the complete financial evidence investigation workflow: from executive compliance overview and human-in-the-loop field review to 3-way documentary matching, 4-tier finding classification, sealed SHA-256 audit dossier generation, and transparent UGREEN NAS Skill bridge architecture.

---

## 2. Screenshot Manifest & Technical Specifications

| # | File Name | Screen Target | Dimensions | File Size | SHA-256 Checksum |
| :-: | :--- | :--- | :-: | :-: | :--- |
| **01** | `01-vaultpilot-dashboard.png` | **Main Dashboard — Primary Devpost Showcase** | 1920 × 1080 | 283.5 KB | `5552fbc8852c12bcf4af9238ab164d958ea3fafb85317d2cb56d20d27c7ab035` |
| **02** | `02-evidence-review.png` | **Evidence Review & HITL Verification Drawer** | 1920 × 1080 | 230.2 KB | `8bd47d9703375e0c46832d9df987d81dd743d1b32a5eb6af3efea5e2ed95d14e` |
| **03** | `03-evidence-ledger.png` | **Three-Way Evidence Reconciliation Ledger** | 1920 × 1080 | 240.4 KB | `4c5a4a0b3795bcef26a61a5f18063471b066d22b5389d75483a7753f3a9124c2` |
| **04** | `04-investigation-findings.png` | **Four-Tier Classified Findings & Evidential Gaps** | 1920 × 1080 | 186.0 KB | `9db65d41edf93a9d32ac3bc423ab3b72a0d4b39d72f95c0f2247bbc57f509f40` |
| **05** | `05-investigation-report.png` | **Official Audit Dossier & Sealed Snapshot Modal** | 1920 × 1080 | 229.8 KB | `6beaf17d46edab6dae1100726ab6c6a9a7e742155a61c788a655965468fdc482` |
| **06** | `06-ugreen-skill-bridge.png` | **UGREEN NAS Skill Bridge Architecture** | 1920 × 1080 | 194.2 KB | `38f8f390c13709f13ed762c1331b13994cb6edaa05a58f7727014c68f02455c9` |

---

## 3. Screen-by-Screen Quality & Functional Audit

### 1. `01-vaultpilot-dashboard.png` (Main Dashboard — Primary Devpost Showcase)
- **Visual Composition:** Clean 3-column responsive layout with dark navigation sidebar, top executive header, high-contrast hero banner, 4 KPI statistic cards, configured grant scopes, and reconciliation status summary.
- **Key Data Displayed:**
  - Verified Spend: `$8,500 Reconciled` (Strict 3-way documented proof).
  - Confirmed Discrepancy: `1 High Priority` (Direct conflict between PO authorization & invoice).
  - Missing Supporting Evidence: `1 Scope Bounded` (Invoices lacking verified disbursement vouchers).
  - Unverified / Blurry Scan: `1 HITL Review` (Degraded optical scans requiring manual verification).
  - Grant Scopes: *Solar Water Sanitation Initiative* (`PRJ-WASH-2026`, $50,000 USD) and *Rural Mobile Health Clinic* (`PRJ-MED-2026`, $75,000 USD).
  - System Badges: `Live Backend` (green), `Demo Mode` (purple), `NAS: Read-Only` (gray), and `Uliya v0.7.3 EMULATED` (slate).
- **Legibility & Aesthetics:** Zero horizontal overflow, crisp typography, intuitive color-coded status badges, and prominent call-to-action buttons.

### 2. `02-evidence-review.png` (Evidence Review & Human Verification Queue)
- **Visual Composition:** Dual-pane presentation showing the underlying document review queue in the background and the active Human-in-the-Loop (HITL) Evidence Review Drawer open on the right side.
- **Key Data Displayed:**
  - Target Document: `INV-MED-7712.pdf` (Document ID: `#109`, INVOICE, Review in Progress).
  - Cryptographic Seal: SHA-256 `a87ff679a2f3e71d9181a67b7542122ca87ff679a2f3e71d9181a67b7542122c`.
  - Extracted Fields & Audit Actions:
    - **Amount:** Original `14500` $\longrightarrow$ Reviewed / Effective `12000.00` (`CORRECTED` badge).
    - **Currency:** `USD` (`PENDING` badge).
    - **Vendor:** Original `MedSupply Co` $\longrightarrow$ Reviewed: *Excluded from calculations* (`REJECTED` badge).
    - **Date:** `2026-03-01` (`CLARIFICATION` badge).
  - Action Controls: `Verify`, `Correct`, `Reject`, `Clarify` buttons available per field, plus `Re-evaluate Matching` trigger.

### 3. `03-evidence-ledger.png` (3-Way Evidence Reconciliation Ledger)
- **Visual Composition:** Enterprise-grade tabular ledger displaying side-by-side comparative evidence across Purchase Orders, Invoices, and Disbursement Proofs.
- **Key Data Displayed:**
  - 3-Way Cross-Examination Rows:
    - `TXN-14-PO-2026-081`: PO `$8,500.00` == Invoice `$8,500.00` == Receipt `$8,500.00` $\longrightarrow$ `RECONCILED MATCH` (green).
    - `TXN-14-PO-MED-441`: PO `$12,000.00` vs Invoice `$12,000.00` vs Receipt `$14,500.00` $\longrightarrow$ `VARIANCE HOLD` (red, `+$2,500.00 USD` disbursement variance note).
    - `TXN-14-INV-UNSUPP-902`: Missing PO, Invoice `$2,400.00`, Unpaid / No Voucher $\longrightarrow$ `MISSING RECEIPT` (amber).
    - `TXN-14-MISC`: Missing PO, Missing Invoice, Unpaid $\longrightarrow$ `UNVERIFIED` (gray).
  - Filter Controls: Interactive status filter pills (`All (56)`, `Reconciled Match`, `Variance Hold`, `Missing Receipt`, `Unverified`).

### 4. `04-investigation-findings.png` (Four-Tier Classified Findings & Gaps)
- **Visual Composition:** Structured card hierarchy detailing audit observations classified under the conservative 4-tier taxonomy.
- **Key Data Displayed:**
  - **Tier 4 (Optical Degradation / Unverified):** `IMG_7781_blurry.jpg` — Untrusted smudged text, requiring high-resolution scan from field team.
  - **Tier 2 (Potential Anomaly):** `PO-2026-081 vs INV-SP-1092` — Fast billing window (14-day turnaround vs typical 30-day interval). Explicitly notes this is an anomaly indicator, not evidence of misconduct.
  - **Tier 3 (Missing Supporting Evidence):** `INV-UNSUPP-902` — Missing payment voucher ($2,400.00 USD). Explicitly notes that absence of evidence in this folder does not prove payment never occurred.
  - Traceability: Every finding displays `Ref: <filename>` and concrete "Recommended Audit Action".

### 5. `05-investigation-report.png` (Official Audit Dossier & Sealed Snapshot Modal)
- **Visual Composition:** Centered modal dialog showing the completed investigation summary and the cryptographic snapshot registry.
- **Key Data Displayed:**
  - Investigation Details: "E2E Full Financial Evidence Audit" on `/volume1/NGO_Projects/Water_Health_2026` (8 files analyzed, Status: `COMPLETED`, Verified Spend: `$8,500 USD`).
  - Audit Summary: Quantitative breakdown of findings and matching expenditure.
  - Sealed Report Snapshots:
    - `IR-9-V2: Post-Correction Audit Dossier` (Status: `SEALED & VERIFIED`, SHA-256: `1f4234ad252906a52f55b1c15f6774748c57b37a3161e73ede7ad81a352b38b2`).
    - `IR-8-V1: Baseline Investigation Certification Report` (Status: `SEALED & VERIFIED`).
  - Export Options: Direct download buttons for `Printable HTML Dossier` (formatted print layout), `Markdown (.md)`, and `CSV` with schedule selection (`Reconciliation Schedule`, `Findings Schedule`, `Audit Trail Schedule`).

### 6. `06-ugreen-skill-bridge.png` (UGREEN NAS Skill Bridge Architecture)
- **Visual Composition:** Comprehensive architectural dashboard explaining how VaultPilot AI interfaces with the UGREEN UGOS runtime.
- **Key Data Displayed:**
  - Status Badges: `CURRENT STATUS: OFFLINE LOCAL EMULATION` and `STANDARD: ULIYA V0.7.3`.
  - Prominent Transparency Notice: *"Hardware Status: Simulated Local Emulation (`EmulatedNASProvider`) — Physical hardware binding to the UGREEN AI NAS iDX6011 Pro is scheduled for Round 2 finalist validation following official device assignment."*
  - Architectural Guarantees: *Strict Read-Only Fence*, *Fenced Path Traversal* (`/volume1/NGO_Projects/`), and *Declarative Orchestration* (pure Markdown Skill package without unverified scripts).
  - Capability Register: Declarative mappings for `file-agent` (`ug-filesystem.find`), `document-agent` (`ug-document.extract`), and `document-agent` (`ug-document.reconcile`), with honest `Simulated (Round 2 Target)` badges.

---

## 4. Environment & Data Protection Verification

During screenshot generation, strict security safeguards were enforced:
1. **Production Database Protected:** The production database [`backend/vaultpilot.db`](file:///home/osama/VaultPilot-AI/backend/vaultpilot.db) was never opened or modified. All tables retain their baseline counts:
   - `alembic_version: 1`, `projects: 2`, `investigations: 1`, `documents: 8`, `evidence_ledger_entries: 5`, `findings: 4`, `document_field_reviews: 4`, `field_review_history: 5`, `investigation_reports: 0`.
2. **Isolated Demo Environment:** The live application executed against [`backend/demo_vaultpilot.db`](file:///home/osama/VaultPilot-AI/backend/demo_vaultpilot.db) with `UGREEN_NAS_MODE=emulated`.
3. **Skill Package Untouched:** The validated [`dist/vaultpilot-skill.zip`](file:///home/osama/VaultPilot-AI/dist/vaultpilot-skill.zip) archive (`4b002849af79eb3c5d5cb0aa77c9f083480b57250465747a19c4dc997f1dd01f`) was not altered.
4. **Source Evidence Intact:** All sample financial evidence in the demo storage workspace remained strictly read-only.

---

## 5. Devpost Submission Recommendations

### Recommended Primary Showcase / Cover Screenshot
> **Recommended:** `01-vaultpilot-dashboard.png`

**Rationale:**  
The main dashboard serves as the definitive visual anchor for the project submission:
- Immediately conveys the product identity: *"VaultPilot AI — Financial Evidence Intelligence Hub"*.
- Highlights the core hackathon themes: *"UGOS / Uliya Standard v0.7.3 Active"*, *"Zero Cloud Egress Architecture"*, and NAS filesystem path containment.
- Features prominent metric cards ($8,500 verified spend, 1 confirmed discrepancy, 1 missing evidence, 1 unverified scan) that demonstrate practical NGO utility.
- Contains the live backend, demo mode, and read-only status indicators, ensuring compliance with competition integrity rules.

### Recommended Secondary Gallery Sequence
For the Devpost media carousel:
1. **Slide 1:** `01-vaultpilot-dashboard.png` (Main Overview & Financial KPIs)
2. **Slide 2:** `03-evidence-ledger.png` (Core Feature: 3-Way Evidence Matching PO $\longleftrightarrow$ Invoice $\longleftrightarrow$ Receipt)
3. **Slide 3:** `02-evidence-review.png` (Interactive HITL Review Drawer: Field Correction & Audit Trail)
4. **Slide 4:** `04-investigation-findings.png` (Conservative 4-Tier Audit Finding Taxonomy)
5. **Slide 5:** `05-investigation-report.png` (Immutable SHA-256 Sealed Dossiers & Multi-Format Exports)
6. **Slide 6:** `06-ugreen-skill-bridge.png` (Technical Compliance: UGOS Skill Bridge & Emulation Disclosure)

---

## 6. Verification Checklist

- [x] All 6 screenshots captured using headless Google Chrome at native 1920 × 1080 resolution.
- [x] Zero browser developer tools, scrollbars, loading spinners, or clipped dialogs present.
- [x] All screenshots originate from live application rendering with real backend data.
- [x] Local emulation mode clearly communicated in header badges and architectural notes.
- [x] No physical NAS hardware falsely claimed as connected.
- [x] Conservative audit terminology preserved (no unsupported fraud allegations).
- [x] All files verified and stored in [`docs/devpost/screenshots/`](file:///home/osama/VaultPilot-AI/docs/devpost/screenshots/).
