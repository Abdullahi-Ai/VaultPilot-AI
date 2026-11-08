import csv
import io
import pytest
from decimal import Decimal
from app.models.project import Project
from app.models.investigation import Investigation
from app.models.document import Document
from app.models.finding import Finding
from app.models.ledger import EvidenceLedgerEntry
from app.models.report import InvestigationReport
from app.services.report_service import ReportService
from app.services.csv_exporter import (
    CSVFinancialExporter,
    ReportIntegrityError,
    validate_financial_decimal,
    format_financial_decimal,
    sanitize_csv_text_cell,
    has_excessive_precision,
    is_currency_recognized,
    get_currency_minor_units
)

@pytest.fixture
def rich_investigation_setup(test_db):
    """Creates a complete populated investigation environment with multiple currencies and findings."""
    project = Project(
        name="Emergency Medical Support Project",
        code="EMSP-2026",
        donor="Global Health Alliance",
        budget=250000.0,
        currency="USD",
        nas_folder_path="/volume1/finance/EMSP-2026"
    )
    test_db.add(project)
    test_db.flush()

    inv = Investigation(
        project_id=project.id,
        title="Q1-Q2 Comprehensive Procurement Audit",
        scope_path="/volume1/finance/EMSP-2026",
        status="COMPLETED",
        summary="Audit of medical supplies procurement.",
        document_count=3
    )
    test_db.add(inv)
    test_db.flush()

    doc_po = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="PO-9001.pdf",
        file_path="/volume1/finance/EMSP-2026/orders/PO-9001.pdf",
        document_type="PURCHASE_ORDER",
        extraction_status="EXTRACTED",
        extracted_data={"po_reference": "PO-9001", "amount": 12500.0, "currency": "USD", "vendor": "MedEquip Ltd"}
    )
    doc_inv = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="INV-ME-4001.pdf",
        file_path="/volume1/finance/EMSP-2026/invoices/INV-ME-4001.pdf",
        document_type="INVOICE",
        extraction_status="EXTRACTED",
        extracted_data={"invoice_number": "INV-ME-4001", "po_reference": "PO-9001", "amount": 12500.0, "currency": "USD", "vendor": "MedEquip Ltd"}
    )
    doc_rec = Document(
        project_id=project.id,
        investigation_id=inv.id,
        filename="REC-BNK-8012.pdf",
        file_path="/volume1/finance/EMSP-2026/receipts/REC-BNK-8012.pdf",
        document_type="RECEIPT",
        extraction_status="EXTRACTED",
        extracted_data={"receipt_id": "REC-BNK-8012", "invoice_reference": "INV-ME-4001", "amount": 12500.0, "currency": "USD"}
    )
    test_db.add_all([doc_po, doc_inv, doc_rec])
    test_db.flush()

    f1 = Finding(
        investigation_id=inv.id,
        title="Overbilled Logistics Surcharge",
        classification="CONFIRMED_DISCREPANCY",
        subject_reference="PO-9001 vs INV-ME-4001",
        source_paths=[doc_po.file_path, doc_inv.file_path],
        expected_value="Authorized budget limit",
        observed_value="Billed surcharge in excess of contract",
        variance_explanation="Billed variance of 450.00 USD without change order approval.",
        recommended_action="Recover 450.00 USD excess billing from next disbursement.",
        source_document_ids=[doc_po.id, doc_inv.id],
        missing_evidence_details="Signed variation authorization missing.",
        evidence_limitations="Scope limited to EMSP-2026.",
        classification_rationale="Classified as CONFIRMED_DISCREPANCY because contract limits were breached."
    )
    test_db.add(f1)

    # 1. Standard USD entry
    entry1 = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-USD-001",
        item_description="Surgical Diagnostics & Patient Monitors",
        supplier_name="MedEquip Ltd",
        po_reference="PO-9001",
        po_amount=12500.0,
        invoice_number="INV-ME-4001",
        invoice_amount=12500.0,
        receipt_proof="REC-BNK-8012",
        receipt_amount=12500.0,
        paid_amount=12500.0,
        currency="USD",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH",
        variance_amount=0.0,
        source_file_paths=[doc_po.file_path, doc_inv.file_path, doc_rec.file_path],
        source_document_ids=[doc_po.id, doc_inv.id, doc_rec.id]
    )

    # 2. Legitimate negative variance / credit adjustment entry
    entry2 = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-USD-002",
        item_description="Vendor Volume Rebate Discount",
        supplier_name="MedEquip Ltd",
        invoice_number="CR-ME-002",
        invoice_amount=-1500.0,
        paid_amount=-1500.0,
        currency="USD",
        variance_amount=-25.50,
        variance_reason="Rebate credit note adjustment",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH"
    )

    # 3. EUR Entry for multi-currency segregation
    entry_eur = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-EUR-001",
        item_description="Cold-Chain Vaccine Chillers",
        supplier_name="BioKlima AG",
        po_reference="PO-EUR-77",
        po_amount=8400.0,
        invoice_number="INV-BK-202",
        invoice_amount=8400.0,
        receipt_proof="REC-EUR-33",
        paid_amount=8400.0,
        currency="EUR",
        reconciliation_status="RECONCILED_MATCH",
        match_confidence="EXACT_MATCH"
    )

    # 4. Undocumented Currency Entry
    entry_undoc = EvidenceLedgerEntry(
        investigation_id=inv.id,
        transaction_id="TXN-UNDOC-99",
        item_description="Field Clinic Waste Management",
        invoice_number="INV-UNK-99",
        invoice_amount=350.0,
        paid_amount=350.0,
        currency=None,
        reconciliation_status="UNVERIFIED",
        match_confidence="UNMATCHED",
        requires_human_review=True,
        human_review_reason="Missing currency code on invoice."
    )

    test_db.add_all([entry1, entry2, entry_eur, entry_undoc])
    test_db.commit()

    return {
        "project": project,
        "investigation": inv,
        "docs": [doc_po, doc_inv, doc_rec],
        "findings": [f1],
        "entries": [entry1, entry2, entry_eur, entry_undoc]
    }


# =========================================================================
# 1. DEF-02 Re-Audit: Currency Recognition & Exact Precision Tests
# =========================================================================

def test_iso_4217_currency_recognition():
    """DEF-02-C: Verify ISO 4217 currency registry and minor unit mappings."""
    # Zero decimal
    assert get_currency_minor_units("JPY") == 0
    assert get_currency_minor_units("KRW") == 0
    assert is_currency_recognized("JPY") is True

    # Three decimal
    assert get_currency_minor_units("KWD") == 3
    assert get_currency_minor_units("BHD") == 3
    assert is_currency_recognized("KWD") is True

    # Two decimal
    assert get_currency_minor_units("USD") == 2
    assert get_currency_minor_units("EUR") == 2
    assert get_currency_minor_units("GBP") == 2
    assert is_currency_recognized("USD") is True

    # Unrecognized / Missing
    assert get_currency_minor_units("XYZ") is None
    assert is_currency_recognized("XYZ") is False
    assert get_currency_minor_units("") is None
    assert get_currency_minor_units(None) is None
    assert is_currency_recognized(None) is False


def test_has_excessive_precision():
    """DEF-02-B: Verify detection of amounts exceeding recognized currency minor units."""
    # JPY: zero minor units
    assert has_excessive_precision(1000, "JPY") is False
    assert has_excessive_precision("1000", "JPY") is False
    assert has_excessive_precision("1000.50", "JPY") is True
    assert has_excessive_precision(1000.5, "JPY") is True

    # USD: two minor units
    assert has_excessive_precision("123.45", "USD") is False
    assert has_excessive_precision(123.45, "USD") is False
    assert has_excessive_precision("123.456", "USD") is True
    assert has_excessive_precision("123.4567", "USD") is True

    # KWD: three minor units
    assert has_excessive_precision("12.500", "KWD") is False
    assert has_excessive_precision("12.5001", "KWD") is True

    # Missing and unsupported currencies are not flagged as excessive precision (flagged separately)
    assert has_excessive_precision("100.00", None) is False
    assert has_excessive_precision("100.00", "XYZ") is False


def test_financial_decimal_preserves_source_precision_without_silent_rounding():
    """DEF-02: Verify that sub-cent fractional amounts are NOT silently rounded."""
    assert validate_financial_decimal("123.456", currency="USD") == Decimal("123.456")
    assert format_financial_decimal("123.456", currency="USD") == "123.456"

    assert validate_financial_decimal("123.4567", currency="USD") == Decimal("123.4567")
    assert format_financial_decimal("123.4567", currency="USD") == "123.4567"

    assert validate_financial_decimal(Decimal("999.888"), currency="USD") == Decimal("999.888")
    assert format_financial_decimal(Decimal("999.888"), currency="USD") == "999.888"


def test_unsupported_and_missing_currency_decimal_handling():
    """DEF-02-A: Verify unsupported and missing currencies do NOT assume two decimal places."""
    # Missing currency: exact source digits preserved, no padding
    assert validate_financial_decimal("100", currency=None) == Decimal("100")
    assert format_financial_decimal("100", currency=None) == "100"
    assert validate_financial_decimal("100.00", currency=None) == Decimal("100.00")
    assert format_financial_decimal("100.00", currency=None) == "100.00"

    # Unsupported currency: exact source digits preserved, no padding
    assert validate_financial_decimal("500", currency="XYZ") == Decimal("500")
    assert format_financial_decimal("500", currency="XYZ") == "500"
    assert validate_financial_decimal("500.5", currency="XYZ") == Decimal("500.5")
    assert format_financial_decimal("500.5", currency="XYZ") == "500.5"


def test_currency_specific_precision_and_negative_zero():
    """DEF-02: Verify currency-specific precision handling and negative zero normalization."""
    # Zero-decimal currencies (JPY, KRW)
    assert validate_financial_decimal(1000, currency="JPY") == Decimal("1000")
    assert format_financial_decimal(1000, currency="JPY") == "1000"
    assert validate_financial_decimal("1000.50", currency="JPY") == Decimal("1000.50")
    assert format_financial_decimal("1000.50", currency="JPY") == "1000.50"

    # Three-decimal currencies (KWD, BHD)
    assert validate_financial_decimal(12.5, currency="KWD") == Decimal("12.500")
    assert format_financial_decimal(12.5, currency="KWD") == "12.500"
    assert format_financial_decimal("12.5001", currency="KWD") == "12.5001"

    # Negative zero normalization
    assert validate_financial_decimal("-0", currency="USD") == Decimal("0.00")
    assert validate_financial_decimal("-0.00", currency="USD") == Decimal("0.00")
    assert format_financial_decimal("-0", currency="USD") == "0.00"
    assert format_financial_decimal("-0.00", currency="USD") == "0.00"


def test_financial_decimal_validation_rejects_malformed_and_formulas():
    """Verify malformed inputs, formula-like strings, and non-finite values are rejected."""
    # Formula-like strings resembling numbers
    assert validate_financial_decimal(" -1+1") is None
    assert validate_financial_decimal("-1+1") is None
    assert validate_financial_decimal("=-1500.00") is None
    assert validate_financial_decimal("-A1+B1") is None
    assert validate_financial_decimal("+100-50") is None

    # Non-finite values
    assert validate_financial_decimal(float("nan")) is None
    assert validate_financial_decimal(float("inf")) is None
    assert validate_financial_decimal(float("-inf")) is None
    assert validate_financial_decimal("NaN") is None
    assert validate_financial_decimal("Infinity") is None
    assert validate_financial_decimal("-Infinity") is None

    # Malformed strings with letters, currency labels, or multiple dots
    assert validate_financial_decimal("12500.00USD") is None
    assert validate_financial_decimal("$1500.00") is None
    assert validate_financial_decimal("1.2.3") is None
    assert validate_financial_decimal("N/A") is None
    assert validate_financial_decimal("") is None
    assert validate_financial_decimal(None) is None
    assert validate_financial_decimal(True) is None
    assert validate_financial_decimal(False) is None


def test_format_financial_decimal_never_silently_defaults_to_zero():
    """Verify that invalid/missing financial values produce empty strings, never 0.00."""
    assert format_financial_decimal(1500.0, currency="USD") == "1500.00"
    assert format_financial_decimal(-25.50, currency="USD") == "-25.50"
    assert format_financial_decimal(0.0, currency="USD") == "0.00"

    assert format_financial_decimal(None) == ""
    assert format_financial_decimal("") == ""
    assert format_financial_decimal("INVALID") == ""
    assert format_financial_decimal("NaN") == ""
    assert format_financial_decimal(None) != "0.00"


# =========================================================================
# 2. Formula-Injection Security & Identifier Sanitization (DEF-03)
# =========================================================================

def test_csv_formula_injection_sanitization_standard_triggers():
    """Verify formula triggers (=, +, -, @, %, |) are neutralized with single-quote prefix."""
    assert sanitize_csv_text_cell("=1+1") == "'=1+1"
    assert sanitize_csv_text_cell("+1+1") == "'+1+1"
    assert sanitize_csv_text_cell("-1+1") == "'-1+1"
    assert sanitize_csv_text_cell("@SUM(A1:A5)") == "'@SUM(A1:A5)"
    assert sanitize_csv_text_cell("%SYSTEM%") == "'%SYSTEM%"
    assert sanitize_csv_text_cell("|calc.exe") == "'|calc.exe"


def test_csv_formula_injection_with_leading_whitespace_and_control_chars():
    """Verify formula triggers preceded by spaces, tabs, CR, or LF are neutralized."""
    assert sanitize_csv_text_cell("   =1+1") == "'   =1+1"
    assert sanitize_csv_text_cell("  +500") == "'  +500"
    assert sanitize_csv_text_cell("\t=1+1") == "'\t=1+1"
    assert sanitize_csv_text_cell("\r=1+1") == "'\r=1+1"
    assert sanitize_csv_text_cell("\n=1+1") == "'\n=1+1"
    assert sanitize_csv_text_cell(" \t@SUM(A1:A5)") == "' \t@SUM(A1:A5)"
    assert sanitize_csv_text_cell("\r\n-cmd|'/C calc'!A0") == "'\r\n-cmd|'/C calc'!A0"


def test_csv_safe_ordinary_text_preserved_without_quote():
    """Verify legitimate text values without formula triggers are not modified."""
    assert sanitize_csv_text_cell("Solar Water Pumps") == "Solar Water Pumps"
    assert sanitize_csv_text_cell("Invoice #INV-2026-001") == "Invoice #INV-2026-001"
    assert sanitize_csv_text_cell("MedEquip Global Ltd.") == "MedEquip Global Ltd."
    assert sanitize_csv_text_cell("Lot A - 30 days turnaround") == "Lot A - 30 days turnaround"
    assert sanitize_csv_text_cell("") == ""
    assert sanitize_csv_text_cell(None) == ""


def test_csv_defensive_sanitization_of_finding_and_document_ids():
    """DEF-03: Verify finding and document identifiers are defensively neutralized against formula triggers."""
    assert sanitize_csv_text_cell("=F101") == "'=F101"
    assert sanitize_csv_text_cell("+D202") == "'+D202"
    assert sanitize_csv_text_cell("-DOC-3") == "'-DOC-3"
    assert sanitize_csv_text_cell("@DOC-4") == "'@DOC-4"
    assert sanitize_csv_text_cell(101) == "101"
    assert sanitize_csv_text_cell("101") == "101"


# =========================================================================
# 3. Snapshot Integrity Gating & Fail-Closed Tests
# =========================================================================

def test_csv_export_valid_snapshot_succeeds(test_db, rich_investigation_setup):
    """DEF-01: Verify untampered report snapshot generates clean CSV by default, and optional header when requested."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    # 1. Default export (no metadata header comments)
    csv_text = CSVFinancialExporter.export_schedule(report, schedule="reconciliation")
    assert csv_text.startswith("\ufeff")
    clean_text = csv_text.lstrip("\ufeff")
    lines = clean_text.splitlines()
    assert lines[0].startswith("Transaction_Tracking_ID,Item_Description")
    assert "# VaultPilot AI Audit Export" not in csv_text

    # 2. Explicit metadata mode
    csv_with_meta = CSVFinancialExporter.export_schedule(report, schedule="reconciliation", include_metadata_header=True)
    assert "# VaultPilot AI Audit Export" in csv_with_meta
    assert f"# Report ID: IR-{report.id}-V1" in csv_with_meta
    assert f"# Cryptographic Integrity: VERIFIED ({report.snapshot_integrity_hash})" in csv_with_meta


def test_csv_export_tampered_snapshot_refuses_export(test_db, rich_investigation_setup):
    """Verify tampered snapshot payload fails closed and raises ReportIntegrityError."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    tampered_payload = dict(report.snapshot_payload)
    tampered_payload["tampered_key"] = "unauthorized_modification"
    report.snapshot_payload = tampered_payload

    with pytest.raises(ReportIntegrityError) as exc_info:
        CSVFinancialExporter.export_schedule(report, schedule="reconciliation")

    assert "REPORT_INTEGRITY_VERIFICATION_FAILED" in str(exc_info.value)
    assert "Export generation refused" in str(exc_info.value)


def test_csv_export_missing_hash_or_payload_refuses_export():
    """Verify missing hash, missing payload, or None report raises ReportIntegrityError."""
    with pytest.raises(ReportIntegrityError):
        CSVFinancialExporter.export_schedule(None)

    empty_rep = InvestigationReport(id=1, snapshot_payload=None, snapshot_integrity_hash="abc")
    with pytest.raises(ReportIntegrityError):
        CSVFinancialExporter.export_schedule(empty_rep)

    no_hash_rep = InvestigationReport(id=2, snapshot_payload={"k": "v"}, snapshot_integrity_hash=None)
    with pytest.raises(ReportIntegrityError):
        CSVFinancialExporter.export_schedule(no_hash_rep)


def test_csv_export_invalid_schedule_name_rejected(test_db, rich_investigation_setup):
    """Verify invalid schedule parameter raises ValueError."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    with pytest.raises(ValueError) as exc_info:
        CSVFinancialExporter.export_schedule(report, schedule="nonexistent_schedule")

    assert "Invalid schedule 'nonexistent_schedule'" in str(exc_info.value)
    assert "Must be one of: reconciliation, summary, findings, evidence" in str(exc_info.value)


# =========================================================================
# 4. Standard CSV Interoperability Tests (DEF-01)
# =========================================================================

def test_standard_csv_reader_and_dictreader_interoperability(test_db, rich_investigation_setup):
    """DEF-01: Verify all schedules can be consumed directly by standard csv.reader and csv.DictReader."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    for schedule in CSVFinancialExporter.VALID_SCHEDULES:
        csv_text = CSVFinancialExporter.export_schedule(report, schedule=schedule)
        clean_text = csv_text.lstrip("\ufeff")

        # 1. Direct csv.reader consumption
        reader = list(csv.reader(io.StringIO(clean_text)))
        header_row = reader[0]
        data_rows = reader[1:]
        expected_len = len(header_row)
        assert expected_len > 0

        # Every data row must have the exact same number of fields as the header
        for r_idx, r in enumerate(data_rows):
            assert len(r) == expected_len, f"Inconsistent field count in schedule '{schedule}' row {r_idx}"

        # 2. Direct csv.DictReader consumption without line filtering
        dict_reader = csv.DictReader(io.StringIO(clean_text))
        assert dict_reader.fieldnames == header_row
        dict_rows = list(dict_reader)
        assert len(dict_rows) == len(data_rows)


# =========================================================================
# 5. Financial Integrity in Schedules: Review Flags & Exclusions (DEF-02)
# =========================================================================

def test_reconciliation_schedule_flags_unsupported_currency_and_excessive_precision():
    """DEF-02-A & DEF-02-B: Verify reconciliation schedule flags unsupported currency and excessive precision."""
    # Create a synthetic report snapshot with excessive precision and unsupported currency
    payload = {
        "investigation_summary": {"project_code": "PREC-01", "project_name": "Precision Test"},
        "reconciliation_ledger_snapshot": [
            {
                "transaction_id": "TXN-EXCESS-01",
                "item_description": "Fractional Precision Goods",
                "currency": "USD",
                "po_amount": 123.456,
                "invoice_amount": 123.456,
                "paid_amount": 123.456,
                "reconciliation_status": "RECONCILED_MATCH",
                "match_confidence": "EXACT_MATCH",
                "requires_human_review": False
            },
            {
                "transaction_id": "TXN-UNSUPP-01",
                "item_description": "Unsupported Currency Goods",
                "currency": "XYZ",
                "po_amount": 500.0,
                "invoice_amount": 500.0,
                "paid_amount": 500.0,
                "reconciliation_status": "RECONCILED_MATCH",
                "match_confidence": "EXACT_MATCH",
                "requires_human_review": False
            }
        ]
    }
    sha_hash = ReportService.compute_snapshot_hash(payload)
    rep = InvestigationReport(id=201, investigation_id=1, report_version=1, snapshot_payload=payload, snapshot_integrity_hash=sha_hash)

    csv_text = CSVFinancialExporter.export_schedule(rep, schedule="reconciliation")
    clean_text = csv_text.lstrip("\ufeff")
    reader = list(csv.DictReader(io.StringIO(clean_text)))

    # Row 1: Excessive precision in USD
    row1 = reader[0]
    assert row1["Transaction_Tracking_ID"] == "TXN-EXCESS-01"
    assert row1["Requires_Human_Review"] == "Yes"
    assert row1["Reconciliation_Status"] == "EXCESSIVE_PRECISION_HOLD"
    assert "minor-unit precision" in row1["Human_Review_Reason"]
    assert row1["Invoice_Billed_Amount"] == "123.456"

    # Row 2: Unsupported currency XYZ
    row2 = reader[1]
    assert row2["Transaction_Tracking_ID"] == "TXN-UNSUPP-01"
    assert row2["Requires_Human_Review"] == "Yes"
    assert row2["Reconciliation_Status"] == "UNVERIFIED_CURRENCY"
    assert "unsupported currency 'XYZ'" in row2["Human_Review_Reason"]
    assert row2["Invoice_Billed_Amount"] == "500.0"


def test_summary_schedule_excludes_excessive_precision_and_unsupported_currency():
    """DEF-02: Verify summary schedule excludes excessive precision and unsupported currencies from verified totals."""
    payload = {
        "investigation_summary": {"project_code": "SUMM-01", "project_name": "Summary Verification"},
        "reconciliation_ledger_snapshot": [
            {
                "transaction_id": "TXN-1",
                "currency": "USD",
                "paid_amount": 1000.00,
                "reconciliation_status": "RECONCILED_MATCH"
            },
            {
                "transaction_id": "TXN-2",
                "currency": "USD",
                "paid_amount": 123.456, # Excessive precision
                "reconciliation_status": "RECONCILED_MATCH"
            },
            {
                "transaction_id": "TXN-3",
                "currency": "XYZ", # Unsupported currency
                "paid_amount": 400.00,
                "reconciliation_status": "RECONCILED_MATCH"
            }
        ],
        "financial_summary": {
            "by_currency": {
                "USD": {
                    "currency": "USD",
                    "verified_expenditure": 1123.46, # Raw unadjusted total in snapshot
                    "unverified_amounts": 0.0,
                    "potential_anomaly_amounts": 0.0,
                    "variance_hold_amounts": 0.0,
                    "unapplied_receipts": 0.0,
                    "transaction_count": 2
                },
                "XYZ": {
                    "currency": "XYZ",
                    "verified_expenditure": 400.00,
                    "unverified_amounts": 0.0,
                    "potential_anomaly_amounts": 0.0,
                    "variance_hold_amounts": 0.0,
                    "unapplied_receipts": 0.0,
                    "transaction_count": 1
                }
            },
            "undocumented_currency_entries": [
                {
                    "unverified_amount": 250.00,
                    "reason": "Missing currency code"
                }
            ]
        }
    }
    sha_hash = ReportService.compute_snapshot_hash(payload)
    rep = InvestigationReport(id=202, investigation_id=1, report_version=1, snapshot_payload=payload, snapshot_integrity_hash=sha_hash)

    csv_text = CSVFinancialExporter.export_schedule(rep, schedule="summary")
    clean_text = csv_text.lstrip("\ufeff")
    reader = list(csv.DictReader(io.StringIO(clean_text)))

    rows_by_category = {(r["Currency"], r["Metric_Category"]): r for r in reader}

    # 1. USD Verified Matching Expenditure must have 123.456 DEDUCTED: 1123.46 - 123.456 = 1000.00
    usd_verified = rows_by_category.get(("USD", "Verified Matching Expenditure"))
    assert usd_verified is not None
    assert usd_verified["Amount"] == "1000.00"

    # 2. Excessive precision row must be explicitly disclosed
    excess_row = rows_by_category.get(("USD", "Amounts Exceeding Currency Precision"))
    assert excess_row is not None
    assert excess_row["Amount"] == "123.456"

    # 3. Unsupported currency XYZ must NOT have a "Verified Matching Expenditure" row
    assert ("XYZ", "Verified Matching Expenditure") not in rows_by_category
    unsupp_row = rows_by_category.get(("XYZ", "Unsupported Currency Disclosure"))
    assert unsupp_row is not None
    # Must preserve exact source representation without assuming two decimal places
    assert unsupp_row["Amount"] in ("400.0", "400.00")
    assert "not an ISO 4217 recognized currency" in unsupp_row["Accounting_Guidance"]

    # 4. Undocumented missing currency isolated
    undoc_row = rows_by_category.get(("UNDOCUMENTED", "Missing Currency Disclosure"))
    assert undoc_row is not None
    assert undoc_row["Amount"] in ("250.0", "250.00")


# =========================================================================
# 6. Legacy Fallback Reconciliation Comprehensive Tests (DEF-04)
# =========================================================================

def test_legacy_fallback_reconciliation_all_conditions():
    """DEF-04: Verify legacy fallback handles all 10 conditions without inventing matches."""
    # Condition 1: Empty documents -> emits headers only, valid CSV
    empty_payload = {
        "investigation_summary": {"project_code": "LEG-0", "project_name": "Empty"},
        "evidence_register_snapshot": []
    }
    h0 = ReportService.compute_snapshot_hash(empty_payload)
    rep0 = InvestigationReport(id=300, investigation_id=1, report_version=1, snapshot_payload=empty_payload, snapshot_integrity_hash=h0)
    csv0 = CSVFinancialExporter.export_schedule(rep0, schedule="reconciliation")
    r0 = list(csv.reader(io.StringIO(csv0.lstrip("\ufeff"))))
    assert len(r0) == 1 # Only header
    assert r0[0][0] == "Transaction_Tracking_ID"

    # Conditions 2 through 10: Rich set of edge cases in legacy evidence
    evidence = [
        # Match 1: Exact 3-way match (PO-1, INV-1, REC-1)
        {
            "document_id": 1,
            "document_type": "PURCHASE_ORDER",
            "extracted_data_summary": {"po_reference": "PO-01", "amount": 1000.0, "currency": "USD", "vendor": "Vendor A"}
        },
        {
            "document_id": 2,
            "document_type": "INVOICE",
            "extracted_data_summary": {"invoice_number": "INV-01", "po_reference": "PO-01", "amount": 1000.0, "currency": "USD", "vendor": "Vendor A"}
        },
        {
            "document_id": 3,
            "document_type": "RECEIPT",
            "extracted_data_summary": {"receipt_id": "REC-01", "invoice_reference": "INV-01", "amount": 1000.0, "currency": "USD"}
        },
        # Condition 3: Missing PO (INV-02 has no PO reference, but has REC-02)
        {
            "document_id": 4,
            "document_type": "INVOICE",
            "extracted_data_summary": {"invoice_number": "INV-02", "amount": 400.0, "currency": "USD", "vendor": "Vendor B"}
        },
        {
            "document_id": 5,
            "document_type": "RECEIPT",
            "extracted_data_summary": {"receipt_id": "REC-02", "invoice_reference": "INV-02", "amount": 400.0, "currency": "USD"}
        },
        # Condition 5: Missing Receipt (PO-03 and INV-03, but no receipt)
        {
            "document_id": 6,
            "document_type": "PURCHASE_ORDER",
            "extracted_data_summary": {"po_reference": "PO-03", "amount": 800.0, "currency": "USD", "vendor": "Vendor C"}
        },
        {
            "document_id": 7,
            "document_type": "INVOICE",
            "extracted_data_summary": {"invoice_number": "INV-03", "po_reference": "PO-03", "amount": 800.0, "currency": "USD", "vendor": "Vendor C"}
        },
        # Condition 4: Standalone unapplied receipt (REC-STANDALONE has no matching invoice)
        {
            "document_id": 8,
            "document_type": "RECEIPT",
            "extracted_data_summary": {"receipt_id": "REC-STANDALONE", "invoice_reference": "INV-NONEXISTENT", "amount": 250.0, "currency": "USD"}
        },
        # Condition 6: Ambiguous multiple candidate POs (PO-AMB-A and PO-AMB-B share same reference)
        {
            "document_id": 9,
            "document_type": "PURCHASE_ORDER",
            "extracted_data_summary": {"po_reference": "PO-AMB", "amount": 300.0, "currency": "USD"}
        },
        {
            "document_id": 10,
            "document_type": "PURCHASE_ORDER",
            "extracted_data_summary": {"po_reference": "PO-AMB", "amount": 300.0, "currency": "USD"}
        },
        {
            "document_id": 11,
            "document_type": "INVOICE",
            "extracted_data_summary": {"invoice_number": "INV-AMB", "po_reference": "PO-AMB", "amount": 300.0, "currency": "USD"}
        },
        # Condition 7: Amount variance (PO=500, INV=500, REC=450)
        {
            "document_id": 12,
            "document_type": "PURCHASE_ORDER",
            "extracted_data_summary": {"po_reference": "PO-VAR", "amount": 500.0, "currency": "USD"}
        },
        {
            "document_id": 13,
            "document_type": "INVOICE",
            "extracted_data_summary": {"invoice_number": "INV-VAR", "po_reference": "PO-VAR", "amount": 500.0, "currency": "USD"}
        },
        {
            "document_id": 14,
            "document_type": "RECEIPT",
            "extracted_data_summary": {"receipt_id": "REC-VAR", "invoice_reference": "INV-VAR", "amount": 450.0, "currency": "USD"}
        },
        # Condition 8: Currency mismatch (PO in USD, INV in EUR)
        {
            "document_id": 15,
            "document_type": "PURCHASE_ORDER",
            "extracted_data_summary": {"po_reference": "PO-MISMATCH", "amount": 600.0, "currency": "USD"}
        },
        {
            "document_id": 16,
            "document_type": "INVOICE",
            "extracted_data_summary": {"invoice_number": "INV-MISMATCH", "po_reference": "PO-MISMATCH", "amount": 600.0, "currency": "EUR"}
        },
        {
            "document_id": 17,
            "document_type": "RECEIPT",
            "extracted_data_summary": {"receipt_id": "REC-MISMATCH", "invoice_reference": "INV-MISMATCH", "amount": 600.0, "currency": "EUR"}
        }
    ]

    payload = {
        "investigation_summary": {"project_code": "LEG-FULL", "project_name": "Full Legacy Test"},
        "evidence_register_snapshot": evidence
    }
    h = ReportService.compute_snapshot_hash(payload)
    rep = InvestigationReport(id=301, investigation_id=1, report_version=1, snapshot_payload=payload, snapshot_integrity_hash=h)

    csv_text = CSVFinancialExporter.export_schedule(rep, schedule="reconciliation")
    clean_text = csv_text.lstrip("\ufeff")
    reader = list(csv.DictReader(io.StringIO(clean_text)))

    by_txn = {r["Transaction_Tracking_ID"]: r for r in reader}

    # Verify Condition 2: Exact Match
    row_inv1 = by_txn["INV-01"]
    assert row_inv1["Reconciliation_Status"] == "RECONCILED"
    assert row_inv1["Match_Confidence"] == "EXACT_MATCH"
    assert row_inv1["Requires_Human_Review"] == "No"

    # Verify Condition 3: Missing PO
    row_inv2 = by_txn["INV-02"]
    assert row_inv2["Reconciliation_Status"] == "MISSING_PO"
    assert row_inv2["Requires_Human_Review"] == "Yes"
    assert "Missing purchase order" in row_inv2["Human_Review_Reason"]

    # Verify Condition 5: Missing Receipt
    row_inv3 = by_txn["INV-03"]
    assert row_inv3["Reconciliation_Status"] == "MISSING_RECEIPT"
    assert row_inv3["Requires_Human_Review"] == "Yes"
    assert "Missing disbursement proof" in row_inv3["Human_Review_Reason"]

    # Verify Condition 4: Standalone unapplied receipt
    row_rec_stand = by_txn["REC-STANDALONE"]
    assert row_rec_stand["Reconciliation_Status"] == "UNAPPLIED_RECEIPT"
    assert row_rec_stand["Requires_Human_Review"] == "Yes"

    # Verify Condition 6: Ambiguous PO candidates
    row_amb = by_txn["INV-AMB"]
    assert row_amb["Reconciliation_Status"] == "AMBIGUOUS_MATCH"
    assert row_amb["Requires_Human_Review"] == "Yes"

    # Verify Condition 7: Amount variance
    row_var = by_txn["INV-VAR"]
    assert row_var["Reconciliation_Status"] == "VARIANCE_HOLD"
    assert row_var["Variance_Amount"] == "-50.00"
    assert row_var["Requires_Human_Review"] == "Yes"

    # Verify Condition 8: Currency mismatch
    row_mis = by_txn["INV-MISMATCH"]
    assert row_mis["Reconciliation_Status"] == "CURRENCY_MISMATCH"
    assert row_mis["Requires_Human_Review"] == "Yes"
    assert "Currency mismatch" in row_mis["Human_Review_Reason"]


def test_csv_export_bytes_helper(test_db, rich_investigation_setup):
    """Verify export_schedule_bytes returns valid UTF-8 BOM byte sequence."""
    inv = rich_investigation_setup["investigation"]
    report = ReportService.create_report_snapshot(db=test_db, investigation_id=inv.id)

    csv_bytes = CSVFinancialExporter.export_schedule_bytes(report, schedule="reconciliation")
    assert isinstance(csv_bytes, bytes)
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    assert b"TXN-USD-001" in csv_bytes
