# VaultPilot AI — Final Competition Submission Checklist

**Competition:** UGREEN Hackathon 2026 on AI NAS: Bring Your Skills to UGOS (Devpost)  
**Track:** Workflow / Innovation  
**Official Skill Identifier:** `vaultpilot`  
**Round 1 Deadline:** November 15, 2026, 11:59 PM EST  
**Verification Date:** November 10, 2026  

---

## Phase A: Round 1 Initial Submission Checklist

### 1. Mandatory Submission Deliverables (Automated Verification Complete)
- [x] **Project Proposal PDF:**
  - [x] File verified at `docs/VaultPilot_AI_Project_Proposal.pdf`.
  - [x] File size is strictly $\le$ 1,048,576 bytes (**21,075 bytes / 20.6 KB**).
  - [x] Substantive word count across all 10 Starter Kit questions is strictly $\le$ 500 words (**416 substantive words**).
  - [x] Text is 100% legible, machine-readable, and verified via `pdftotext`.
  - [x] Question 1 answered in exactly one sentence.
- [x] **Pre-test Skill Package (ZIP):**
  - [x] File verified at `dist/vaultpilot-skill.zip`.
  - [x] File size is strictly $\le$ 10 MB (**18,471 bytes compressed / 44,272 bytes uncompressed**).
  - [x] SHA-256 matches frozen baseline `3498f5081a50fe44761ba105975cb02c82352b78c7bf42dc708c1714f4e699c0`.
  - [x] Contains `SKILL.md` at root with valid YAML frontmatter (`name: vaultpilot`, length 10 chars $\le$ 64).
  - [x] Zero executable binaries, Python wheels, or shell scripts inside the archive.
  - [x] All relative references in `references/` resolve cleanly.
- [x] **Automated Regression & Test Suite:**
  - [x] 155 automated backend tests passing (**155 passed, 0 failed**).
  - [x] Frontend production build completes cleanly with zero errors.
  - [x] Live E2E functional regression passing with 100% success (`scripts/e2e_functional_regression.py`).
  - [x] Multi-viewport visual QA passing with 100% success (**119/119 viewports passed**).
  - [x] Interactive modals and drawers verified at desktop and mobile widths.

### 2. Devpost Portal Form Entries (Action Required by User)
- [ ] **Project Title:** Enter `VaultPilot AI: Intelligent Financial Evidence Investigation for NGOs`
- [ ] **Tagline:** Enter `Every transaction needs evidence. Every finding needs a source.`
- [ ] **Track Selected:** Select `Workflow / Innovation`
- [ ] **Upload Required Skill Package (ZIP):** Upload `dist/vaultpilot-skill.zip`
- [ ] **Upload Required Project Proposal (PDF):** Upload `docs/VaultPilot_AI_Project_Proposal.pdf`
- [ ] **GitHub Repository Link:** Provide `https://github.com/osama/VaultPilot-AI` (or user's remote URL)
- [ ] **Demonstration Video Link (Optional for Round 1):** Link YouTube screencast if recorded.
- [ ] **Acknowledge Rules & Disclosures:**
  - [ ] Acknowledge use of open-source libraries (MIT: FastAPI, React, Vite, TailwindCSS, SQLAlchemy; GPL-2.0: `poppler-utils`).
  - [ ] Confirm no physical UGREEN NAS testing is claimed for Round 1 (emulation disclosed).

---

## Phase B: Round 2 Finalist Execution Checklist (Nov 22 – Nov 30, 2026)

### 1. Hardware Access & Live Testing (Pending Finalist Selection)
- [ ] Connect to assigned remote physical `iDX6011 Pro` running UGOS Pro using organizer credentials.
- [ ] Deploy Skill package to onboard Uliya runtime.
- [ ] Execute test investigations on `/volume1/...` storage pool.
- [ ] Complete `docs/ROUND2_NAS_VALIDATION_REPORT.md` with physical hardware performance benchmarks.

### 2. Mandatory Final Video Submission
- [ ] Record $\le$ 3-minute video on physical UGOS Pro following `docs/ROUND1_DEMO_SCRIPT.md` / `docs/ROUND2_FINAL_VIDEO_SCRIPT.md`.
- [ ] Upload to YouTube (public or unlisted) with English voiceover or subtitles.
- [ ] Add video URL to Devpost "Public Video Demo" field before November 30, 2026, 11:59 PM EST.
