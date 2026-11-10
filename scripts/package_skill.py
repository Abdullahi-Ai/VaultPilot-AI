#!/usr/bin/env python3
"""
VaultPilot AI — Skill Package Auditor, Packager & Uliya Compliance Validator
Validates:
1. SKILL.md YAML frontmatter compliance (name, description).
2. Linked reference file resolution in references/.
3. Zero prohibited binaries, executables, or unsupported scripts.
4. Size constraints (<= 10MB total, <= 1MB per file).
5. Deterministic ZIP packaging into dist/vaultpilot-skill.zip.
6. Checksum calculation and extraction verification.
7. Verification against official Uliya check-skill.mjs.
"""

import os
import sys
import zipfile
import hashlib
import re
import shutil
import subprocess

SKILL_DIR = "vaultpilot"
ZIP_PATH = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "dist/vaultpilot-skill-round2-candidate.zip"

PROHIBITED_EXTENSIONS = {
    ".py", ".pyc", ".sh", ".bash", ".exe", ".bin", ".so", ".dll",
    ".dylib", ".class", ".jar", ".wasm", ".tar", ".gz"
}

def verify_frontmatter(skill_md_path):
    if not os.path.exists(skill_md_path):
        return False, "SKILL.md does not exist"

    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not match:
        return False, "SKILL.md missing valid YAML frontmatter ('---' header/footer)"

    fm_text = match.group(1)
    name_m = re.search(r"^name:\s*([a-zA-Z0-9_-]+)", fm_text, re.MULTILINE)
    if not name_m:
        return False, "Frontmatter missing 'name' field"
    name = name_m.group(1).strip()
    if not (2 <= len(name) <= 64):
        return False, f"Name length ({len(name)}) must be between 2 and 64 characters"
    if name != name.lower():
        return False, f"Name '{name}' must be all lowercase"

    desc_m = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
    if not desc_m:
        return False, "Frontmatter missing single-line 'description' field"
    desc = desc_m.group(1).strip()

    if not desc:
        return False, "Description cannot be empty"
    if len(desc) > 1024:
        return False, f"Description length ({len(desc)}) exceeds 1,024 characters"

    return True, f"Frontmatter valid: name='{name}', description length={len(desc)}"

def audit_directory(skill_dir):
    issues = []
    total_size = 0
    file_count = 0
    files_found = []

    for root, dirs, files in os.walk(skill_dir):
        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, skill_dir)
            files_found.append(rel_path)
            file_count += 1
            sz = os.path.getsize(path)
            total_size += sz

            if sz > 1024 * 1024:
                issues.append(f"File {rel_path} exceeds 1 MB ({sz} bytes)")

            ext = os.path.splitext(f)[1].lower()
            if ext in PROHIBITED_EXTENSIONS:
                issues.append(f"Prohibited file format detected: {rel_path}")

    if total_size > 10 * 1024 * 1024:
        issues.append(f"Total package uncompressed size exceeds 10 MB ({total_size} bytes)")

    # Verify root constraints under Uliya v0.7.3: root can only contain SKILL.md and references/
    for item in os.listdir(skill_dir):
        if item == "SKILL.md":
            continue
        elif item == "references" and os.path.isdir(os.path.join(skill_dir, item)):
            continue
        else:
            issues.append(f"Unauthorized item at root of Skill package: {item}")

    # Verify linked references
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        issues.append("Missing mandatory SKILL.md at root")
    else:
        with open(skill_md, "r", encoding="utf-8") as f:
            md_text = f.read()
        links = re.findall(r"\[.*?\]\((references/[a-zA-Z0-9_.-]+\.md)\)", md_text)
        for link in links:
            target = os.path.join(skill_dir, link)
            if not os.path.exists(target):
                issues.append(f"Linked reference not found: {link}")

        # Ensure all files under references/ are linked
        ref_dir = os.path.join(skill_dir, "references")
        if os.path.exists(ref_dir):
            for ref_file in os.listdir(ref_dir):
                if ref_file.endswith(".md"):
                    expected_link = f"references/{ref_file}"
                    if expected_link not in links:
                        issues.append(f"Reference file '{expected_link}' is not linked directly from SKILL.md")

    return sorted(files_found), total_size, issues

def build_zip(skill_dir, zip_path):
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Collect files deterministically
    file_list = []
    for root, dirs, files in os.walk(skill_dir):
        for f in files:
            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, skill_dir)
            file_list.append((full_path, arcname))

    file_list.sort(key=lambda x: x[1])

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for full_path, arcname in file_list:
            # Normalize timestamp for reproducible build
            zinfo = zipfile.ZipInfo(arcname, date_time=(2026, 11, 10, 0, 0, 0))
            zinfo.external_attr = 0o644 << 16
            with open(full_path, "rb") as f:
                content = f.read()
            zf.writestr(zinfo, content)

    # Compute hash
    h = hashlib.sha256()
    with open(zip_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def audit_zip_file(zip_path):
    if not os.path.exists(zip_path):
        return None, [], 0, ["ZIP file does not exist"]

    h = hashlib.sha256()
    with open(zip_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    actual_hash = h.hexdigest()

    issues = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        infolist = zf.infolist()
        total_size = sum(i.file_size for i in infolist)
        names = [i.filename for i in infolist]

        if "SKILL.md" not in names:
            issues.append("ZIP does not contain SKILL.md at archive root")

        for info in infolist:
            if info.file_size > 1024 * 1024:
                issues.append(f"Archive entry {info.filename} exceeds 1 MB ({info.file_size} bytes)")
            ext = os.path.splitext(info.filename)[1].lower()
            if ext in PROHIBITED_EXTENSIONS:
                issues.append(f"Archive contains prohibited file: {info.filename}")

    # Test extraction
    test_extract_dir = "/tmp/skill-extract-test"
    if os.path.exists(test_extract_dir):
        shutil.rmtree(test_extract_dir)
    os.makedirs(test_extract_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(test_extract_dir)
    except Exception as e:
        issues.append(f"ZIP extraction failed: {str(e)}")
    finally:
        if os.path.exists(test_extract_dir):
            shutil.rmtree(test_extract_dir)

    return actual_hash, names, total_size, issues

def run_official_checker(skill_dir):
    checker_path = "/tmp/uliya-skill-kit/uliya-skill-kit/scripts/check-skill.mjs"
    if not os.path.exists(checker_path):
        return None, "Official checker not found at /tmp/uliya-skill-kit/uliya-skill-kit/scripts/check-skill.mjs"
    result = subprocess.run(
        ["node", checker_path, os.path.abspath(skill_dir)],
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout

def main():
    build_mode = "--build" in sys.argv or "-b" in sys.argv

    print("=" * 60)
    print("VAULTPILOT AI — SKILL PACKAGE & COMPLIANCE AUDIT")
    print("=" * 60)

    # 1. Frontmatter
    fm_ok, fm_msg = verify_frontmatter(os.path.join(SKILL_DIR, "SKILL.md"))
    print(f"Frontmatter Check: {'PASSED' if fm_ok else 'FAILED'} -> {fm_msg}")

    # 2. Source Directory
    files_found, total_sz, dir_issues = audit_directory(SKILL_DIR)
    print(f"\nSource Directory '{SKILL_DIR}/':")
    print(f"  Files: {files_found}")
    print(f"  Total Uncompressed Size: {total_sz} bytes ({total_sz/1024:.1f} KB)")
    print(f"  Directory Issues: {dir_issues if dir_issues else 'None (Clean)'}")

    # 3. Official Checker Execution
    checker_rc, checker_out = run_official_checker(SKILL_DIR)
    print(f"\nOfficial check-skill.mjs Validation:")
    print(f"  Exit Code: {checker_rc}")
    if checker_rc == 0:
        print("  Status: STATIC PASS (0 errors, 0 warnings)")
    else:
        print(f"  Output: {checker_out}")

    # 4. Build or Audit ZIP
    if build_mode:
        print(f"\nBuilding deterministic archive '{ZIP_PATH}'...")
        new_hash = build_zip(SKILL_DIR, ZIP_PATH)
        print(f"  Built successfully. SHA-256: {new_hash}")

    zip_hash, zip_files, zip_sz, zip_issues = audit_zip_file(ZIP_PATH)
    print(f"\nArchive '{ZIP_PATH}':")
    print(f"  SHA-256 Digest: {zip_hash}")
    print(f"  Archive Entries: {zip_files}")
    print(f"  Archive Size: {os.path.getsize(ZIP_PATH)} bytes compressed, {zip_sz} bytes uncompressed")
    print(f"  Archive Issues: {zip_issues if zip_issues else 'None (Clean)'}")

    if fm_ok and not dir_issues and not zip_issues and checker_rc == 0:
        print("\nOVERALL SKILL PACKAGE AUDIT: ALL CHECKS PASSED (STATIC PASS)")
        sys.exit(0)
    else:
        print("\nOVERALL SKILL PACKAGE AUDIT: ISSUES DETECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()
