# VaultPilot AI — Round 1 Demonstration Presentation Script (3-Minute Screencast)

**Standard:** UGREEN UGOS / Uliya Skill Development Standard (v0.7.3)  
**Execution Mode:** Offline Local Emulation (Synthetic Fixture Dataset)  
**Target Audience:** UGREEN Hackathon 2026 Technical Judges & Evaluators  

---

## Script Overview & Accounting Principles Enforced
- **Invoices are Liabilities:** An invoice alone does not prove expenditure.
- **Disbursement Discipline:** Verified spend is credited *strictly and only* when qualifying disbursement proof (payment receipt/bank voucher) is verified.
- **Credit Memo Handling:** A vendor credit memo is *not* an automatic variation order. It requires human auditor inspection in the review interface, followed by an explicit correction and documented audit rationale.
- **Immutable Reporting:** certified reports sealed prior to review actions remain 100% frozen.

---

## Detailed Scene-by-Scene Storyboard

### Scene 1: The NGO Audit Challenge (0:00 – 0:35)
- **Visual:** Split screen showing an unorganized folder tree on NAS storage alongside an audit findings letter citing documentation gaps.
- **Audio / Narration:**  
  *"When international NGOs deliver humanitarian aid, every dollar must be accounted for. But field offices often face a critical challenge: invoices, purchase orders, and payment slips are scattered across local network storage. During donor audits, missing payment receipts and unexplained billing variances can lead to devastating funding clawbacks.  
  VaultPilot AI transforms UGREEN AI NAS into an on-device financial evidence investigation vault—reconstructing evidence chains directly on local storage without cloud data leakage."*

---

### Scene 2: Scoped Discovery & Baseline 3-Way Match (0:35 – 1:15)
- **Visual:** Navigate to the VaultPilot AI dashboard. Select project `PRJ-DEMO-2026` scoped to `/volume1/NGO_Projects/Water_Health_2026`. Click **"Run Investigation"**. Show the evidence acquisition table populating.
- **Audio / Narration:**  
  *"Let's launch an investigation. VaultPilot AI scans the authorized directory scope and indexes documents with SHA-256 evidence digests.  
  Notice our first transaction item: Purchase Order `PO-2026-081` for solar inverters at \$8,500 USD matches Invoice `INV-SP-1092` and Bank Remittance `REC-BNK-993` to the penny. The three-way reconciliation engine classifies this as a `RECONCILED_MATCH`, crediting \$8,500.00 to verified project spend because complete, verified disbursement proof exists."*

---

### Scene 3: Discrepancy Detection & Report Sealing (1:15 – 1:55)
- **Visual:** Click on the **Findings** tab. Highlight finding: `CONFIRMED_DISCREPANCY` between `PO-MED-441` (\$12,000 USD) and `INV-MED-7712` (\$14,500 USD). Show the +\$2,500 variance. Then click **"Reports"** and generate an official audit report snapshot. Show the SHA-256 integrity hash.
- **Audio / Narration:**  
  *"However, our clinic rehabilitation procurement flags a critical issue. The purchase order approved \$12,000 USD, but the vendor billed \$14,500 USD—a documented +\$2,500 overbilling variance. Under our conservative 4-tier taxonomy, this is classified as a `CONFIRMED_DISCREPANCY`.  
  Before taking action, the lead auditor seals an official investigation report. Notice the cryptographic SHA-256 fingerprint generated over the snapshot payload. This ensures historical records can never be retroactively altered."*

---

### Scene 4: Human Verification & Discrepancy Correction (1:55 – 2:35)
- **Visual:** Open the **Evidence Review** drawer for `INV-MED-7712`. Display the raw extracted fields. Click **"Correct"** on the amount field. Enter `$12,000.00`, reviewer ID `auditor_elena`, and rationale: *"Vendor Credit Memo CM-01 covers 2,500 equipment discount"*. Submit the correction. Click **"Re-evaluate Reconciliation"**.
- **Audio / Narration:**  
  *"Now, our human auditor investigates. In the Evidence Review drawer, she locates vendor Credit Memo `CM-01`, which discounted \$2,500 for delayed delivery. A credit memo does not automatically alter contracts; it requires professional human verification.  
  The auditor records the corrected billing of \$12,000 USD, logging her justification into the immutable audit trail. Notice the original \$14,500 extraction is preserved alongside the correction.  
  With one click, she re-evaluates reconciliation. The billing discrepancy resolves immediately. And because payment voucher `VOUCH-331` is verified on file, the \$12,000 authorized expenditure is credited to verified project spend."*

---

### Scene 5: Evidentiary Degradation & Report Immutability (2:35 – 3:00)
- **Visual:** Show `INV-UNSUPP-902` flagged as `MISSING_EVIDENCE` (spend remains \$0.00) and `IMG_7781_blurry.jpg` flagged as `UNVERIFIED`. Finally, return to the previously sealed audit report and show its SHA-256 integrity hash is 100% identical.
- **Audio / Narration:**  
  *"Notice our strict accounting discipline: an unaccompanied invoice for \$2,400 remains classified as `MISSING_EVIDENCE`, and a blurry receipt remains `UNVERIFIED`—zero spend is credited without proof.  
  Finally, we re-check our sealed report: its cryptographic hash is completely unchanged, preserving the historical pre-review audit state.  
  VaultPilot AI: Every transaction needs evidence. Every finding needs a source. Thank you."*
