#!/usr/bin/env python3
"""
VaultPilot AI — Official Devpost High-Resolution Screenshot Capture
Captures 6 genuine, high-quality browser screenshots at 1920x1080 from the live running application:
1. 01-vaultpilot-dashboard.png (Main Dashboard — Primary Devpost Screenshot)
2. 02-evidence-review.png (Evidence Review with HITL Drawer open)
3. 03-evidence-ledger.png (Evidence Ledger 3-Way Matching)
4. 04-investigation-findings.png (4-Tier Findings & Evidential Gaps)
5. 05-investigation-report.png (Official Sealed Audit Dossier Modal)
6. 06-ugreen-skill-bridge.png (UGREEN NAS Skill Bridge & Emulation Architecture)
"""

import os
import sys
import time
import subprocess
from PIL import Image

CHROME_BIN = "/opt/google/chrome/google-chrome"
BASE_URL = "http://localhost:5173"
OUT_DIR = "/home/osama/VaultPilot-AI/docs/devpost/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = [
    (
        "01-vaultpilot-dashboard.png",
        f"{BASE_URL}/#dashboard",
        "Main Dashboard — Executive Financial Compliance Overview, KPI metrics, Grant Scopes & Reconciliation Status",
        3500
    ),
    (
        "02-evidence-review.png",
        f"{BASE_URL}/?drawer_doc=109#reviews",
        "Evidence Review & Human Verification Queue — Extracted financial fields, reviewer actions, and audit trail",
        4500
    ),
    (
        "03-evidence-ledger.png",
        f"{BASE_URL}/#ledger",
        "Evidence Ledger — 3-Way Matching across Purchase Orders, Invoices, and Payment Receipts",
        3500
    ),
    (
        "04-investigation-findings.png",
        f"{BASE_URL}/#findings",
        "Findings & Evidential Gaps — 4-Tier classification taxonomy (Confirmed Discrepancies, Potential Anomalies, Missing Evidence, Unverified)",
        3500
    ),
    (
        "05-investigation-report.png",
        f"{BASE_URL}/?modal_inv=14#investigations",
        "Investigation Report — Official Audit Dossier with sealed SHA-256 snapshot integrity hash & HTML/Markdown/CSV exports",
        4500
    ),
    (
        "06-ugreen-skill-bridge.png",
        f"{BASE_URL}/#ugreen",
        "UGREEN NAS Skill Bridge — Skill integration architecture, registered expert agents, and capability catalog",
        3500
    )
]

def capture():
    print("=" * 70)
    print("VAULTPILOT AI — DEVPOST OFFICIAL SCREENSHOT CAPTURE")
    print(f"Viewport: 1920x1080 | Browser: Google Chrome Headless | DPR: 1.0")
    print(f"Output Directory: {OUT_DIR}")
    print("=" * 70)

    results = []
    for filename, url, desc, wait_ms in TARGETS:
        out_path = os.path.join(OUT_DIR, filename)
        if os.path.exists(out_path):
            os.remove(out_path)

        cmd = [
            CHROME_BIN,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--window-size=1920,1080",
            "--force-device-scale-factor=1",
            "--hide-scrollbars",
            f"--virtual-time-budget={wait_ms}",
            f"--screenshot={out_path}",
            url
        ]
        print(f"\nCapturing: {filename} ...")
        print(f"  URL: {url}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            sz_kb = os.path.getsize(out_path) / 1024
            im = Image.open(out_path)
            w, h = im.size
            print(f"  ✓ SUCCESS: {w}x{h} px | {sz_kb:.1f} KB")
            results.append((filename, w, h, sz_kb, desc, "PASS"))
        else:
            print(f"  ✗ FAILED: {res.stderr}")
            results.append((filename, 0, 0, 0, desc, "FAIL"))

    print("\n" + "=" * 70)
    print("CAPTURE SUMMARY:")
    all_passed = True
    for fn, w, h, sz, desc, status in results:
        print(f"  [{status}] {fn:<30} ({w}x{h}) - {sz:.1f} KB")
        if status != "PASS" or (w, h) != (1920, 1080):
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("ALL 6 DEVPOST SCREENSHOTS CAPTURED AT 1920x1080 SUCCESSFULLY.")
    else:
        print("SOME SCREENSHOTS ENCOUNTERED ISSUES.")
        sys.exit(1)

if __name__ == "__main__":
    capture()
