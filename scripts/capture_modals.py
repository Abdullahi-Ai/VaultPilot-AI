#!/usr/bin/env python3
"""
Captures screenshots of interactive overlays:
1. Create Project Modal (375px & 1280px)
2. Run Investigation Modal (375px & 1280px)
3. Evidence Review Drawer (375px & 1280px)
4. Official Audit Dossier / Report Details Modal (375px & 1280px)
"""

import os
import subprocess
from pathlib import Path

CHROME_BIN = "/usr/bin/google-chrome-stable"
BASE_URL = "http://127.0.0.1:5173"
OUT_DIR = Path("/home/osama/VaultPilot-AI/docs/screenshots/modals_and_drawers")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ("create_project_modal_desktop", f"{BASE_URL}/?modal=create_project#projects", 1280, 800),
    ("create_project_modal_mobile", f"{BASE_URL}/?modal=create_project#projects", 375, 667),
    ("run_investigation_modal_desktop", f"{BASE_URL}/?modal=run_investigation#investigations", 1280, 800),
    ("run_investigation_modal_mobile", f"{BASE_URL}/?modal=run_investigation#investigations", 375, 667),
    ("evidence_review_drawer_desktop", f"{BASE_URL}/?drawer_doc=1#reviews", 1280, 800),
    ("evidence_review_drawer_mobile", f"{BASE_URL}/?drawer_doc=1#reviews", 375, 667),
    ("report_dossier_modal_desktop", f"{BASE_URL}/?modal_inv=1#investigations", 1280, 800),
    ("report_dossier_modal_mobile", f"{BASE_URL}/?modal_inv=1#investigations", 375, 667),
]

for name, url, w, h in TARGETS:
    out_file = OUT_DIR / f"{name}.png"
    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--no-proxy-server",
        "--disable-extensions",
        "--no-first-run",
        f"--window-size={w},{h}",
        "--virtual-time-budget=3000",
        f"--screenshot={out_file}",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and out_file.exists():
        print(f"✓ Saved {name}: {out_file.stat().st_size / 1024:.1f} KB")
    else:
        print(f"✗ Failed {name}")

print("Modal & Drawer capture complete.")
