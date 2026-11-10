# VaultPilot AI — Round 2 Finalist Onboarding & Hardware Staging Guide

**Target Hardware:** UGREEN AI NAS `iDX6011 Pro`  
**Operating System:** UGOS Pro (Linux-based kernel with Btrfs/EXT4 storage pool)  
**Standard:** UGREEN UGOS / Uliya Skill Development Standard (v0.7.3)  
**Execution Phase:** Round 2 Finalist Deployment & Live Validation  

---

## 1. Finalist Credential Reception & Connectivity
Upon selection as one of the 30 finalists, UGREEN organizers will provide remote access credentials to an assigned `iDX6011 Pro` hardware unit.

### Initial Access Steps:
1. **Remote Web Portal Login:**
   - URL: Provided by organizers (e.g. `https://<assigned-nas-ip>:<port>`).
   - Authenticate with designated finalist credentials.
   - Confirm UGOS Pro version and check installed system apps.
2. **Terminal / SSH Access (If Enabled by Organizers):**
   ```bash
   ssh <username>@<assigned-nas-ip> -p <port>
   ```
   - Verify non-root execution permissions.
   - Inspect mounted storage pools: `df -h` (locate `/volume1`).

---

## 2. Environment Verification Checklist

Execute the following diagnostic checks inside the remote environment:

```bash
# 1. Inspect OS and kernel
uname -a
cat /etc/os-release

# 2. Inspect available storage pool
ls -la /volume1/

# 3. Check for available command-line capabilities
which ug-filesystem || echo "ug-filesystem binary status: check UGOS agent registry"
which ug-document || echo "ug-document binary status: check UGOS agent registry"

# 4. Check available runtimes
python3 --version || echo "Python 3 not globally installed"
node -v || echo "Node.js not globally installed"

# 5. Check Poppler utilities for PDF extraction
which pdftotext || echo "pdftotext not available; verify UGOS document agent parser"
```

---

## 3. Staging Test Investigation Folders

Create isolated test directories on `/volume1` to validate discovery without altering production files:

```bash
# Create staging sandbox for NGO audit test
mkdir -p /volume1/VaultPilot_Test/orders
mkdir -p /volume1/VaultPilot_Test/invoices
mkdir -p /volume1/VaultPilot_Test/receipts

# Stage sample files
# (Copy test PDF/CSV fixtures from testing guide)
```

---

## 4. Deploying the Uliya Skill Package

1. **Deploy Package Archive:**
   - Upload `dist/vaultpilot-skill.zip` via the UGOS Skill Management portal or copy to the Uliya Skill directory:
     ```bash
     mkdir -p ~/.ugos/skills/vaultpilot
     unzip dist/vaultpilot-skill.zip -d ~/.ugos/skills/vaultpilot/
     ```
2. **Verify Declarative Manifest:**
   - Ensure `~/.ugos/skills/vaultpilot/SKILL.md` is readable.
   - Test agent invocation through the UGOS Assistant chat interface:
     *"Use vaultpilot to investigate /volume1/VaultPilot_Test"*

---

## 5. Live Hardware Diagnostic Protocol
- Verify that `ug-filesystem.find` correctly bounds searches to `/volume1/VaultPilot_Test`.
- Verify that `ug-document.extract` reliably parses invoice numbers, amounts, and dates.
- Observe whether `ug-document.reconcile` is natively supported or if comparative reasoning is executed by the onboard LLM via `SKILL.md` prompt heuristics.
- Record any CLI syntax deviations for immediate update in the validation report.
