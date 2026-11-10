#!/usr/bin/env python3
"""
VaultPilot AI — Proposal PDF Generator & Word Count Validator
Strictly enforces:
1. Substantive answer word count <= 500 English words.
2. PDF file size <= 1,048,576 bytes (1 MB).
"""

import os
import re
import sys
import subprocess

def parse_proposal(markdown_path):
    with open(markdown_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    title = ""
    subtitle = ""
    meta = []
    questions = []

    current_q = None
    current_ans = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
        elif stripped.startswith("## "):
            subtitle = stripped[3:].strip()
        elif stripped.startswith("**Track:**") or stripped.startswith("**Official Skill Identifier:**") or stripped.startswith("**Platform Standard:**"):
            meta.append(stripped)
        elif re.match(r"^###\s+\d+\.", stripped):
            if current_q:
                questions.append((current_q, " ".join(current_ans).strip()))
            current_q = stripped[4:].strip()
            current_ans = []
        elif current_q:
            if stripped and not stripped.startswith("---"):
                current_ans.append(stripped)

    if current_q:
        questions.append((current_q, " ".join(current_ans).strip()))

    return title, subtitle, meta, questions

def count_substantive_words(questions):
    total = 0
    breakdown = []
    for q, ans in questions:
        words = re.findall(r"\b[A-Za-z0-9_'-]+\b", ans)
        count = len(words)
        total += count
        breakdown.append((q, count))
    return total, breakdown

def escape_ps(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def generate_pdf(markdown_path, output_pdf_path):
    title, subtitle, meta, questions = parse_proposal(markdown_path)
    word_count, breakdown = count_substantive_words(questions)

    print(f"=== Substantive Word Count Validation ===")
    for q, count in breakdown:
        short_q = q[:50] + "..." if len(q) > 50 else q
        print(f"  {short_q}: {count} words")
    print(f"Total Substantive Words: {word_count} / 500 max")

    if word_count > 500:
        raise ValueError(f"WORD COUNT EXCEEDED: {word_count} words (Limit is 500 words)")

    # Generate professional PostScript
    ps_lines = [
        "%!PS-Adobe-3.0",
        "%%BoundingBox: 0 0 612 792",
        "%%Pages: 2",
        "%%EndComments",
        "/LM 54 def",
        "/RM 558 def",
        "/PW 504 def",
        "/FTitle /Helvetica-Bold findfont 14 scalefont def",
        "/FSub /Helvetica-Bold findfont 10 scalefont def",
        "/FMeta /Helvetica-Oblique findfont 8.5 scalefont def",
        "/FQ /Helvetica-Bold findfont 8.5 scalefont def",
        "/FA /Helvetica findfont 8.0 scalefont def",
        "/FNum /Helvetica-Bold findfont 8.0 scalefont def",
        "/lineHeight 10.5 def",
        "/qLineHeight 11.5 def",
        "%%Page: 1 1",
        "0.1 0.3 0.6 setrgbcolor",
        "LM 755 moveto (VAULTPILOT AI: FINANCIAL EVIDENCE INVESTIGATION FOR NGOS) FTitle setfont show",
        "0.2 0.2 0.2 setrgbcolor",
        "LM 742 moveto (UGREEN Hackathon 2026 on AI NAS | Official Round 1 Project Proposal) FSub setfont show",
        "0.5 0.5 0.5 setrgbcolor",
        "LM 734 moveto RM 734 lineto stroke",
        "0.3 0.3 0.3 setrgbcolor",
        "LM 724 moveto (Track: Workflow / Innovation   |   Skill ID: vaultpilot   |   Standard: UGREEN UGOS / Uliya v0.7.3) FMeta setfont show",
        "LM 716 moveto RM 716 lineto stroke",
        "/y 700 def"
    ]

    # Helper function for word-wrapped text
    def wrap_text(text, max_chars=105):
        words = text.split()
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 > max_chars:
                lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
            else:
                cur.append(w)
                cur_len += len(w) + 1
        if cur:
            lines.append(" ".join(cur))
        return lines

    page = 1
    for idx, (q, ans) in enumerate(questions, 1):
        # Check if need new page
        q_lines = wrap_text(f"{q}", 95)
        ans_lines = wrap_text(ans, 105)
        needed_h = (len(q_lines) * 12) + (len(ans_lines) * 10.5) + 14

        ps_lines.append(f"% --- Question {idx} ---")
        ps_lines.append("0.1 0.25 0.5 setrgbcolor")
        ps_lines.append("FQ setfont")
        for ql in q_lines:
            ps_lines.append(f"LM y moveto ({escape_ps(ql)}) show")
            ps_lines.append("/y y qLineHeight sub def")

        ps_lines.append("0.15 0.15 0.15 setrgbcolor")
        ps_lines.append("FA setfont")
        for al in ans_lines:
            ps_lines.append(f"LM y moveto ({escape_ps(al)}) show")
            ps_lines.append("/y y lineHeight sub def")

        ps_lines.append("/y y 6 sub def")

    # Footer
    ps_lines.append("0.5 0.5 0.5 setrgbcolor")
    ps_lines.append("LM 38 moveto RM 38 lineto stroke")
    ps_lines.append(f"LM 28 moveto (VaultPilot AI | Official Round 1 Proposal | Substantive Words: {word_count}/500 | Format: PDF <= 1MB) FMeta setfont show")
    ps_lines.append("showpage")
    ps_lines.append("%%EOF")

    ps_content = "\n".join(ps_lines)
    tmp_ps = "/tmp/proposal_temp.ps"
    with open(tmp_ps, "w", encoding="utf-8") as f:
        f.write(ps_content)

    # Convert to PDF using ps2pdf
    cmd = ["ps2pdf", "-dPDFSETTINGS=/prepress", "-dEmbedAllFonts=true", tmp_ps, output_pdf_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ps2pdf failed: {res.stderr}")

    size_bytes = os.path.getsize(output_pdf_path)
    print(f"Generated PDF: {output_pdf_path}")
    print(f"File Size: {size_bytes} bytes ({size_bytes / 1024:.1f} KB) / 1,048,576 bytes max")

    if size_bytes > 1048576:
        raise ValueError(f"PDF SIZE EXCEEDED: {size_bytes} bytes (Limit is 1 MB)")

    return word_count, size_bytes

if __name__ == "__main__":
    md_file = "docs/ROUND1_PROJECT_PROPOSAL.md"
    pdf_file = "docs/VaultPilot_AI_Project_Proposal.pdf"
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
    if len(sys.argv) > 2:
        pdf_file = sys.argv[2]

    wc, sz = generate_pdf(md_file, pdf_file)
    print(f"SUCCESS: Substantive Words: {wc}/500 | PDF Size: {sz/1024:.1f} KB (<= 1MB)")
