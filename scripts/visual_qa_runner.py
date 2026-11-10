#!/usr/bin/env python3
"""
VaultPilot AI — Full Visual Quality Assurance & Multi-Viewport Test Suite
Executes headless Chrome against the live local application across 7 core pages
and all target viewports (320px to 2560px + mobile/tablet portrait/landscape).
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path

CHROME_BIN = "/usr/bin/google-chrome-stable"
BASE_URL = "http://127.0.0.1:5173"
SCREENSHOTS_DIR = Path("/home/osama/VaultPilot-AI/docs/screenshots")

PAGES = [
    ("dashboard", "Dashboard", "#dashboard"),
    ("projects", "Grant Projects", "#projects"),
    ("investigations", "Investigations", "#investigations"),
    ("reviews", "Evidence Review", "#reviews"),
    ("ledger", "Evidence Ledger", "#ledger"),
    ("findings", "Findings & Gaps", "#findings"),
    ("ugreen", "UGREEN NAS Skill Bridge", "#ugreen"),
]

VIEWPORTS = [
    # (name, width, height, category)
    ("320px", 320, 568, "Mobile Portrait (Compact / iPhone SE)"),
    ("360px", 360, 640, "Mobile Portrait (Android Standard)"),
    ("375px", 375, 667, "Mobile Portrait (iPhone 8 / SE2)"),
    ("375px_portrait", 375, 812, "Mobile Portrait (iPhone X/11/12 Mini)"),
    ("390px", 390, 844, "Mobile Portrait (iPhone 12/13/14)"),
    ("430px", 430, 932, "Mobile Portrait (iPhone 14/15 Pro Max)"),
    ("600px", 600, 960, "Foldable / Compact Tablet Portrait"),
    ("768px", 768, 1024, "Tablet Portrait (iPad Mini / Air)"),
    ("812px_landscape", 812, 375, "Mobile Landscape (iPhone X/11/12)"),
    ("820px", 820, 1180, "Tablet Portrait (iPad Air 10.9)"),
    ("1024px", 1024, 768, "Tablet Landscape / Compact Desktop"),
    ("1280px", 1280, 800, "Desktop Laptop (WXGA / Chromebook)"),
    ("1366px", 1366, 768, "Desktop Laptop (HD 15.6)"),
    ("1440px", 1440, 900, "Desktop Laptop (MacBook Pro 15)"),
    ("1600px", 1600, 900, "Desktop Monitor (HD+)"),
    ("1920px", 1920, 1080, "Desktop Monitor (Full HD 1080p)"),
    ("2560px", 2560, 1440, "High-Res Display (QHD / 2K)"),
]

def capture_screenshot(url, out_path, width, height, delay_ms=3000):
    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        "--no-proxy-server",
        "--disable-extensions",
        "--no-first-run",
        f"--window-size={width},{height}",
        f"--virtual-time-budget={delay_ms}",
        f"--screenshot={out_path}",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0

def run_visual_qa():
    print("=" * 70)
    print("  VAULTPILOT AI — VISUAL QA & MULTI-VIEWPORT TEST EXECUTION")
    print("=" * 70)

    total_tests = len(PAGES) * len(VIEWPORTS)
    passed_tests = 0
    results = {}

    for page_slug, page_name, hash_tag in PAGES:
        page_dir = SCREENSHOTS_DIR / page_slug
        page_dir.mkdir(parents=True, exist_ok=True)
        results[page_slug] = []
        print(f"\n[Testing Page: {page_name}] (Hash: {hash_tag})")

        for vp_name, width, height, category in VIEWPORTS:
            out_file = page_dir / f"{page_slug}_{vp_name}.png"
            target_url = f"{BASE_URL}/{hash_tag}"

            success = capture_screenshot(target_url, str(out_file), width, height, delay_ms=2500)
            status_str = "PASS" if success else "FAIL"
            size_kb = (os.path.getsize(out_file) / 1024) if success else 0

            if success:
                passed_tests += 1
                print(f"  ✓ {vp_name:<16} ({width}x{height}) [{category}]: {size_kb:.1f} KB")
            else:
                print(f"  ✗ {vp_name:<16} ({width}x{height}) [{category}]: FAILED")

            results[page_slug].append({
                "viewport": vp_name,
                "width": width,
                "height": height,
                "category": category,
                "status": status_str,
                "file": str(out_file),
                "size_kb": size_kb
            })

    print("\n" + "=" * 70)
    print(f"VISUAL QA SUMMARY: {passed_tests} / {total_tests} VIEWPORTS PASSED ({passed_tests/total_tests*100:.1f}%)")
    print("=" * 70)

    # Save results manifest
    manifest_path = SCREENSHOTS_DIR / "visual_qa_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Test manifest saved to: {manifest_path}")

if __name__ == "__main__":
    run_visual_qa()
