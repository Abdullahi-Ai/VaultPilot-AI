# VaultPilot AI — Round 2 Final Demo Video Production Script (3 Minutes)

**Mandatory Competition Rule:** Public YouTube Video ($\le$ 3:00) featuring live footage on assigned UGREEN AI NAS hardware with English narration or subtitles.

---

## Technical Specifications
- **Duration:** Strictly $\le$ 2 minutes 55 seconds (to prevent 3:01 clipping disqualification).
- **Resolution:** 1080p (1920x1080) at 30 or 60 fps.
- **Audio:** Clear English narration, normalized to -14 LUFS, background ambient music at -24 dB.
- **Visuals:** Direct screen capture of UGOS Pro UI running on `iDX6011 Pro`.

---

## Timed Scene-by-Scene Script

### Scene 1: The NGO Funding Crisis (0:00 – 0:30)
- **Visual:** Fast-paced opening. Direct screen recording showing UGOS Pro desktop. Open File Manager to `/volume1/NGO_Projects`. Show folders cluttered with PDFs, spreadsheets, and scanned receipts.
- **Narration:**  
  *"For international NGOs, lost paperwork isn't just an inconvenience—it's a financial catastrophe. Every year, humanitarian organizations face severe grant clawbacks from institutional donors simply because field payment receipts and purchase orders are scattered across local office storage.  
  Meet VaultPilot AI: a NAS-native financial evidence investigation Skill built for UGREEN AI NAS."*

---

### Scene 2: Scoped Discovery on UGREEN AI NAS (0:30 – 1:05)
- **Visual:** Open UGOS AI Assistant. Type the command:  
  `"Use vaultpilot to investigate /volume1/NGO_Projects/Water_Sanitation_2026"`  
  Show the Skill activating, delegating to `file-agent`, and scanning the directory.
- **Narration:**  
  *"Operating directly on our UGREEN iDX6011 Pro, VaultPilot AI discovers financial records within the authorized directory. It indexes every document with streaming SHA-256 evidence digests.  
  Operating strictly read-only, it preserves all original files without moving or modifying a single byte."*

---

### Scene 3: Multi-Document 3-Way Reconciliation (1:05 – 1:40)
- **Visual:** Show the interactive investigation report generating in real-time. Show the three-way matching table:
  - Row 1: `PO-2026-081` (\$8,500) $\longleftrightarrow$ `INV-SP-1092` (\$8,500) $\longleftrightarrow$ `REC-BNK-993` (\$8,500) $\rightarrow$ `RECONCILED_MATCH`.
  - Row 2: `PO-MED-441` (\$12,000) $\longleftrightarrow$ `INV-MED-7712` (\$14,500) $\rightarrow$ `CONFIRMED_DISCREPANCY` (+\$2,500 variance).
- **Narration:**  
  *"VaultPilot AI reconstructs complete three-way evidence chains. Solar inverters match to the penny across purchase order, invoice, and payment slip, crediting \$8,500 to verified expenditure.  
  However, for clinic beds, the vendor billed \$14,500 against an approved \$12,000 purchase order. VaultPilot AI's conservative 4-tier audit taxonomy flags a Confirmed Discrepancy, citing the exact returned file paths."*

---

### Scene 4: Human Review & Re-Reconciliation (1:40 – 2:20)
- **Visual:** Open the Evidence Review drawer for `INV-MED-7712`. Highlight vendor Credit Memo `CM-01`. Enter human correction: adjust invoice billing to `$12,000.00`, enter auditor notes: *"Credit Memo CM-01 verified on file"*. Click **"Re-evaluate Reconciliation"**. Show the discrepancy resolving to `RECONCILED_MATCH` and verified spend updating.
- **Narration:**  
  *"AI shouldn't make unilateral financial decisions. In the Evidence Review drawer, an auditor inspects Credit Memo CM-01, which adjusted for delivery delays.  
  She enters the corrected \$12,000 billing, preserving the original extraction and logging an immutable audit record. With one click, she re-evaluates reconciliation. The discrepancy clears, and with payment proof confirmed on file, the \$12,000 is safely credited to verified project spend."*

---

### Scene 5: Audit Integrity & Conclusion (2:20 – 2:50)
- **Visual:** Show `INV-UNSUPP-902` flagged as `MISSING_EVIDENCE` (spend remains \$0.00) and blurry scan flagged as `UNVERIFIED`. Open sealed report snapshot showing SHA-256 hash completely unchanged.
- **Narration:**  
  *"Strict accounting principles are enforced: unaccompanied invoices and unreadable scans fail-closed with zero spend credited. And certified audit reports remain sealed with SHA-256 integrity hashes, completely immune to retroactive tampering.  
  VaultPilot AI on UGREEN AI NAS: Every transaction needs evidence. Every finding needs a source."*
- **Visual (2:50 – 2:55):** UGREEN Hackathon 2026 Title Card + GitHub / Devpost link.
