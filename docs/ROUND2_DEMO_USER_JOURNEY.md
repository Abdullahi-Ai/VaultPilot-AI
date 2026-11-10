# VaultPilot AI — Round 2 Demo User Journey & Experience Architecture

**Document Status:** Official UX & Product Demonstration Guide  
**Author:** UX Engineer & Hackathon Competition Strategist  
**Date:** November 10, 2026  
**Repository:** `/home/osama/VaultPilot-AI`  
**User Focus:** NGO Compliance Auditors, Procurement Managers, Donors & Hackathon Judges

---

## 1. The 60-Second Hackathon Judge Hook

Within the first 60 seconds of interacting with VaultPilot AI, a hackathon judge or compliance officer immediately understands three things:

1. **What it does:** Automates the tedious, error-prone manual verification of grant expenditures across scattered NAS documents.
2. **How it is unique:** It uses deterministic 3-way matching (PO $\longleftrightarrow$ Invoice $\longleftrightarrow$ Receipt) and conservative legal auditing rules—never hallucinating financial figures.
3. **Why it belongs on UGREEN NAS:** It operates locally with zero cloud egress, strict read-only storage sandboxing, and immutable SHA-256 cryptographic report sealing.

---

## 2. Target Personas & Core Value Propositions

| Persona | Core Pain Point | VaultPilot AI Solution |
| :--- | :--- | :--- |
| **NGO Auditor (Elena Vance)** | Manually opening 500+ PDFs/scans to verify if invoices match approved purchase orders before donor reporting deadlines. | Instant 3-way reconciliation ledger flagging exact dollar variances and missing vouchers in seconds. |
| **Procurement Officer (Marcus)** | Inadvertent vendor overbilling or duplicate billing slipping through unverified field disbursements. | Automatic detection of invoice amounts exceeding authorized PO lines (`CONFIRMED_DISCREPANCY`). |
| **Grant Project Manager (Amina)** | Risk of false fraud accusations when local field receipts are temporarily delayed in transit. | Clear distinction between `MISSING_EVIDENCE` and confirmed fraud, preventing reputational damage. |
| **Hackathon Judge** | AI projects that hallucinate numbers, make fake hardware claims, or act as simple wrappers around cloud LLMs. | Fully local, explainable, deterministically audited platform with genuine Uliya Skill compliance and verifiable seals. |

---

## 3. The 6-Stage Guided Investigation Journey

```mermaid
graph LR
    S1["1. Select Scope"] --> S2["2. Discover Files"]
    S2 --> S3["3. Extract Data"]
    S3 --> S4["4. Reconcile Records"]
    S4 --> S5["5. Human Review"]
    S5 --> S6["6. Seal & Export"]

    style S1 fill:#0284c7,stroke:#0369a1,color:#fff
    style S2 fill:#0284c7,stroke:#0369a1,color:#fff
    style S3 fill:#0284c7,stroke:#0369a1,color:#fff
    style S4 fill:#0284c7,stroke:#0369a1,color:#fff
    style S5 fill:#10b981,stroke:#059669,color:#fff
    style S6 fill:#6366f1,stroke:#4f46e5,color:#fff
```

### Stage 1: Select Investigation Scope
- **User Action:** Auditor opens the VaultPilot dashboard, views active grant projects (e.g. *Solar Water & Medical Clinic Aid*), and clicks **Launch Investigation**.
- **System Response:** Verifies the authorized NAS scope path (`/volume1/NGO_Projects/Water_Health_2026`). Ensures path containment within the authorized root.

### Stage 2: Discover Evidence (`file-agent`)
- **User Action:** Auditor monitors live discovery progress.
- **System Response:** `file-agent` scans the scoped NAS directory in read-only mode, discovering 8 financial documents (3 POs, 3 Invoices, 2 Receipts) and computing streaming SHA-256 digests.

### Stage 3: Extract Structured Information (`document-agent`)
- **User Action:** Auditor reviews parsed document cards with extraction confidence badges.
- **System Response:** `document-agent` parses dates, currencies, line items, and vendor details from PDFs and CSVs without hallucination. Degraded scans (`IMG_7781_blurry.jpg`) fail-close to `UNVERIFIED`.

### Stage 4: Reconcile Records (Deterministic 3-Way Engine)
- **User Action:** Auditor navigates to the **3-Way Evidence Ledger**.
- **System Response:** The engine matches POs to Invoices to Payment Receipts:
  - Clean Match: `PO-2026-081` ($8.5k) == `INV-SP-1092` ($8.5k) == `REC-BNK-993` ($8.5k) $\longrightarrow$ `RECONCILED MATCH`.
  - Overbilling Variance: `PO-MED-441` ($12k) vs `INV-MED-7712` ($14.5k) $\longrightarrow$ `VARIANCE HOLD` (+$2,500.00 USD).
  - Missing Disbursement: `INV-UNSUPP-902` ($2.4k) lacking payment slip $\longrightarrow$ `MISSING RECEIPT`.

### Stage 5: Human-in-the-Loop Review & Field Correction
- **User Action:** Auditor opens the **Evidence Review Drawer** for `INV-MED-7712.pdf`.
  - Reads vendor Credit Memo `CM-01` explaining the $2,500 discount for delayed delivery.
  - Clicks **Correct Field**, inputs `$12,000.00 USD`, notes Credit Memo reference, and submits.
- **System Response:** System cryptographically signs the action with HMAC-SHA256, appends an immutable audit log entry, and automatically re-evaluates the ledger. The overbilling hold clears!

### Stage 6: Seal & Export Cryptographic Audit Dossier
- **User Action:** Auditor opens the **Official Audit Dossier Modal** and clicks **Seal New Audit Snapshot**.
- **System Response:** Sealer computes SHA-256 snapshot hash `1f4234ad...`, stamps report `IR-9-V2: Post-Correction Audit Dossier`, and provides instant downloads for:
  - Printable HTML Dossier (print-ready styling for donor packages).
  - Standalone Markdown (`.md`).
  - Audited CSVs (Reconciliation, Findings, and Audit Trail schedules).
