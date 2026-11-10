# VaultPilot AI: Submission Disclosures & Architectural Specifications

This reference document details the official hackathon submission disclosures, architectural boundaries, and operational safeguards for VaultPilot AI under the UGREEN UGOS / Uliya Skill Development Standard (v0.7.3).

---

## 1. Project Overview & Scope

Non-governmental organizations (NGOs) and international development agencies manage grant-funded expenditures across diverse financial records: purchase orders, commercial vendor invoices, payment receipts, and periodic financial reports. Reconciling these records across networked storage shares is challenging, prone to clerical oversight, and susceptible to unverified claims.

**VaultPilot AI** is a NAS-native financial evidence investigation Skill designed for UGREEN AI NAS. It discovers authorized financial documents, extracts structured transaction metadata, cross-examines evidence chains using rule-guided reasoning, and delivers transparent investigation reports citing traceable source paths without modifying, moving, or deleting original files on storage shares.

---

## 2. Mandatory Hackathon Disclosures

### Third-Party Components & Licenses
- **Specification Basis:** Built in compliance with the Uliya Skill Development Standard (v0.7.3) and the Agent Skills specification.
- **Embedded Dependencies:** Contains zero embedded third-party npm packages, Python wheels, binary libraries, external API wrappers, or compiled executables within the Skill package.
- **Application Layer Separation:** The companion demonstration web interface (FastAPI backend and React frontend) is maintained separately outside the Skill distribution archive in accordance with hackathon guidelines.

### Principal Functionality Developed for this Hackathon
- **Evidence Traceability Ledger:** A declarative orchestration workflow that preserves bidirectional links between transaction claims and returned filesystem paths.
- **4-Tier Finding Classification Taxonomy:** A conservative audit classification scheme tailored for NGO compliance (Confirmed Discrepancy, Potential Anomaly, Missing Evidence, Unverified Record).
- **Multi-Document Cross-Examination:** Cross-verifying financial relationships between Purchase Orders, Invoices, Payment Receipts, and Bank Slips.
- **Untrusted Document Defense:** Treating all extracted document text and sidecar metadata as passive, untrusted input.

### Generative AI Tools Used
- Generative AI coding assistants were utilized during project development for architectural drafting, capability schema mapping, prompt refinement, and edge-case testing design.

### Physical Hardware & Runtime Testing Status
- **Static Skill Validation:** Fully verified and certified via the official Uliya Skill static validator (`check-skill.mjs` v2.0.0) with zero errors and zero warnings.
- **Backend Envelope Validation:** The backend implements strict Pydantic envelope validators (`UliyaResponseEnvelope`, `FindCapabilityData`, `ExtractedDocumentData`, `ReconcileCapabilityData`) handling all 5 delegation states.
- **Local Emulation:** Offline demonstration and automated test suites operate via the isolated `EmulatedNASProvider` and `LocalDevStorageProvider`.
- **Live Physical NAS & Uliya Daemon Testing Notice:** Live invocation of the Uliya runtime daemon process on genuine UGOS Pro hardware (`iDX6011 Pro`) is scheduled for the official physical NAS testing window (November 22–28, 2026). No claim of prior physical daemon execution is made.

---

## 3. Package File Structure Compliance

Under the official Uliya Skill Development Standard:
- The package root contains exclusively `SKILL.md` and the `references/` directory.
- `SKILL.md` acts as the primary declarative entry point.
- All supplementary documentation, methodologies, and disclosures reside within `references/*.md` and are linked directly from `SKILL.md`.
- No `README.md`, manifest files, or extraneous root-level files are included in the distributable archive to ensure complete validator compliance.
