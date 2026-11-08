# VaultPilot AI: Finding Classification Taxonomy

This reference defines the formal audit taxonomy used by VaultPilot AI during financial evidence investigations on UGREEN AI NAS. Every observation is evaluated using rule-guided evidence assessment, not as an autonomous legal, fraud, or deterministic accounting engine.

---

## 1. Classification Principles

1. **Evidence-Based Assessment:** Every finding must be linked directly to identifiable source file paths returned by the system and extracted document values.
2. **Conservative Evaluation:** Ambiguous, unreadable, unavailable, or partial information must never be upgraded to a confirmed violation.
3. **Non-Accusatory Terminology:** VaultPilot AI is a financial evidence investigation assistant, not a judicial authority or autonomous auditor. It never alleges fraud, dishonesty, forgery, or intentional wrongdoing. It reports objective documentation variances and evidential gaps.
4. **Scope-Bounded Findings:** A finding applies solely to the files discovered within the authorized search path.

---

## 2. Four-Tier Finding Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       EVIDENTIAL OBSERVATION                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
[Both Source Records Available]                   [Record Missing or Incomplete]
           │                                                   │
     ┌─────┴─────┐                                       ┌─────┴─────┐
     ▼           ▼                                       ▼           ▼
[Direct      [Plausible /                          [Document    [Corrupted /
 Conflict]   Unusual Pattern]                       Not Found]   Unreadable]
     │           │                                       │           │
     ▼           ▼                                       ▼           ▼
 Tier 1:     Tier 2:                                 Tier 3:     Tier 4:
 Confirmed   Potential                               Missing     Unverified
 Discrepancy Anomaly                                 Evidence
```

### Tier 1: Confirmed Discrepancy
* **Definition:** A direct, irreconcilable inconsistency between two or more discovered, readable source documents where both records provide explicit, contradictory data.
* **Evidential Requirement:** Must cite at least two identifiable source file paths returned by discovery, the exact conflicting fields (e.g., approved amount vs. billed amount), and the exact numerical or textual variance.
* **Standard Examples:**
  - Purchase Order approves a fixed total of \$5,000 USD, but the associated vendor Invoice bills \$6,200 USD for identical item quantities without an amendment document.
  - Project Financial Report lists payment voucher `PV-2026-088` as \$1,400 USD, while the attached official bank receipt indicates an actual disbursement of \$1,100 USD.
* **Reporting Tone:** Objective statement of variance: *"Documented numerical variance of \$1,200 USD observed between PO-102 (\$5,000 USD) and INV-404 (\$6,200 USD)."*

### Tier 2: Potential Anomaly
* **Definition:** An unusual pattern, sequence, or grouping that deviates from typical administrative procedure but does not constitute a direct textual or numerical contradiction between verified records.
* **Evidential Requirement:** Must cite the observed pattern, the relevant returned file paths, and explain why human verification is warranted.
* **Standard Examples:**
  - **Unusual Date Sequences:** An invoice date precedes the purchase order date by several weeks, or a receipt payment timestamp occurs prior to the invoice date. *(Note: Legitimate business reasons exist, such as emergency procurement, retroactive PO issuance, or advance retainer payments; human verification is required).*
  - **Duplicate-Looking Records:** Two separate invoices from the same supplier bear identical monetary amounts and line descriptions within a 48-hour window, but carry different invoice reference numbers.
  - **Mismatched Organizational / Vendor Naming:** The supplier name on the invoice differs slightly from the payee name on the bank remittance receipt (e.g., parent company vs. operating subsidiary).
* **Reporting Tone:** Neutral advisory: *"Unusual chronology observed: Receipt payment date (12-Jan-2026) precedes Purchase Order authorization date (28-Jan-2026). Verify whether this represents an advance retainer or emergency procurement."*

### Tier 3: Missing Evidence
* **Definition:** A necessary supporting document or verification record was not discovered within the explicitly searched directory scope.
* **Evidential Boundary:** **Critical Distinction:** Stating that a document is "Missing Evidence" establishes only that the file was absent from the searched NAS folder. It does **not** prove or imply that the transaction was unauthorized, that goods were not received, or that payment never occurred.
* **Standard Examples:**
  - A project financial report records an expenditure of \$3,500 USD for field vehicle rental, but no corresponding vendor invoice or rental agreement was discovered in the scoped folder.
  - An invoice exists for \$800 USD with terms marked "Paid", but no payment receipt, bank slip, or cash voucher was discovered.
  - A vendor invoice references `PO-2026-044`, but no matching purchase order document is present in the directory.
* **Reporting Tone:** Clear scope limitation: *"No supporting receipt was discovered within the searched folder scope `/volume1/NGO_Projects/Education_2026` for Invoice `INV-902`. Recommend confirming whether records are filed in an alternate repository."*

### Tier 4: Unverified
* **Definition:** The available document or record is insufficient to establish verified facts due to technical, extraction, formatting, or clarity limitations.
* **Evidential Boundary:** Applied whenever extraction yields unavailable fields, unreadable text, or non-comparable currencies without exchange documentation.
* **Standard Examples:**
  - **Low-Resolution / Smeared Scans:** An image or scanned receipt cannot be reliably parsed by `ug-document.extract`.
  - **Unavailable Fields:** Fields omitted by the document or unsupported by the schema (not assumed to be null).
  - **Incompatible Multi-Currency Formats:** Records list values in different, non-comparable currencies without exchange documentation (e.g., local currency cash voucher vs. USD grant budget) where offline evaluation cannot verify equivalency without guessing rates.
* **Reporting Tone:** Transparent technical limitation: *"Payment receipt `IMG_3042.jpg` could not be reliably extracted due to low image clarity/smudged printing. The transaction amount remains Unverified pending manual document inspection."*

---

## 3. Classification Decision Matrix

| Observed Condition | Extracted Evidence Quality | Appropriate Classification | Prohibited Action |
| :--- | :--- | :--- | :--- |
| Discovered PO: \$1,000; Discovered Invoice: \$1,500 | High (both values readable & explicit) | **Confirmed Discrepancy** | Never allege intentional overbilling. |
| Invoice date earlier than PO approval date | High (both dates explicit) | **Potential Anomaly** | Never assume the transaction is invalid. |
| Two identical invoice amounts from same vendor | High | **Potential Anomaly** | Never claim duplicate fraud. |
| Invoice exists, payment receipt not found | Scope-bounded | **Missing Evidence** | Never claim payment was never made. |
| Receipt image blurry, amount unreadable | Low / Extraction Failed | **Unverified** | Never guess or interpolate numbers. |
| Invoices in EUR, Project report in USD, no FX slip | Medium | **Unverified** (Currency Conflict) | Never calculate totals across mixed currencies. |

---

## 4. Reporting Standards for Findings

For every finding presented in the final investigation report, the Skill formats the entry using the following structure:

1. **Classification:** [Confirmed Discrepancy | Potential Anomaly | Missing Evidence | Unverified]
2. **Subject Item / Transaction Reference:** [e.g., Medical Supplies Batch 3]
3. **Source Paths:** Exact relative file paths returned by discovery (e.g., `invoices/INV-102.pdf`, `orders/PO-088.pdf`).
4. **Expected Value / Record:** [e.g., PO Authorization: \$4,000.00 USD]
5. **Observed Value / Record:** [e.g., Invoiced Amount: \$4,750.00 USD]
6. **Detailed Explanation:** Factual description of the variance or gap without speculative language.
7. **Recommended Human Action:** Specific verification step for the finance or procurement officer.
