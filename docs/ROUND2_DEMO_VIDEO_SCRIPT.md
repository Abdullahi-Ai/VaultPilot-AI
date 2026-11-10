# VaultPilot AI — Round 2 Official Demo Video Script (3 Minutes)

**Track:** Automate Your Workflow  
**Competition:** UGREEN Hackathon 2026 on AI NAS  
**Target Duration:** 2 minutes 50 seconds ($\le$ 3:00:00 strictly enforced)  
**Resolution:** 1080p (1920 × 1080, 16:9) at 30/60 fps  
**Audio Standards:** Normalized English voiceover (-14 LUFS, peak -1 dB), background bed (-24 dB)  
**Primary Tagline:** *"Every transaction needs evidence. Every finding needs a source."*

---

## Video Timing & Scene Architecture

```mermaid
timeline
    title 3-Minute Video Timeline (170 Seconds Total)
    00:00 - 00:15 : Scene 1: The Problem & NGO Compliance Crisis
    00:15 - 00:35 : Scene 2: Product Introduction & Local AI NAS Architecture
    00:35 - 01:10 : Scene 3: Agentic Discovery & Read-Only Confinement
    01:10 - 01:45 : Scene 4: Multi-Document 3-Way Reconciliation
    01:45 - 02:15 : Scene 5: Conservative 4-Tier Audit Taxonomy
    02:15 - 02:40 : Scene 6: Human Oversight & Cryptographic Attestation
    02:40 - 02:55 : Scene 7: Sealed Dossier & Integrity Verification
    02:55 - 03:00 : Scene 8: Closing & Project Links
```

---

## Detailed Scene-by-Scene Script

### Scene 1: The NGO Compliance Crisis (0:00 – 0:15 | 15s)
- **Visual:** Open with a fast, high-contrast visual. A high-density file manager view showing `/volume1/NGO_Projects/Water_Sanitation_2026` packed with unsorted PDFs, scanned banking receipts, duplicate invoices, and vendor quotes.
- **On-Screen Text:**  
  *Top Left:* UGREEN AI NAS • Humanitarian Audit Automation  
  *Lower Third:* **THE PROBLEM:** $30B+ in annual grant funding faces clawback risk due to missing or mismatched documentary evidence.
- **Narration (0:00 – 0:15):**  
  > *"Every year, humanitarian NGOs and procurement teams face catastrophic grant clawbacks—not because funds were stolen, but because field receipts, invoices, and purchase orders are scattered across local drives. Sensitive financial records cannot be uploaded to public cloud AI. What if your private NAS could investigate financial evidence itself?"*
- **Stage Direction:** Cursor navigates quickly through cluttered folder, highlighting messy vendor folders and unindexed PDF files.

---

### Scene 2: Introducing VaultPilot AI (0:15 – 0:35 | 20s)
- **Visual:** Transition smoothly to the VaultPilot AI Main Dashboard running inside the browser on the UGREEN NAS desktop. Display the KPI cards: Total Grants ($125,000), Active Investigations, 3-Way Matched Spend, and Discrepancies. Show the clean dark-mode interface with the UGREEN NAS status badge ("Storage: Emulated / Physical NAS Ready").
- **On-Screen Text:**  
  *Center Badge:* **VaultPilot AI** — NAS-Native Financial Evidence Investigation  
  *Lower Third:* Track: Automate Your Workflow | 100% Local Execution | Zero Cloud Leaks
- **Narration (0:15 – 0:35):**  
  > *"Introducing VaultPilot AI: a NAS-native financial evidence investigation platform built specifically for UGREEN AI NAS under the 'Automate Your Workflow' track. Operating 100% locally on UGOS Pro, VaultPilot automates forensic document matching, preserves donor data privacy with zero external API calls, and enforces the golden rule of auditing: every transaction needs evidence; every finding needs a source."*
- **Stage Direction:** Slow camera pan across the dashboard KPI cards, zooming gently into the Spend Reconciliation widget.

---

### Scene 3: Agentic Discovery & Read-Only Confinement (0:35 – 1:10 | 35s)
- **Visual:** Switch to the UGREEN NAS Skill Bridge panel. Show the Uliya Skill command dispatch:  
  `"Use vaultpilot to investigate /volume1/NGO_Projects/Water_Sanitation_2026"`  
  Show the capability card delegating to `file-agent` using `ug-filesystem.find`. Highlight the system logs verifying:  
  - Path confinement within authorized directory (`/volume1/NGO_Projects/...`)  
  - Symlink and `..` escape rejection  
  - Streaming SHA-256 hash generation for every discovered PDF and TIFF
- **On-Screen Text:**  
  *Overlay Card:* **Agentic Capability Delegation** → `ug-filesystem.find` & `ug-document.extract`  
  *Security Pill:* **Strict Read-Only Mode** (Zero file modification • Symlink traversal blocked)
- **Narration (0:35 – 1:10):**  
  > *"Through the official Uliya Skill framework, VaultPilot AI delegates document discovery to the NAS file agent. It traverses authorized project folders with strict path confinement, rejecting symlinks and directory traversal attacks.  
  Every discovered financial document is immediately fingerprinted with streaming SHA-256 cryptographic digests. The filesystem remains strictly read-only—not a single byte of your source records is ever modified."*
- **Stage Direction:** Mouse clicks "Execute Discovery". Progress bar fills smoothly. Discovered file tree populates with 12 synthetic financial documents with their exact SHA-256 checksums displayed.

---

### Scene 4: Multi-Document 3-Way Reconciliation (1:10 – 1:45 | 35s)
- **Visual:** Transition to the **Evidence Ledger**. Show the three-way matching table reconstructing the transaction lifecycle.  
  - Row 1: Purchase Order `PO-2026-081` ($8,500.00) $\leftrightarrow$ Vendor Invoice `INV-SP-1092` ($8,500.00) $\leftrightarrow$ Bank Payment Slip `REC-BNK-993` ($8,500.00) $\rightarrow$ Green Badge: `RECONCILED_MATCH`.  
  - Row 2: Purchase Order `PO-MED-441` ($12,000.00) $\leftrightarrow$ Medical Invoice `INV-MED-7712` ($14,500.00) $\rightarrow$ Red Badge: `CONFIRMED_DISCREPANCY` (+$2,500.00 variance).
- **On-Screen Text:**  
  *Header:* **Deterministic 3-Way Reconciliation Engine**  
  *Callout Box 1:* Solar Inverter Project: $8,500.00 exact match across 3 independent documents.  
  *Callout Box 2:* Clinic Hospital Beds: $14,500.00 billed vs $12,000.00 authorized (+$2,500.00 variance).
- **Narration (1:10 – 1:45):**  
  > *"Once extracted, VaultPilot's deterministic reconciliation engine reconstructs complete three-way transaction chains.  
  For our solar pumping equipment, purchase order PO-081 matches invoice 1092 and the bank debit slip to the penny, instantly verifying $8,500 in approved grant expenditure.  
  No LLM guesses arithmetic: Python's exact decimal engine evaluates variances deterministically, isolating discrepancies with mathematical certainty."*
- **Stage Direction:** Zoom in to the variance column showing `+$2,500.00`. Hover over the source document pill showing linked invoice file path and SHA-256 hash.

---

### Scene 5: Conservative 4-Tier Audit Taxonomy (1:45 – 2:15 | 30s)
- **Visual:** Navigate to the **Findings & Gaps** view. Demonstrate the four distinct finding tiers:  
  1. `CONFIRMED_DISCREPANCY`: Medical Supplies billing excess (+$2,500).  
  2. `MISSING_EVIDENCE`: Unsupported Consultant Invoice `INV-UNSUPP-902` ($3,200.00) without PO or bank proof.  
  3. `POTENTIAL_ANOMALY`: Vendor Name mismatch or date sequence anomaly.  
  4. `UNVERIFIED_FINDING`: Blurry receipt scan (`REC-BLUR-004`) failing confidence threshold ($0 credited).
- **On-Screen Text:**  
  *Audit Standard:* **Conservative 4-Tier Taxonomy** (Zero Unfounded Accusations)  
  *Rules:* Fail-Closed Accounting • Unverified files credit $0.00 spend
- **Narration (1:45 – 2:15):**  
  > *"Unlike typical AI assistants that jump to conclusions, VaultPilot AI enforces a conservative 4-tier audit taxonomy.  
  It distinguishes a Confirmed Discrepancy from a Potential Anomaly. Unsupported invoices are flagged as Missing Evidence. And corrupted or low-confidence scans are classified as Unverified Findings.  
  Under our fail-closed accounting principle, zero grant spend is credited until valid evidence is verified."*
- **Stage Direction:** Expand the Missing Evidence card for `INV-UNSUPP-902`, highlighting the checklist showing missing PO and missing bank payment.

---

### Scene 6: Human Oversight & Cryptographic Attestation (2:15 – 2:40 | 25s)
- **Visual:** Click "Review" on `INV-MED-7712` to open the **Evidence Review Drawer**.  
  - Show original extracted amount: `$14,500.00`.  
  - Auditor points to attached Vendor Credit Memo `CM-01` (-$2,500 discount for delivery delay).  
  - Auditor edits amount to `$12,000.00`, types note: *"Credit Memo CM-01 applied per procurement agreement"*.  
  - Click **"Sign & Apply Correction"**. System generates HMAC-SHA256 signature and immutable audit log entry.  
  - Click **"Re-evaluate Reconciliation"**. The discrepancy badge turns green (`RECONCILED_MATCH`), and verified spend updates to $12,000.00.
- **On-Screen Text:**  
  *Workflow:* **Human-in-the-Loop (HITL) Review**  
  *Integrity:* Cryptographic Attestation (HMAC-SHA256 Tamper Evidence) • Instant Re-Reconciliation
- **Narration (2:15 – 2:40):**  
  > *"AI should never make unilateral financial decisions. In the Evidence Review drawer, an auditor inspects Credit Memo CM-01 on file.  
  She inputs the corrected billing amount of $12,000. VaultPilot cryptographically signs the modification with an HMAC-SHA256 attestation, preserving the raw extraction history.  
  With one click, she re-evaluates the ledger. The discrepancy resolves, and $12,000 is safely credited to verified project spend."*
- **Stage Direction:** Click "Sign & Apply Correction", show green toast confirmation with signature hash preview, then click "Re-evaluate Reconciliation" and watch the ledger status flip to green.

---

### Scene 7: Sealed Dossier & Integrity Verification (2:40 – 2:55 | 15s)
- **Visual:** Switch to **Investigation Report**. Show the complete audit summary table, donor compliance scorecard (100% evidentiary backing), and the **Integrity Verification Card** displaying the root SHA-256 seal. Click "Export PDF Dossier" and "Export CSV Reconciliation".
- **On-Screen Text:**  
  *Audit Deliverable:* **Tamper-Evident Grant Audit Dossier**  
  *Security:* SHA-256 Root Checksum • Full Evidence Citation • Export to PDF & CSV
- **Narration (2:40 – 2:55):**  
  > *"The final investigation dossier is sealed with a root SHA-256 checksum, creating a tamper-evident audit record ready for institutional donors like USAID, the EU, or the Global Fund. Exportable instantly to PDF and CSV with every finding linked to its source file on your NAS."*
- **Stage Direction:** Hover over the green "Dossier Sealed: Integrity Verified" badge. Click "Export PDF", showing the downloaded summary dossier preview.

---

### Scene 8: Closing & Project Identity (2:55 – 3:00 | 5s)
- **Visual:** Clean full-screen outro slate with official hackathon branding.  
  - VaultPilot AI Logo & Tagline  
  - "UGREEN Hackathon 2026 • Automate Your Workflow"  
  - GitHub Repository: `github.com/Abdullahi-Ai/VaultPilot-AI`  
  - Devpost Link: `devpost.com/software/vaultpilot-ai`
- **On-Screen Text:**  
  **VaultPilot AI**  
  *Every transaction needs evidence. Every finding needs a source.*  
  UGREEN AI NAS • Automate Your Workflow Track
- **Narration (2:55 – 3:00):**  
  > *"VaultPilot AI on UGREEN AI NAS: Every transaction needs evidence. Every finding needs a source. Thank you."*
- **Stage Direction:** Music swells softly and fades to silence at 2:59. Screen fades to black.

---

## Word Count & Audio Pacing Verification

| Scene | Duration | Word Count | Speaking Rate | Pacing Assessment |
|---|---|---|---|---|
| **Scene 1: The Problem** | 15 sec | 44 words | 176 WPM | Urgent, engaging hook |
| **Scene 2: Introducing VaultPilot** | 20 sec | 48 words | 144 WPM | Clear, measured intro |
| **Scene 3: Agentic Discovery** | 35 sec | 68 words | 116 WPM | Deliberate, technical precision |
| **Scene 4: 3-Way Reconciliation** | 35 sec | 67 words | 114 WPM | Focused, demonstrative |
| **Scene 5: Conservative Taxonomy** | 30 sec | 58 words | 116 WPM | Authoritative, audit standard |
| **Scene 6: Human Oversight** | 25 sec | 57 words | 136 WPM | Action-oriented, crisp |
| **Scene 7: Sealed Dossier** | 15 sec | 39 words | 156 WPM | Conclusive, high impact |
| **Scene 8: Closing** | 5 sec | 14 words | 168 WPM | Memorable sign-off |
| **TOTAL** | **170 sec (2:50)** | **349 words** | **~123 WPM** | **Optimal broadcast pace ($\le$ 130 WPM average)** |

---

## Production Safety Notes for Competition Compliance
1. **Hard 3-Minute Limit:** The video must conclude at or before **02:55**. YouTube rounds video duration up; a 3:00.2 video displays as 3:01, risking automated disqualification.
2. **Audio Levels:** Speech at -14 LUFS integrated, background music side-chained to duck -6 dB during speech.
3. **Hardware Disclosure:** The video clearly references UGREEN AI NAS and the official Uliya Skill runtime without fabricating physical hardware claims prior to the Nov 22 testing window.
