# VaultPilot AI: Intelligent Financial Evidence Investigation for NGOs

VaultPilot AI is a NAS-native financial evidence investigation system designed for NGOs, development organizations, and compliance teams. It helps finance and procurement officers reconstruct the documentary evidence behind project expenditures directly on local UGREEN AI NAS storage.

> **Tagline:** Every transaction needs evidence. Every finding needs a source.

---

## Repository Structure

```
VaultPilot-AI/
├── README.md                      # Root project overview & architecture roadmap
└── vaultpilot/                    # UGREEN NAS Skill Submission Package (v0.7.3 compliant)
    ├── SKILL.md                   # Skill entry point and orchestration workflow
    ├── README.md                  # Skill-specific documentation and mandatory disclosures
    └── references/
        ├── finding-classification.md     # 4-tier finding classification taxonomy
        ├── investigation-methodology.md  # Capability mappings and evidence heuristics
        └── testing-guide.md              # Core test scenarios and edge cases
```

---

## Architectural Separation

In strict adherence to the **UGREEN NAS Skill Hackathon 2026** competition rules:
* **The Skill Package (`vaultpilot/`):** Contains exclusively declarative Markdown orchestration files conforming to the Uliya Skill Development Standard v0.7.3. It contains **no scripts, no executables, no binary runtimes, and no external dependencies**.
* **Future Application Architecture (Post-Hackathon Roadmap):**
  - **Frontend:** React + Vite + Tailwind CSS dashboard for visual evidence graph exploration.
  - **Backend:** Python + FastAPI REST API for external integrations.
  - **Database:** PostgreSQL + SQLAlchemy for metadata caching and audit history.
  *All application layer code is maintained strictly outside the `vaultpilot/` Skill package.*

---

## Key Features of the UGREEN NAS Skill

1. **Evidence Traceability Ledger:** Reconstructs the documentary evidence trail linking Purchase Orders $\longleftrightarrow$ Invoices $\longleftrightarrow$ Payment Proofs $\longleftrightarrow$ Project Expense Reports via rule-guided reasoning.
2. **Strictly Read-Only:** Preserves all original NAS files. Never moves, renames, modifies, or deletes documents.
3. **Conservative Audit Taxonomy:** Classifies findings into *Confirmed Discrepancy*, *Potential Anomaly*, *Missing Evidence*, and *Unverified*. Never makes speculative fraud accusations.
4. **Untrusted Content Fencing:** Treats document text as passive untrusted content to defend against embedded instructions in documents.
5. **Multi-Currency Protection:** Segregates totals by currency group; never silently combines mixed currencies without exchange documentation.

---

## Competition Information
- **Event:** UGREEN Hackathon 2026 on AI NAS: Bring Your Skills to UGOS
- **Track:** Workflow / Innovation
- **Official Skill Identifier:** `vaultpilot`
- **Submission Title:** VaultPilot AI: Intelligent Financial Evidence Investigation for NGOs
