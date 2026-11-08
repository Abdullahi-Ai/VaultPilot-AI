import json
import hashlib
import hmac
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.investigation import Investigation
from app.models.finding import Finding
from app.models.document import Document
from app.models.ledger import EvidenceLedgerEntry
from app.models.report import InvestigationReport
from app.services.reconciliation_engine import normalize_currency

class ReportService:

    @staticmethod
    def create_report_snapshot(
        db: Session,
        investigation_id: int,
        title: Optional[str] = None,
        report_status: str = "FINAL"
    ) -> InvestigationReport:
        """
        Creates an immutable, point-in-time report snapshot for an investigation.
        Captures investigation summary, findings snapshot, evidence register,
        and currency-separated financial summaries.
        Computes a canonical SHA-256 integrity hash of the snapshot payload.
        """
        investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not investigation:
            raise ValueError(f"Investigation with ID {investigation_id} not found.")

        project = db.query(Project).filter(Project.id == investigation.project_id).first()
        if not project:
            raise ValueError(f"Project with ID {investigation.project_id} not found.")

        # Query all related records strictly bound to this investigation and project
        findings = db.query(Finding).filter(Finding.investigation_id == investigation.id).all()
        documents = db.query(Document).filter(Document.investigation_id == investigation.id).all()
        ledger_entries = db.query(EvidenceLedgerEntry).filter(EvidenceLedgerEntry.investigation_id == investigation.id).all()

        # Enforce cross-project safety check on all documents
        for doc in documents:
            if doc.project_id != project.id:
                raise ValueError(
                    f"Cross-project safety violation: Document '{doc.filename}' belongs to Project #{doc.project_id}, "
                    f"not Project #{project.id}. Cannot include in report."
                )

        # Version sequencing: determine next version for this investigation
        latest_report = db.query(InvestigationReport).filter(
            InvestigationReport.investigation_id == investigation.id
        ).order_by(InvestigationReport.report_version.desc()).first()

        next_version = (latest_report.report_version + 1) if latest_report else 1
        now_dt = datetime.datetime.utcnow()
        now_iso = now_dt.isoformat()

        # 1. Document counts by type
        doc_counts_by_type: Dict[str, int] = {}
        for doc in documents:
            doc_type = doc.document_type or "OTHER"
            doc_counts_by_type[doc_type] = doc_counts_by_type.get(doc_type, 0) + 1

        # 2. Financial Summary separated strictly by currency
        by_curr: Dict[str, Dict[str, Any]] = {}
        undocumented_currency_entries: List[Dict[str, Any]] = []
        ledger_ids: List[int] = []

        for entry in ledger_entries:
            ledger_ids.append(entry.id)
            norm_curr = normalize_currency(entry.currency)

            if not norm_curr:
                # Rule: Missing currency must never default to USD and never aggregate into verified totals
                undocumented_currency_entries.append({
                    "ledger_entry_id": entry.id,
                    "transaction_id": entry.transaction_id,
                    "unverified_amount": entry.paid_amount or entry.invoice_amount or entry.po_amount,
                    "reason": "Missing, unextracted, or non-standard currency code."
                })
                continue

            if norm_curr not in by_curr:
                by_curr[norm_curr] = {
                    "currency": norm_curr,
                    "verified_expenditure": 0.0,
                    "unverified_amounts": 0.0,
                    "potential_anomaly_amounts": 0.0,
                    "variance_hold_amounts": 0.0,
                    "unapplied_receipts": 0.0,
                    "transaction_count": 0
                }

            item = by_curr[norm_curr]
            item["transaction_count"] += 1

            status = entry.reconciliation_status
            paid = entry.paid_amount or 0.0
            billed = entry.invoice_amount or 0.0
            variance = entry.variance_amount or 0.0

            if status in ["RECONCILED_MATCH", "RECONCILED_WITH_VARIATION"]:
                item["verified_expenditure"] += paid
            elif status == "UNAPPLIED_RECEIPT":
                # Do not count unapplied receipts as verified expenditure
                item["unapplied_receipts"] += paid
            elif status == "VARIANCE_HOLD":
                # Do not treat variance hold as confirmed loss; record held variance
                item["variance_hold_amounts"] += (variance if variance > 0 else billed)
            elif status == "UNVERIFIED":
                item["unverified_amounts"] += (paid or billed)
            else:
                # E.g. PARTIAL_PAYMENT, MULTI_INVOICE_PO, MISSING_RECEIPT, MISSING_PO
                item["potential_anomaly_amounts"] += (variance if variance > 0 else billed)

        # Round all financial amounts to 2 decimal places
        for c, item in by_curr.items():
            for k in ["verified_expenditure", "unverified_amounts", "potential_anomaly_amounts", "variance_hold_amounts", "unapplied_receipts"]:
                item[k] = round(item[k], 2)

        financial_summary = {
            "by_currency": by_curr,
            "undocumented_currency_entries": undocumented_currency_entries,
            "underlying_ledger_entry_ids": sorted(ledger_ids)
        }

        # 3. Findings Snapshot
        findings_snapshot = []
        for f in findings:
            findings_snapshot.append({
                "finding_id": f.id,
                "classification": f.classification,
                "title": f.title,
                "subject_reference": f.subject_reference,
                "description": f.variance_explanation,
                "classification_rationale": f.classification_rationale,
                "expected_value": f.expected_value,
                "observed_value": f.observed_value,
                "variance_explanation": f.variance_explanation,
                "comparison_details": f.comparison_details or {},
                "source_paths": f.source_paths or [],
                "source_document_ids": f.source_document_ids or [],
                "evidence_limitations": f.evidence_limitations,
                "missing_evidence_details": f.missing_evidence_details,
                "requires_human_review": f.classification in ["POTENTIAL_ANOMALY", "UNVERIFIED", "MISSING_EVIDENCE"],
                "recommended_action": f.recommended_action
            })

        # 4. Evidence Register Snapshot
        evidence_register_snapshot = []
        for doc in documents:
            role = "SUPPORTING_EVIDENCE"
            if doc.document_type == "PURCHASE_ORDER": role = "AUTHORIZATION"
            elif doc.document_type == "INVOICE": role = "BILLING"
            elif doc.document_type == "RECEIPT": role = "DISBURSEMENT_PROOF"
            elif doc.document_type in ["FINANCIAL_REPORT", "EXPENSE_REPORT"]: role = "FINANCIAL_REPORT"

            linked_f_ids = [f.id for f in findings if doc.id in (f.source_document_ids or [])]

            evidence_register_snapshot.append({
                "document_id": doc.id,
                "investigation_id": doc.investigation_id,
                "project_id": doc.project_id,
                "filename": doc.filename,
                "source_path": doc.file_path,
                "document_type": doc.document_type,
                "extraction_status": doc.extraction_status,
                "extracted_data_summary": doc.extracted_data or {},
                "linked_finding_ids": sorted(linked_f_ids),
                "evidence_role": role,
                "evidence_limitations": "Optical degradation or unverified scan" if doc.extraction_status == "UNVERIFIED" else None
            })

        # 5. Reconciliation Ledger Snapshot
        ledger_snapshot = []
        for entry in ledger_entries:
            ledger_snapshot.append({
                "ledger_entry_id": entry.id,
                "transaction_id": entry.transaction_id,
                "item_description": entry.item_description or "General Item",
                "supplier_name": entry.supplier_name,
                "po_reference": entry.po_reference,
                "po_amount": entry.po_amount,
                "invoice_number": entry.invoice_number,
                "invoice_amount": entry.invoice_amount,
                "receipt_proof": entry.receipt_proof,
                "paid_amount": entry.paid_amount,
                "currency": entry.currency,
                "reconciliation_status": entry.reconciliation_status,
                "match_confidence": entry.match_confidence,
                "requires_human_review": entry.requires_human_review,
                "variance_amount": entry.variance_amount,
                "variance_reason": entry.variance_reason,
                "human_review_reason": entry.human_review_reason
            })

        # 6. Investigation Summary
        investigation_summary = {
            "project_id": project.id,
            "project_name": project.name,
            "project_code": project.code,
            "donor": project.donor,
            "investigation_id": investigation.id,
            "investigation_title": investigation.title,
            "investigation_scope": investigation.scope_path,
            "investigation_status": investigation.status,
            "document_count": len(documents),
            "document_counts_by_type": doc_counts_by_type,
            "generation_timestamp": now_iso
        }

        # 7. Complete Snapshot Payload
        snapshot_payload = {
            "metadata": {
                "schema_version": "1.0.0",
                "methodology_version": "VaultPilot-Audit-Methodology-2.0",
                "canonical_timestamp": now_iso,
                "investigation_id": investigation.id,
                "report_version": next_version
            },
            "investigation_summary": investigation_summary,
            "findings_snapshot": findings_snapshot,
            "evidence_register_snapshot": evidence_register_snapshot,
            "financial_summary": financial_summary,
            "reconciliation_ledger_snapshot": ledger_snapshot
        }

        # 8. Canonical Integrity Hash (SHA-256 of canonical JSON serialized bytes)
        integrity_hash = ReportService.compute_snapshot_hash(snapshot_payload)

        # Human review determination
        requires_review = (
            any(f["requires_human_review"] for f in findings_snapshot) or
            any(e.requires_human_review for e in ledger_entries) or
            len(undocumented_currency_entries) > 0
        )

        limitations_text = (
            f"Investigation scope is strictly limited to files discovered in '{investigation.scope_path}'. "
            "Findings reflect rule-guided reasoning over returned evidence. Absence of records in this directory "
            "does not establish that transactions did not occur outside the searched folder. "
            "Qualified human review is required before taking administrative or legal action."
        )

        report_title = title or f"Investigation Report v{next_version} — {investigation.title}"

        report = InvestigationReport(
            project_id=project.id,
            investigation_id=investigation.id,
            report_version=next_version,
            report_status=report_status,
            report_title=report_title,
            generation_timestamp=now_dt,
            reporting_schema_version="1.0.0",
            methodology_version="VaultPilot-Audit-Methodology-2.0",
            investigation_scope=investigation.scope_path,
            executive_summary=investigation.summary,
            financial_summary=financial_summary,
            investigation_limitations=limitations_text,
            requires_human_review=requires_review,
            snapshot_payload=snapshot_payload,
            snapshot_integrity_hash=integrity_hash,
            created_at=now_dt
        )

        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_report(db: Session, report_id: int) -> Optional[InvestigationReport]:
        """Retrieves a stored report snapshot by ID."""
        return db.query(InvestigationReport).filter(InvestigationReport.id == report_id).first()

    @staticmethod
    def list_reports_for_investigation(db: Session, investigation_id: int) -> List[InvestigationReport]:
        """Lists all report versions for a given investigation, ordered by version descending."""
        return db.query(InvestigationReport).filter(
            InvestigationReport.investigation_id == investigation_id
        ).order_by(InvestigationReport.report_version.desc()).all()

    @staticmethod
    def compute_snapshot_hash(snapshot_payload: Dict[str, Any]) -> str:
        """
        Computes the canonical SHA-256 integrity hash over a snapshot payload dictionary.
        Uses sorted keys, standard separators, and UTF-8 encoding.
        """
        canonical_bytes = json.dumps(
            snapshot_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True
        ).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()

    @staticmethod
    def verify_report_integrity(report: InvestigationReport) -> bool:
        """
        Cryptographically verifies the stored report snapshot payload against its recorded SHA-256 hash.
        Fails closed (returns False) if the report, snapshot_payload, or stored hash is missing or invalid,
        or if the recomputed canonical SHA-256 digest does not match the stored hash.
        """
        if not report or not report.snapshot_payload or not report.snapshot_integrity_hash:
            return False
        try:
            expected_hash = ReportService.compute_snapshot_hash(report.snapshot_payload)
            return hmac.compare_digest(expected_hash, report.snapshot_integrity_hash)
        except Exception:
            return False

    @staticmethod
    def get_report_markdown(db: Session, report_id: int) -> str:
        """
        Retrieves a stored report snapshot and renders it as an audit-grade Markdown dossier
        exclusively from the immutable snapshot_payload.
        """
        report = ReportService.get_report(db, report_id)
        if not report:
            raise ValueError(f"Report with ID {report_id} not found.")
        from app.services.markdown_renderer import MarkdownDossierRenderer
        return MarkdownDossierRenderer.render(report)

    @staticmethod
    def get_report_html(db: Session, report_id: int) -> str:
        """
        Retrieves a stored report snapshot and renders it as a publication-ready,
        printable HTML5 audit dossier exclusively from the immutable snapshot_payload.
        Enforces fail-closed cryptographic integrity verification before rendering.
        """
        report = ReportService.get_report(db, report_id)
        if not report:
            raise ValueError(f"Report with ID {report_id} not found.")
        from app.services.html_renderer import HTMLDossierRenderer
        return HTMLDossierRenderer.render(report)

    @staticmethod
    def get_report_csv(
        db: Session,
        report_id: int,
        schedule: str = "reconciliation",
        include_metadata_header: bool = False
    ) -> str:
        """
        Retrieves a stored report snapshot and exports a specified schedule as a CSV string
        exclusively from the immutable snapshot_payload.
        Enforces fail-closed cryptographic integrity verification before exporting.
        """
        report = ReportService.get_report(db, report_id)
        if not report:
            raise ValueError(f"Report with ID {report_id} not found.")
        from app.services.csv_exporter import CSVFinancialExporter
        return CSVFinancialExporter.export_schedule(
            report=report,
            schedule=schedule,
            include_metadata_header=include_metadata_header
        )
