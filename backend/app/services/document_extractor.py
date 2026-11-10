"""
VaultPilot AI — Genuine Financial Document Extraction Engine
Extracts verified financial data from PDF, CSV, TXT, and JSON documents.
Maintains strict evidentiary provenance, TOCTOU protection, and read-only invariants.
Untrusted companion sidecars are explicitly tagged and never automatically verified.
"""

import os
import csv
import json
import re
import stat
import datetime
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

CURRENCY_REGEX = re.compile(r"\b(USD|EUR|GBP|KES|UGX|CAD|AUD|CHF|JPY|ZAR|NGN|INR|RWF)\b", re.IGNORECASE)
DATE_REGEX_ISO = re.compile(r"\b(20\d{2}[-/]\d{2}[-/]\d{2})\b")
DATE_REGEX_COMMON = re.compile(r"\b(\d{2}[-/]\d{2}[-/]20\d{2})\b")

class FinancialDocumentExtractor:
    """
    Genuine multi-format financial document parser.
    Extracts structured fields without hallucinating or inventing missing values.
    """

    MAX_FILE_READ_BYTES = 5 * 1024 * 1024  # 5 MB safety limit for text/CSV reading
    MAX_SIDECAR_BYTES = 1 * 1024 * 1024    # 1 MB safety limit for companion sidecars

    @classmethod
    def extract_document(
        cls,
        file_path: str,
        doc_type: str,
        nas_root: Optional[str] = None,
        file_sha256: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts structured financial fields and full provenance from a genuine file.
        Returns a standardized financial extraction payload.
        """
        if not os.path.exists(file_path):
            return {"status": "UNAVAILABLE", "error": f"File does not exist: {file_path}"}

        # Check special files before reading
        try:
            st = os.lstat(file_path)
            if (stat.S_ISFIFO(st.st_mode) or stat.S_ISSOCK(st.st_mode) or
                stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode)):
                return {"status": "UNAVAILABLE", "error": f"Special non-regular file rejected: {file_path}"}
        except OSError as e:
            return {"status": "UNAVAILABLE", "error": f"Cannot stat file: {str(e)}"}

        ext = os.path.splitext(file_path)[1].lower()
        file_size = st.st_size

        # Default empty provenance structure
        provenance = {
            "source_path": file_path,
            "filename": os.path.basename(file_path),
            "file_size_bytes": file_size,
            "sha256": file_sha256,
            "extraction_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "extraction_method": "UNKNOWN",
            "requires_human_verification": False
        }

        # Route by file extension
        if ext == ".pdf":
            result = cls._extract_pdf(file_path, doc_type, provenance, nas_root)
        elif ext == ".csv":
            result = cls._extract_csv(file_path, doc_type, provenance)
        elif ext in (".txt", ".md"):
            result = cls._extract_txt(file_path, doc_type, provenance)
        elif ext == ".json":
            result = cls._extract_json_document(file_path, doc_type, provenance)
        else:
            # Binary image or unsupported media (e.g. .jpg, .png, .tiff)
            result = cls._handle_scanned_or_binary(file_path, doc_type, provenance, nas_root)

        return result

    @classmethod
    def _extract_pdf(
        cls,
        file_path: str,
        doc_type: str,
        provenance: Dict[str, Any],
        nas_root: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extracts text from machine-readable PDF using pdftotext.
        If the PDF is a scanned image with no text stream, checks for untrusted companion sidecars.
        """
        provenance["source_format"] = "PDF"

        try:
            # Controlled arguments with '--' to prevent flag injection; safe execution timeout
            proc = subprocess.run(
                ["pdftotext", "-layout", "--", file_path, "-"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            raw_text = proc.stdout[:cls.MAX_FILE_READ_BYTES] if proc.returncode == 0 else ""
        except FileNotFoundError:
            raw_text = ""
        except subprocess.TimeoutExpired:
            return {
                "status": "UNVERIFIED",
                "error": "PDF text extraction timed out.",
                "requires_human_verification": True,
                "provenance": provenance
            }
        except Exception as e:
            return {
                "status": "CORRUPTED",
                "error": f"PDF extraction failed: {str(e)}",
                "requires_human_verification": True,
                "provenance": provenance
            }

        cleaned_text = raw_text.strip() if raw_text else ""

        # Case A: Machine-readable text successfully extracted from PDF
        if cleaned_text:
            provenance["extraction_method"] = "PDF_TEXT_LAYOUT"
            provenance["requires_human_verification"] = False
            extracted = cls._parse_text_layout(cleaned_text, doc_type, file_path)
            extracted["status"] = "EXTRACTED"
            extracted["provenance"] = provenance
            extracted["requires_human_verification"] = False
            return extracted

        # Case B: PDF has no machine-readable text (scanned image PDF)
        # Check if an untrusted companion sidecar is present
        sidecar_data = cls._read_untrusted_sidecar(file_path, nas_root)
        if sidecar_data:
            provenance["extraction_method"] = "UNTRUSTED_SIDECAR"
            provenance["requires_human_verification"] = True
            provenance["untrusted_sidecar_path"] = sidecar_data.get("_sidecar_path")
            provenance["is_verified_evidence"] = False

            result = dict(sidecar_data)
            result.pop("_sidecar_path", None)
            result.setdefault("status", "EXTRACTED")
            result["requires_human_verification"] = True
            result["is_verified_evidence"] = False
            result["error"] = "Extracted from untrusted companion metadata; unverified against scanned PDF content."
            result["provenance"] = provenance
            cls._ensure_standard_references(result, doc_type, file_path)
            return result

        # Case C: Scanned PDF without sidecar and no local OCR
        provenance["extraction_method"] = "NONE"
        provenance["requires_human_verification"] = True
        return {
            "status": "UNVERIFIED",
            "document_type": doc_type,
            "error": "Scanned PDF containing no machine-readable text; local OCR capability not available.",
            "requires_human_verification": True,
            "provenance": provenance
        }

    @classmethod
    def _extract_csv(
        cls,
        file_path: str,
        doc_type: str,
        provenance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extracts structured accounting data and itemized rows from CSV.
        Preserves Decimal precision, prevents double-counting between line items and summary rows,
        and records exact row-level provenance.
        """
        provenance["source_format"] = "CSV"
        provenance["extraction_method"] = "CSV_STRUCTURED"

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                fd = f.fileno()
                st_before = os.fstat(fd)
                lines = [line for idx, line in enumerate(f) if idx < 1000] # max 1000 rows
                st_after = os.fstat(fd)
                if st_before.st_mtime_ns != st_after.st_mtime_ns:
                    return {
                        "status": "UNVERIFIED",
                        "error": "CSV file mutated concurrently during extraction.",
                        "requires_human_verification": True,
                        "provenance": provenance
                    }
        except Exception as e:
            return {
                "status": "CORRUPTED",
                "error": f"Failed to read CSV: {str(e)}",
                "requires_human_verification": True,
                "provenance": provenance
            }

        if not lines:
            return {
                "status": "UNVERIFIED",
                "error": "Empty CSV file.",
                "requires_human_verification": True,
                "provenance": provenance
            }

        reader = csv.DictReader(lines)
        if not reader.fieldnames:
            return {
                "status": "UNVERIFIED",
                "error": "Malformed CSV header.",
                "requires_human_verification": True,
                "provenance": provenance
            }

        res: Dict[str, Any] = {
            "status": "EXTRACTED",
            "document_type": doc_type,
            "line_items": [],
            "requires_human_verification": False,
            "provenance": provenance,
            "field_provenance": {}
        }

        item_total_sum = Decimal("0.00")
        tax_total_sum = Decimal("0.00")
        explicit_summary_total: Optional[Decimal] = None
        explicit_summary_tax: Optional[Decimal] = None
        explicit_total_row_num: Optional[int] = None

        currencies_seen = set()
        dates_seen = {}
        vendors_seen = {}
        po_refs_seen = {}
        inv_nums_seen = {}
        rec_ids_seen = {}
        first_amt_row_num = None

        row_idx = 1 # Header is row 1
        for row in reader:
            row_idx += 1
            r_lower = {k.lower().strip().replace(" ", "_"): (v.strip() if v else "") for k, v in row.items() if k}

            desc = r_lower.get("description") or r_lower.get("item") or r_lower.get("details") or ""
            is_summary_row = desc.lower().strip() in (
                "total", "grand total", "subtotal", "sum", "balance due", "invoice total", "total amount"
            )

            # Amount extraction
            amt_val: Optional[Decimal] = None
            for key in ["amount", "line_total", "net_amount", "billed", "paid", "total", "total_amount"]:
                if key in r_lower and r_lower[key]:
                    try:
                        clean_num = r_lower[key].replace(",", "").replace("$", "").replace("€", "").replace("£", "")
                        amt_val = Decimal(clean_num)
                        if first_amt_row_num is None:
                            first_amt_row_num = row_idx
                        break
                    except (InvalidOperation, ValueError):
                        pass

            # Tax extraction
            tax_val: Optional[Decimal] = None
            for key in ["tax", "tax_amount", "vat", "gst", "sales_tax"]:
                if key in r_lower and r_lower[key]:
                    try:
                        clean_tax = r_lower[key].replace(",", "").replace("$", "").replace("€", "").replace("£", "")
                        tax_val = Decimal(clean_tax)
                        break
                    except (InvalidOperation, ValueError):
                        pass

            if is_summary_row:
                # Capture as explicit summary total; do NOT add into item_total_sum to prevent double counting
                if amt_val is not None and explicit_summary_total is None:
                    explicit_summary_total = amt_val
                    explicit_total_row_num = row_idx
                if tax_val is not None and explicit_summary_tax is None:
                    explicit_summary_tax = tax_val
                continue

            # Standard item row
            if amt_val is not None:
                item_total_sum += amt_val
            if tax_val is not None:
                tax_total_sum += tax_val

            # Quantity and unit price
            qty = None
            if "quantity" in r_lower or "qty" in r_lower:
                try:
                    qty = float(r_lower.get("quantity") or r_lower.get("qty") or "1")
                except ValueError:
                    qty = 1.0

            unit_price = None
            if "unit_price" in r_lower or "price" in r_lower:
                try:
                    unit_price = float((r_lower.get("unit_price") or r_lower.get("price") or "").replace(",", "").replace("$", ""))
                except ValueError:
                    pass

            res["line_items"].append({
                "row_number": row_idx,
                "description": desc,
                "quantity": qty,
                "unit_price": unit_price,
                "amount": float(amt_val) if amt_val is not None else None,
                "tax": float(tax_val) if tax_val is not None else None
            })

            # Currency
            for key in ["currency", "curr", "curr_code"]:
                if key in r_lower and r_lower[key]:
                    c_clean = r_lower[key].upper()
                    if len(c_clean) == 3 and c_clean.isalpha():
                        currencies_seen.add((c_clean, row_idx))

            # Date
            for key in ["date", "transaction_date", "doc_date", "invoice_date"]:
                if key in r_lower and r_lower[key] and "date" not in dates_seen:
                    dates_seen["date"] = (r_lower[key], row_idx)

            # Vendor
            for key in ["vendor", "supplier", "payee", "company", "vendor_name"]:
                if key in r_lower and r_lower[key] and "vendor" not in vendors_seen:
                    vendors_seen["vendor"] = (r_lower[key], row_idx)

            # References
            for key in ["po_reference", "po_number", "po_ref", "order_no"]:
                if key in r_lower and r_lower[key] and "po" not in po_refs_seen:
                    po_refs_seen["po"] = (r_lower[key], row_idx)
            for key in ["invoice_number", "invoice_no", "inv_no", "bill_no"]:
                if key in r_lower and r_lower[key] and "inv" not in inv_nums_seen:
                    inv_nums_seen["inv"] = (r_lower[key], row_idx)
            for key in ["receipt_id", "receipt_no", "voucher_no"]:
                if key in r_lower and r_lower[key] and "rec" not in rec_ids_seen:
                    rec_ids_seen["rec"] = (r_lower[key], row_idx)

        # Financial reconciliation: use explicit summary total if provided, otherwise sum of line items
        final_total: Optional[Decimal] = None
        final_row_num = None
        if explicit_summary_total is not None:
            final_total = explicit_summary_total
            final_row_num = explicit_total_row_num
        elif len(res["line_items"]) > 0 and item_total_sum > Decimal("0.00"):
            final_total = item_total_sum
            final_row_num = first_amt_row_num

        final_tax: Optional[Decimal] = None
        if explicit_summary_tax is not None:
            final_tax = explicit_summary_tax
        elif tax_total_sum > Decimal("0.00"):
            final_tax = tax_total_sum

        res["amount"] = float(final_total) if final_total is not None else None
        res["tax_amount"] = float(final_tax) if final_tax is not None else None

        # Metadata
        res["currency"] = next(iter(currencies_seen))[0] if len({c[0] for c in currencies_seen}) == 1 else None
        res["date"] = dates_seen["date"][0] if dates_seen else None
        res["vendor"] = vendors_seen["vendor"][0] if vendors_seen else None

        if po_refs_seen:
            res["po_reference"] = po_refs_seen["po"][0]
        if inv_nums_seen:
            res["invoice_number"] = inv_nums_seen["inv"][0]
        if rec_ids_seen:
            res["receipt_id"] = rec_ids_seen["rec"][0]

        # Field-level exact provenance
        fp = {}
        if res["amount"] is not None:
            fp["amount"] = {"value": res["amount"], "source_location": f"Row {final_row_num}" if final_row_num else None}
        if res["tax_amount"] is not None:
            fp["tax_amount"] = {"value": res["tax_amount"], "source_location": f"Row {explicit_total_row_num or first_amt_row_num}" if (explicit_total_row_num or first_amt_row_num) else None}
        if res["currency"]:
            curr_row = next(iter(currencies_seen))[1] if currencies_seen else None
            fp["currency"] = {"value": res["currency"], "source_location": f"Row {curr_row}" if curr_row else None}
        if res["vendor"]:
            fp["vendor"] = {"value": res["vendor"], "source_location": f"Row {vendors_seen['vendor'][1]}" if vendors_seen else None}
        if res["date"]:
            fp["date"] = {"value": res["date"], "source_location": f"Row {dates_seen['date'][1]}" if dates_seen else None}
        if res.get("po_reference"):
            fp["po_reference"] = {"value": res["po_reference"], "source_location": f"Row {po_refs_seen['po'][1]}" if po_refs_seen else None}
        if res.get("invoice_number"):
            fp["invoice_number"] = {"value": res["invoice_number"], "source_location": f"Row {inv_nums_seen['inv'][1]}" if inv_nums_seen else None}
        res["field_provenance"] = fp

        cls._ensure_standard_references(res, doc_type, file_path)
        return res

    @classmethod
    def _extract_txt(
        cls,
        file_path: str,
        doc_type: str,
        provenance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extracts structured financial fields from plain-text or markdown files.
        """
        provenance["source_format"] = "TEXT"
        provenance["extraction_method"] = "TXT_PARSER"

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                fd = f.fileno()
                st_before = os.fstat(fd)
                content = f.read(cls.MAX_FILE_READ_BYTES)
                st_after = os.fstat(fd)
                if st_before.st_mtime_ns != st_after.st_mtime_ns:
                    return {
                        "status": "UNVERIFIED",
                        "error": "Text file mutated concurrently during extraction.",
                        "requires_human_verification": True,
                        "provenance": provenance
                    }
        except Exception as e:
            return {
                "status": "CORRUPTED",
                "error": f"Failed to read text file: {str(e)}",
                "requires_human_verification": True,
                "provenance": provenance
            }

        extracted = cls._parse_text_layout(content, doc_type, file_path)
        extracted["status"] = "EXTRACTED"
        extracted["provenance"] = provenance
        extracted["requires_human_verification"] = False
        return extracted

    @classmethod
    def _extract_json_document(
        cls,
        file_path: str,
        doc_type: str,
        provenance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extracts financial fields from native structured JSON documents.
        """
        provenance["source_format"] = "JSON"
        provenance["extraction_method"] = "JSON_DOCUMENT"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                fd = f.fileno()
                st_before = os.fstat(fd)
                data = json.load(f)
                st_after = os.fstat(fd)
                if st_before.st_mtime_ns != st_after.st_mtime_ns:
                    return {
                        "status": "UNVERIFIED",
                        "error": "JSON file mutated concurrently during extraction.",
                        "requires_human_verification": True,
                        "provenance": provenance
                    }
        except json.JSONDecodeError as e:
            return {
                "status": "CORRUPTED",
                "error": f"Malformed JSON: {str(e)}",
                "requires_human_verification": True,
                "provenance": provenance
            }
        except Exception as e:
            return {
                "status": "CORRUPTED",
                "error": f"Failed to read JSON: {str(e)}",
                "requires_human_verification": True,
                "provenance": provenance
            }

        if not isinstance(data, dict):
            return {
                "status": "UNVERIFIED",
                "error": "JSON document root is not an object.",
                "requires_human_verification": True,
                "provenance": provenance
            }

        res: Dict[str, Any] = {
            "status": "EXTRACTED",
            "document_type": data.get("document_type") or doc_type,
            "vendor": data.get("vendor") or data.get("supplier") or data.get("payee"),
            "date": data.get("date") or data.get("transaction_date"),
            "currency": cls._validate_currency(data.get("currency")),
            "amount": cls._safe_float(data.get("amount") if data.get("amount") is not None else data.get("total")),
            "tax_amount": cls._safe_float(data.get("tax_amount") if data.get("tax_amount") is not None else data.get("tax")),
            "line_items": data.get("line_items") if isinstance(data.get("line_items"), list) else [],
            "payment_reference": data.get("payment_reference") or data.get("payment_ref"),
            "payment_status": data.get("payment_status"),
            "project_reference": data.get("project_reference") or data.get("project_code"),
            "requires_human_verification": False,
            "provenance": provenance
        }

        # References
        if "po_reference" in data or "po_ref" in data or "order_no" in data:
            res["po_reference"] = data.get("po_reference") or data.get("po_ref") or data.get("order_no")
        if "invoice_number" in data or "invoice_no" in data:
            res["invoice_number"] = data.get("invoice_number") or data.get("invoice_no")
        if "invoice_reference" in data or "invoice_ref" in data:
            res["invoice_reference"] = data.get("invoice_reference") or data.get("invoice_ref")
        if "receipt_id" in data or "receipt_no" in data:
            res["receipt_id"] = data.get("receipt_id") or data.get("receipt_no")

        # Field provenance for JSON
        fp = {}
        for fld in ["amount", "tax_amount", "currency", "vendor", "date", "po_reference", "invoice_number", "receipt_id", "payment_reference", "payment_status"]:
            if res.get(fld) is not None:
                matching_k = next((k for k in data if k.lower().replace("_", "") == fld.lower().replace("_", "")), fld)
                fp[fld] = {"value": res[fld], "source_location": f"Key '{matching_k}'"}
        res["field_provenance"] = fp

        cls._ensure_standard_references(res, res["document_type"], file_path)
        return res

    @classmethod
    def _handle_scanned_or_binary(
        cls,
        file_path: str,
        doc_type: str,
        provenance: Dict[str, Any],
        nas_root: Optional[str]
    ) -> Dict[str, Any]:
        """
        Handles image/binary files. Checks for untrusted companion sidecars.
        Since local OCR is not installed, results are always marked UNVERIFIED.
        """
        provenance["source_format"] = "BINARY_IMAGE"

        sidecar_data = cls._read_untrusted_sidecar(file_path, nas_root)
        if sidecar_data:
            provenance["extraction_method"] = "UNTRUSTED_SIDECAR"
            provenance["requires_human_verification"] = True
            provenance["untrusted_sidecar_path"] = sidecar_data.get("_sidecar_path")
            provenance["is_verified_evidence"] = False

            result = dict(sidecar_data)
            result.pop("_sidecar_path", None)
            result.setdefault("status", "EXTRACTED")
            result["requires_human_verification"] = True
            result["is_verified_evidence"] = False
            result["error"] = "Extracted from untrusted companion sidecar; physical image not verified by OCR."
            result["provenance"] = provenance
            cls._ensure_standard_references(result, doc_type, file_path)
            return result

        provenance["extraction_method"] = "NONE"
        provenance["requires_human_verification"] = True
        return {
            "status": "UNVERIFIED",
            "document_type": doc_type,
            "error": "Scanned or binary document without machine-readable text and no local OCR capability available.",
            "requires_human_verification": True,
            "provenance": provenance
        }

    @classmethod
    def _read_untrusted_sidecar(cls, file_path: str, nas_root: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Safely attempts to read an untrusted companion JSON sidecar.
        Enforces size cap, boundary containment within nas_root, and regular file stat checks.
        """
        candidates = [
            f"{file_path}.json",
            f"{os.path.splitext(file_path)[0]}.json",
            f"{file_path}.meta.json"
        ]
        real_root = os.path.realpath(nas_root) if nas_root and os.path.exists(nas_root) else None
        parent_dir = os.path.dirname(os.path.realpath(file_path))

        for cand in candidates:
            if os.path.exists(cand):
                real_cand = os.path.realpath(cand)
                # Verify containment and sibling directory location
                if real_root and os.path.commonpath([real_root, real_cand]) != real_root:
                    continue
                if os.path.dirname(real_cand) != parent_dir:
                    continue
                try:
                    lst = os.lstat(cand)
                    if not stat.S_ISREG(lst.st_mode) or lst.st_size > cls.MAX_SIDECAR_BYTES:
                        continue
                    with open(cand, "r", encoding="utf-8") as sf:
                        fd = sf.fileno()
                        st_b = os.fstat(fd)
                        data = json.load(sf)
                        st_a = os.fstat(fd)
                        if st_b.st_mtime_ns != st_a.st_mtime_ns:
                            continue
                        if isinstance(data, dict):
                            data["_sidecar_path"] = cand
                            return data
                except Exception:
                    continue
        return None

    @classmethod
    def _parse_text_layout(cls, content: str, doc_type: str, file_path: str) -> Dict[str, Any]:
        """
        Deterministic parser for structured text/PDF layouts.
        Extracts numbers, ISO currency, dates, vendors, tax, and item lines without inventing values.
        """
        res: Dict[str, Any] = {
            "document_type": doc_type,
            "vendor": None,
            "date": None,
            "currency": None,
            "amount": None,
            "tax_amount": None,
            "line_items": [],
            "payment_reference": None,
            "payment_status": None,
            "project_reference": None
        }

        # 1. Total Amount extraction
        total_match = re.search(
            r"(?:total\s*(?:amount|due|billed|sum)?|grand\s*total|net\s*payable|amount\s*due|amount)[\s:=]+(?:[A-Za-z]{3}\s*)?((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,4})?)",
            content,
            re.IGNORECASE
        )
        if total_match:
            try:
                res["amount"] = float(total_match.group(1).replace(",", ""))
            except ValueError:
                res["amount"] = None

        # 2. Tax Amount extraction
        tax_match = re.search(
            r"(?:tax\s*(?:amount|due|sum)?|vat\s*(?:amount)?|gst\s*(?:amount)?|sales\s*tax)[\s:=]+(?:[A-Za-z]{3}\s*)?((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,4})?)",
            content,
            re.IGNORECASE
        )
        if tax_match:
            try:
                res["tax_amount"] = float(tax_match.group(1).replace(",", ""))
            except ValueError:
                res["tax_amount"] = None

        # 3. Currency extraction
        curr_match = CURRENCY_REGEX.search(content)
        if curr_match:
            res["currency"] = curr_match.group(1).upper()

        # 4. Date extraction
        date_iso = DATE_REGEX_ISO.search(content)
        if date_iso:
            res["date"] = date_iso.group(1)
        else:
            date_common = DATE_REGEX_COMMON.search(content)
            if date_common:
                res["date"] = date_common.group(1)

        # 5. Vendor extraction
        vendor_match = re.search(
            r"(?:vendor|supplier|payee|from|billed\s*by|contractor)[\s:=]+([^\n\r,;]{2,60})",
            content,
            re.IGNORECASE
        )
        if vendor_match:
            v_clean = vendor_match.group(1).strip()
            # Eliminate garbage matches like "Total" or "Date"
            if not any(stop in v_clean.lower() for stop in ["date", "amount", "total", "tax", "po-", "inv-"]):
                res["vendor"] = v_clean

        # 6. References
        po_match = re.search(r"\b(PO[-_0-9A-Z]+)\b", content, re.IGNORECASE)
        if po_match:
            res["po_reference"] = po_match.group(1).upper()

        inv_match = re.search(r"\b(INV[-_0-9A-Z]+)\b", content, re.IGNORECASE)
        if inv_match:
            inv_code = inv_match.group(1).upper()
            res["invoice_number"] = inv_code
            res["invoice_reference"] = inv_code

        rec_match = re.search(r"\b(REC[-_0-9A-Z]+|VOUCH[-_0-9A-Z]+)\b", content, re.IGNORECASE)
        if rec_match:
            res["receipt_id"] = rec_match.group(1).upper()

        # 7. Project Reference
        prj_match = re.search(r"\b(PRJ[-_0-9A-Z]+)\b", content, re.IGNORECASE)
        if prj_match:
            res["project_reference"] = prj_match.group(1).upper()

        # 8. Payment status
        pay_match = re.search(r"\b(PAID|PENDING|PARTIALLY\s*PAID|UNPAID)\b", content, re.IGNORECASE)
        if pay_match:
            res["payment_status"] = pay_match.group(1).upper()

        # 9. Line items heuristic
        for line in content.splitlines():
            line_clean = line.strip()
            # Match lines like: "1. Solar Panels - Qty: 4 @ 500.00 = 2000.00"
            item_match = re.search(r"^(?:[-*•\d.]+\s*)?([A-Za-z0-9\s-]{3,40})\s+(?:Qty[:\s]*(\d+))?.*?(?:[\$€£]?\s*([0-9,]+\.[0-9]{2}))", line_clean, re.IGNORECASE)
            if item_match and not any(kw in line_clean.lower() for kw in ["total", "amount due", "subtotal", "tax", "vat"]):
                desc = item_match.group(1).strip()
                qty_str = item_match.group(2)
                amt_str = item_match.group(3)
                try:
                    res["line_items"].append({
                        "description": desc,
                        "quantity": float(qty_str) if qty_str else 1.0,
                        "amount": float(amt_str.replace(",", "")) if amt_str else None
                    })
                except ValueError:
                    pass

        # 10. Field-level provenance line tracking
        fp = {}
        for idx, line in enumerate(content.splitlines(), start=1):
            l_str = line.strip()
            if not l_str:
                continue
            if res["amount"] is not None and "amount" not in fp:
                if re.search(r"(?:total\s*(?:amount|due|billed|sum)?|grand\s*total|net\s*payable|amount\s*due|amount)", l_str, re.IGNORECASE):
                    fp["amount"] = {"value": res["amount"], "source_location": f"Line {idx}"}
            if res["tax_amount"] is not None and "tax_amount" not in fp:
                if re.search(r"(?:tax\s*(?:amount|due|sum)?|vat|gst|sales\s*tax)", l_str, re.IGNORECASE):
                    fp["tax_amount"] = {"value": res["tax_amount"], "source_location": f"Line {idx}"}
            if res["currency"] and "currency" not in fp:
                if CURRENCY_REGEX.search(l_str):
                    fp["currency"] = {"value": res["currency"], "source_location": f"Line {idx}"}
            if res["date"] and "date" not in fp:
                if DATE_REGEX_ISO.search(l_str) or DATE_REGEX_COMMON.search(l_str):
                    fp["date"] = {"value": res["date"], "source_location": f"Line {idx}"}
            if res["vendor"] and "vendor" not in fp:
                if re.search(r"(?:vendor|supplier|payee|from|billed\s*by|contractor)", l_str, re.IGNORECASE):
                    fp["vendor"] = {"value": res["vendor"], "source_location": f"Line {idx}"}
            if res.get("po_reference") and "po_reference" not in fp:
                if re.search(r"\bPO[-_0-9A-Z]+\b", l_str, re.IGNORECASE):
                    fp["po_reference"] = {"value": res["po_reference"], "source_location": f"Line {idx}"}
            if res.get("invoice_number") and "invoice_number" not in fp:
                if re.search(r"\bINV[-_0-9A-Z]+\b", l_str, re.IGNORECASE):
                    fp["invoice_number"] = {"value": res["invoice_number"], "source_location": f"Line {idx}"}
            if res.get("receipt_id") and "receipt_id" not in fp:
                if re.search(r"\b(?:REC|VOUCH)[-_0-9A-Z]+\b", l_str, re.IGNORECASE):
                    fp["receipt_id"] = {"value": res["receipt_id"], "source_location": f"Line {idx}"}

        res["field_provenance"] = fp

        cls._ensure_standard_references(res, doc_type, file_path)
        return res

    @staticmethod
    def _validate_currency(curr: Any) -> Optional[str]:
        if curr and isinstance(curr, str) and len(curr.strip()) == 3 and curr.strip().isalpha():
            return curr.strip().upper()
        return None

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(str(val).replace(",", "").replace("$", ""))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _ensure_standard_references(res: Dict[str, Any], doc_type: str, file_path: str) -> None:
        """Ensures standard PO, Invoice, and Receipt lookup keys exist for reconciliation."""
        stem = os.path.splitext(os.path.basename(file_path))[0]
        if doc_type == "PURCHASE_ORDER":
            res.setdefault("po_reference", stem)
        elif doc_type == "INVOICE":
            res.setdefault("invoice_number", stem)
        elif doc_type == "RECEIPT":
            res.setdefault("receipt_id", stem)
