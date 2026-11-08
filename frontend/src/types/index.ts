export type FindingClassification = 
  | 'CONFIRMED_DISCREPANCY'
  | 'POTENTIAL_ANOMALY'
  | 'MISSING_EVIDENCE'
  | 'UNVERIFIED';

export type DataSourceState = 'LIVE_BACKEND' | 'DEMO_DATA' | 'BACKEND_OFFLINE';

export type ReconciliationStatus =
  | 'RECONCILED_MATCH'
  | 'VARIANCE_HOLD'
  | 'MISSING_RECEIPT'
  | 'MISSING_PO'
  | 'UNVERIFIED'
  | 'RECONCILED_WITH_VARIATION'
  | 'PARTIAL_PAYMENT'
  | 'MULTI_INVOICE_PO'
  | 'MULTI_RECEIPT_INVOICE'
  | 'UNAPPLIED_RECEIPT';

export interface DocumentRecord {
  id: number;
  project_id: number;
  investigation_id?: number;
  filename: string;
  file_path: string;
  document_type: string; // INVOICE, RECEIPT, PURCHASE_ORDER, etc.
  extraction_status: string;
  extracted_data?: Record<string, any>;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  code: string;
  donor?: string;
  budget: number;
  currency: string;
  nas_folder_path: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: number;
  investigation_id: number;
  title: string;
  classification: FindingClassification;
  subject_reference?: string;
  source_paths: string[];
  expected_value?: string;
  observed_value?: string;
  variance_explanation: string;
  recommended_action: string;
  created_at: string;

  // Phase 2.1 Traceability & Explainability
  source_document_ids?: number[];
  extracted_fields_used?: Record<string, any>;
  comparison_details?: Record<string, any>;
  evidence_limitations?: string;
  missing_evidence_details?: string;
  classification_rationale?: string;
  documents?: DocumentRecord[];
}

export interface EvidenceLedgerEntry {
  id: number;
  investigation_id: number;
  transaction_id?: string;
  item_description: string;
  supplier_name?: string;
  
  po_reference?: string;
  po_amount?: number;
  invoice_number?: string;
  invoice_amount?: number;
  receipt_proof?: string;
  receipt_amount?: number;
  paid_amount?: number;
  approved_variation_amount?: number;
  
  variance_amount?: number;
  variance_reason?: string;
  currency?: string | null;
  reconciliation_status: ReconciliationStatus;
  
  match_confidence?: 'EXACT_MATCH' | 'PROBABLE_MATCH' | 'PARTIAL_MATCH' | 'UNMATCHED' | 'CONFLICTING_EVIDENCE';
  requires_human_review?: boolean;
  human_review_reason?: string;
  
  multiple_invoices_breakdown?: Array<{ invoice_number?: string; amount?: number; currency?: string; doc_id?: number }>;
  multiple_receipts_breakdown?: Array<{ receipt_id?: string; amount?: number; currency?: string; doc_id?: number }>;
  project_report_reference?: string;
  report_reconciled?: boolean;
  
  source_file_paths: string[];
  created_at: string;

  // Phase 2.1 Traceability & Direct Relationships
  po_document_id?: number;
  invoice_document_id?: number;
  receipt_document_id?: number;
  source_document_ids?: number[];
  matching_criteria?: Record<string, any>;
  po_document?: DocumentRecord;
  invoice_document?: DocumentRecord;
  receipt_document?: DocumentRecord;
}

export interface Investigation {
  id: number;
  project_id: number;
  title: string;
  scope_path: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  summary?: string;
  verified_totals: Record<string, number>;
  document_count: number;
  created_at: string;
  completed_at?: string;
  findings: Finding[];
  ledger_entries: EvidenceLedgerEntry[];
  documents?: DocumentRecord[];
}

export interface InvestigationReportSummary {
  id: number;
  project_id: number;
  investigation_id: number;
  report_version: number;
  report_status: string;
  report_title: string;
  generation_timestamp: string;
  reporting_schema_version: string;
  methodology_version: string;
  investigation_scope: string;
  snapshot_integrity_hash: string;
  requires_human_review: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_projects: number;
  total_investigations: number;
  total_documents_analyzed: number;
  verified_spend_by_currency: Record<string, number>;
  findings_by_classification: {
    CONFIRMED_DISCREPANCY: number;
    POTENTIAL_ANOMALY: number;
    MISSING_EVIDENCE: number;
    UNVERIFIED: number;
  };
  ledger_status_breakdown: {
    RECONCILED_MATCH: number;
    VARIANCE_HOLD: number;
    MISSING_RECEIPT: number;
    MISSING_PO: number;
    UNVERIFIED: number;
  };
}
