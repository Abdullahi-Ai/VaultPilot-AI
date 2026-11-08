import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class ReportCreateRequest(BaseModel):
    title: Optional[str] = None
    report_status: Optional[str] = "FINAL"

class FinancialSummaryCurrencyItem(BaseModel):
    currency: str
    verified_expenditure: float = 0.0
    unverified_amounts: float = 0.0
    potential_anomaly_amounts: float = 0.0
    variance_hold_amounts: float = 0.0
    unapplied_receipts: float = 0.0
    transaction_count: int = 0

class UndocumentedCurrencyEntry(BaseModel):
    ledger_entry_id: int
    transaction_id: Optional[str] = None
    unverified_amount: Optional[float] = None
    reason: str

class FinancialSummary(BaseModel):
    by_currency: Dict[str, FinancialSummaryCurrencyItem] = {}
    undocumented_currency_entries: List[UndocumentedCurrencyEntry] = []
    underlying_ledger_entry_ids: List[int] = []

class InvestigationReportSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    investigation_id: int
    report_version: int
    report_status: str
    report_title: str
    generation_timestamp: datetime.datetime
    reporting_schema_version: str
    methodology_version: str
    investigation_scope: str
    snapshot_integrity_hash: str
    requires_human_review: bool
    created_at: datetime.datetime

class InvestigationReportOut(InvestigationReportSummaryOut):
    executive_summary: Optional[str] = None
    financial_summary: Dict[str, Any] = {}
    investigation_limitations: Optional[str] = None
    snapshot_payload: Dict[str, Any]
