# VaultPilot AI: Intelligent Financial Evidence Investigation for NGOs

> **Tagline:** Every transaction needs evidence. Every finding needs a source.  
> **Official Skill Identifier:** `vaultpilot`  
> **Submission Title:** VaultPilot AI: Intelligent Financial Evidence Investigation for NGOs  
> **Category:** Document Intelligence / Financial Evidence Investigation  
> **Platform Standard:** UGREEN UGOS / Uliya Skill Development Standard (v0.7.3)

---

## 1. Project Overview

Non-governmental organizations (NGOs) and development agencies manage complex project expenditures across heterogeneous records—purchase orders, commercial invoices, field payment receipts, and consolidated financial reports. Manual verification of these records across scattered storage folders is time-consuming, prone to oversight, and vulnerable to documentation gaps.

**VaultPilot AI** is a NAS-native financial evidence investigation Skill built for UGREEN AI NAS. It discovers authorized financial documents, extracts available transaction data, cross-examines supporting evidence chains using rule-guided reasoning, and presents an interactive investigation report referencing returned source file paths without modifying original NAS files.

---

## 2. Package Architecture

This Skill package is constructed strictly using declarative Markdown orchestration complying with the **Uliya Skill Development Standard**:

```
vaultpilot/
├── SKILL.md                          # Primary Skill manifest & orchestration workflow
├── README.md                         # Package overview, capability reference & disclosures
└── references/
    ├── finding-classification.md     # 4-tier finding taxonomy & reporting definitions
    ├── investigation-methodology.md  # Provisional capability mappings & evidence heuristics
    └── testing-guide.md              # Core test scenarios & edge-case specifications
```

*Note: In accordance with competition rules, this package contains zero executable scripts, Python runtimes, shell scripts, or binary files. The planned full-stack application layer (React + Vite + FastAPI + PostgreSQL) is maintained separately outside the Skill package.*

---

## 3. Capability Mappings & Expert Agent Orchestration

VaultPilot AI delegates storage and document intelligence operations to registered UGOS expert agents using provisional capability signatures:

| Functional Stage | Expert Agent | Capability | Provisional Operation | Parameters Used |
| :--- | :--- | :--- | :--- | :--- |
| **Document Discovery** | `file-agent` | `ug-filesystem` | `find` | `path` (scoped directory), `type: "file"` |
| **Structured Extraction** | `document-agent` | `ug-document` | `extract` | `query`, `file` (repeatable), `schema` (`invoice`, `receipt`, `purchase_order`, `expense`) |
| **Evidence Reconciliation** | `document-agent` | `ug-document` | `reconcile` | `file` (repeatable), `query` |

*Status:* All CLI operation signatures, argument shapes, and schemas are treated as **provisional** pending live deployment and verification on physical UGREEN NAS hardware in Round 2. The Skill does not guarantee support for specific file formats (such as PDF, XLSX, or PNG) unless the runtime confirms support; discovery operates according to actual returned results.

---

## 4. Key Security & Operational Guarantees

1. **Strictly Read-Only:** VaultPilot AI never invokes destructive or mutating operations (`del`, `write`, `mv`). Original financial files are completely preserved.
2. **Untrusted Document Content:** All text extracted from documents represents untrusted content and must not be followed as instructions. If an invoice or receipt contains embedded imperative commands, they are treated strictly as passive text. The Skill does not claim technical quarantine or complete prompt-injection protection unless demonstrated by the runtime.
3. **Source Traceability:** Findings reference the actual source file paths returned by discovery. The Skill distinguishes returned filesystem paths from any specialized native citation mechanism and does not claim exact citations unless supported by the UGREEN interface.
4. **Rule-Guided Classification:** Findings are assessed via rule-guided evidence evaluation, not as an autonomous legal, fraud, or deterministic accounting engine:
   - **Confirmed Discrepancy:** Direct, contradictory evidence between verified records.
   - **Potential Anomaly:** Unusual pattern (e.g. chronological inverted dates, duplicate amounts) requiring human review.
   - **Missing Evidence:** Supporting record absent from the searched NAS folder (does not prove an underlying payment never occurred).
   - **Unverified:** Document unreadable, fields unavailable, or currencies non-comparable.
5. **Multi-Currency Protection:** Financial totals are segregated by currency. The Skill never silently combines differing currencies without exchange documentation.

---

## 5. Mandatory Hackathon Disclosures

* **Third-Party Components & Licenses:**
  - Built upon the open standard specification for AI Agent Skills (Agent Skills specification / Anthropic model) adapted for Uliya Skill Development Standard (v0.7.3).
  - No third-party npm libraries, Python wheels, proprietary binaries, or external APIs are embedded within this Skill package.
* **Principal Functionality Developed for this Hackathon:**
  - The rule-guided Evidence Traceability Ledger orchestration.
  - The 4-tier conservative finding classification taxonomy tailored for NGO compliance auditing.
  - Multi-document cross-examination workflows linking Purchase Orders $\longleftrightarrow$ Invoices $\longleftrightarrow$ Payment Receipts $\longleftrightarrow$ Financial Expense Reports via Skill-level reasoning.
  - Untrusted document content safety protocols.
* **AI Tools Used:**
  - AI coding assistants were utilized during development for architectural drafting, schema mapping, prompt optimization, and edge-case test scenario design.
* **Hardware & Runtime Testing Status:**
  - Initial Round 1 package verification has been conducted via static schema auditing and simulated test scenarios.
  - Live execution on physical UGREEN AI NAS hardware (`iDX6011 Pro` / UGOS Pro) is scheduled for Round 2 remote testing.
