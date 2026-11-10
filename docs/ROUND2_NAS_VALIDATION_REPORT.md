# VaultPilot AI — Round 2 Hardware Validation Report & Benchmark Protocol

**Device Under Test:** UGREEN AI NAS `iDX6011 Pro`  
**OS Version:** UGOS Pro  
**Validation Standard:** UGREEN UGOS / Uliya Skill Development Standard (v0.7.3)  
**Status:** Template & Execution Protocol (To be filled during live Round 2 testing)

---

## 1. Executive Summary of Hardware Testing
- **Testing Date:** [To be completed upon access]
- **Hardware Serial / Environment ID:** [Assigned remote node ID]
- **Tester / Team:** VaultPilot AI Team
- **Overall Result:** [Pending Remote Deployment]

---

## 2. CLI Capability Interface Verification

| Expert Agent | Capability | Provisional Operation | Actual Hardware Command / Signature | Verified Status |
| :--- | :--- | :--- | :--- | :---: |
| `file-agent` | `ug-filesystem` | `find` (`path`, `type`) | `[To be verified on live hardware]` | PENDING |
| `document-agent`| `ug-document` | `extract` (`query`, `file`, `schema`) | `[To be verified on live hardware]` | PENDING |
| `document-agent`| `ug-document` | `reconcile` (`file`, `query`) | `[To be verified on live hardware]` | PENDING |

---

## 3. Core Test Case Validation Results

### Test Case 1: Baseline 3-Way Reconciled Match
- **Input Scope:** `/volume1/Test_Projects/Solar_Water_2026/`
- **Files:** `PO-2026-081.pdf` (\$8,500), `INV-SP-1092.pdf` (\$8,500), `REC-BNK-993.pdf` (\$8,500)
- **Observed Behavior:**
  - Filesystem discovery returned 3 paths: [YES / NO]
  - Entity extraction latency: [X.XX seconds]
  - Reconciled status: `RECONCILED_MATCH` [YES / NO]
  - Verified spend credited: \$8,500.00 USD [YES / NO]

### Test Case 2: Documented Billing Inconsistency & Human Correction
- **Input Scope:** `/volume1/Test_Projects/Clinic_Rehab/`
- **Files:** `PO-MED-441.pdf` (\$12,000), `INV-MED-7712.pdf` (\$14,500), `VOUCH-331.pdf` (\$14,500)
- **Observed Behavior:**
  - Overbilling discrepancy flagged as `CONFIRMED_DISCREPANCY`: [YES / NO]
  - Human review correction of billed amount to \$12,000 USD applied: [YES / NO]
  - Re-reconciliation clears discrepancy and credits \$12,000 USD: [YES / NO]
  - Original value preserved in ledger breakdown: [YES / NO]

### Test Case 3: Missing Supporting Record
- **Input Scope:** `/volume1/Test_Projects/Field_Survey/`
- **Files:** `INV-UNSUPP-902.pdf` (\$2,400) without PO or receipt
- **Observed Behavior:**
  - Finding classified as `MISSING_EVIDENCE`: [YES / NO]
  - Verified spend strictly remains \$0.00 USD: [YES / NO]

### Test Case 4: Degraded Scanned Receipt (Fail-Closed)
- **Input Scope:** `/volume1/Test_Projects/Degraded_Scan/`
- **Files:** `IMG_7781_blurry.jpg`
- **Observed Behavior:**
  - Finding classified as `UNVERIFIED`: [YES / NO]
  - Zero numerical hallucination (amount remains None): [YES / NO]
  - Verified spend strictly remains \$0.00 USD: [YES / NO]

---

## 4. Storage Security & Boundary Benchmarks

| Security Metric | Expected Behavior | Observed Result on Hardware |
| :--- | :--- | :---: |
| **Path Traversal (`../`)** | Explicit rejection with access denial | [Pass / Fail] |
| **Symlink Escape** | Blocked canonical resolution | [Pass / Fail] |
| **Read-Only Preservation** | Source file mtime and hash unchanged | [Pass / Fail] |
| **Large File Streaming** | Memory consumption stable under 64KB blocks | [Pass / Fail] |

---

## 5. Performance & Resource Consumption Log
- **CPU Utilization during extraction:** [XX%]
- **Memory Footprint (Peak):** [XXX MB]
- **Average Scan Latency per 10 documents:** [X.XX seconds]
- **Storage I/O Read Throughput:** [XX MB/s]
