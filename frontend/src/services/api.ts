import { Project, Investigation, Finding, EvidenceLedgerEntry, DashboardStats, DataSourceState, DocumentRecord, InvestigationReportSummary, FieldReview, FieldReviewAuditLog, DocumentReviewSummary } from '../types';

const API_BASE = '/api/v1';

// Clearly labeled demo/fallback fixtures with simulated provenance
export const DEMO_DOCUMENTS: DocumentRecord[] = [
  {
    id: 101,
    project_id: 1,
    investigation_id: 1,
    filename: "PO-2026-081.pdf",
    file_path: "/volume1/NGO_Projects/Solar_Water_2026/orders/PO-2026-081.pdf",
    document_type: "PURCHASE_ORDER",
    extraction_status: "EXTRACTED",
    extracted_data: { po_reference: "PO-2026-081", amount: 8500.0, currency: "USD", vendor: "SolarTech Global", date: "2026-02-10" },
    created_at: "2026-03-10T14:00:00Z"
  },
  {
    id: 102,
    project_id: 1,
    investigation_id: 1,
    filename: "INV-SP-1092.pdf",
    file_path: "/volume1/NGO_Projects/Solar_Water_2026/invoices/INV-SP-1092.pdf",
    document_type: "INVOICE",
    extraction_status: "EXTRACTED",
    extracted_data: { invoice_number: "INV-SP-1092", amount: 8500.0, currency: "USD", vendor: "SolarTech Global", date: "2026-02-24" },
    created_at: "2026-03-10T14:00:00Z"
  },
  {
    id: 103,
    project_id: 1,
    investigation_id: 1,
    filename: "REC-BNK-993.pdf",
    file_path: "/volume1/NGO_Projects/Solar_Water_2026/receipts/REC-BNK-993.pdf",
    document_type: "RECEIPT",
    extraction_status: "EXTRACTED",
    extracted_data: { receipt_id: "REC-BNK-993", amount: 8500.0, currency: "USD", payment_method: "WIRE_TRANSFER", date: "2026-03-01" },
    created_at: "2026-03-10T14:00:00Z"
  },
  {
    id: 104,
    project_id: 2,
    investigation_id: 1,
    filename: "PO-MED-441.pdf",
    file_path: "/volume1/NGO_Projects/Clinic_Rehab/orders/PO-MED-441.pdf",
    document_type: "PURCHASE_ORDER",
    extraction_status: "EXTRACTED",
    extracted_data: { po_reference: "PO-MED-441", amount: 18000.0, currency: "USD", vendor: "MedSupply International", date: "2026-02-15" },
    created_at: "2026-03-10T14:00:00Z"
  },
  {
    id: 105,
    project_id: 2,
    investigation_id: 1,
    filename: "INV-MED-7712.pdf",
    file_path: "/volume1/NGO_Projects/Clinic_Rehab/invoices/INV-MED-7712.pdf",
    document_type: "INVOICE",
    extraction_status: "EXTRACTED",
    extracted_data: { invoice_number: "INV-MED-7712", amount: 21500.0, currency: "USD", vendor: "MedSupply International", date: "2026-02-28" },
    created_at: "2026-03-10T14:00:00Z"
  }
];

export const DEMO_PROJECTS: Project[] = [
  {
    id: 1,
    name: "Solar Water Sanitation Initiative",
    code: "PRJ-WASH-2026",
    donor: "Global Humanitarian Water Fund",
    budget: 50000.0,
    currency: "USD",
    nas_folder_path: "/volume1/NGO_Projects/Solar_Water_2026",
    description: "Community clean water solar pump installation across rural primary schools.",
    created_at: "2026-03-01T09:00:00Z",
    updated_at: "2026-03-01T09:00:00Z",
  },
  {
    id: 2,
    name: "Rural Mobile Health Clinic",
    code: "PRJ-MED-2026",
    donor: "International Health Partnership",
    budget: 75000.0,
    currency: "USD",
    nas_folder_path: "/volume1/NGO_Projects/Clinic_Rehab",
    description: "Mobile clinical outreach units and basic pharmaceutical supplies.",
    created_at: "2026-03-05T11:30:00Z",
    updated_at: "2026-03-05T11:30:00Z",
  }
];

export const DEMO_FINDINGS: Finding[] = [
  {
    id: 1,
    investigation_id: 1,
    title: "Billed Amount Exceeds Purchase Order Authorization",
    classification: "CONFIRMED_DISCREPANCY",
    subject_reference: "PO-MED-441 / INV-MED-7712",
    source_paths: [
      "/volume1/NGO_Projects/Clinic_Rehab/orders/PO-MED-441.pdf",
      "/volume1/NGO_Projects/Clinic_Rehab/invoices/INV-MED-7712.pdf"
    ],
    expected_value: "PO Authorization: 18,000.00 USD",
    observed_value: "Invoiced Billing: 21,500.00 USD (+3,500.00 variance)",
    variance_explanation: "Invoice bills 21,500.00 USD exceeding PO of 18,000.00 USD. Exhaustive search confirmed no amendment exists in the repository.",
    recommended_action: "Procurement officer must confirm whether an approved PO amendment was issued outside this repository.",
    created_at: "2026-03-10T14:00:00Z",
    source_document_ids: [104, 105],
    extracted_fields_used: {
      "PO-MED-441": { amount: 18000.0, currency: "USD", field: "amount" },
      "INV-MED-7712": { amount: 21500.0, currency: "USD", field: "amount" }
    },
    comparison_details: {
      po_authorized_amount: 18000.0,
      invoiced_amount: 21500.0,
      unauthorized_variance: 3500.0,
      currency: "USD",
      calculation: "21500.00 - 18000.00 = +3500.00 USD"
    },
    evidence_limitations: "Demonstration fixture. Scoped to simulated path '/volume1/NGO_Projects/Clinic_Rehab'.",
    missing_evidence_details: "Approved variation order or PO amendment covering the +$3,500.00 delta.",
    classification_rationale: "Classified as CONFIRMED_DISCREPANCY because all scoped records were evaluated and no amendment exists in repo."
  },
  {
    id: 2,
    investigation_id: 1,
    title: "Fast Billing Window - Vendor Prompt Invoicing",
    classification: "POTENTIAL_ANOMALY",
    subject_reference: "PO-2026-081 vs INV-SP-1092",
    source_paths: [
      "/volume1/NGO_Projects/Solar_Water_2026/orders/PO-2026-081.pdf",
      "/volume1/NGO_Projects/Solar_Water_2026/invoices/INV-SP-1092.pdf"
    ],
    expected_value: "Standard 30-day billing interval",
    observed_value: "14-day interval from PO authorization",
    variance_explanation: "Invoice submitted 14 days after purchase order issuance. Deviates from typical 30-day cycle. Note: Anomaly indicator, not misconduct.",
    recommended_action: "Verify goods delivery confirmation date with logistics team.",
    created_at: "2026-03-10T14:05:00Z",
    source_document_ids: [101, 102],
    extracted_fields_used: {
      "PO-2026-081": { date: "2026-02-10", po_amount: 8500.0, currency: "USD" },
      "INV-SP-1092": { date: "2026-02-24", invoice_amount: 8500.0, currency: "USD" }
    },
    comparison_details: {
      metric: "billing_turnaround_days",
      observed_interval: 14,
      standard_interval: 30,
      variance_days: -16
    },
    evidence_limitations: "Demonstration fixture. Central logistics delivery logs were not inspected.",
    missing_evidence_details: "Goods received note or field delivery slip confirming delivery date.",
    classification_rationale: "Classified as POTENTIAL_ANOMALY because rapid turnaround warrants delivery date check; no financial discrepancy."
  },
  {
    id: 3,
    investigation_id: 1,
    title: "Missing Disbursement Proof for Commercial Invoice",
    classification: "MISSING_EVIDENCE",
    subject_reference: "INV-UNSUPP-902",
    source_paths: [
      "/volume1/NGO_Projects/Solar_Water_2026/invoices/INV-UNSUPP-902.pdf"
    ],
    expected_value: "Payment Receipt / Bank Remittance Voucher",
    observed_value: "Invoice exists without payment record in scoped directory",
    variance_explanation: "Invoice has no payment slip or receipt in searched folder. Note: This indicates the record was not located in this directory, not that payment did not occur.",
    recommended_action: "Check central finance repository for archived bank slip.",
    created_at: "2026-03-10T14:10:00Z",
    source_document_ids: [],
    extracted_fields_used: { invoice_number: "INV-UNSUPP-902", amount: 4200.0, currency: "USD" },
    comparison_details: { invoice_amount: 4200.0, payment_proof_found: false },
    evidence_limitations: "Scoped strictly to searched directory. Does not prove payment was not made externally.",
    missing_evidence_details: "Bank wire slip or signed voucher.",
    classification_rationale: "Classified as MISSING_EVIDENCE because commercial invoices require proof of payment."
  },
  {
    id: 4,
    investigation_id: 1,
    title: "Illegible Receipt Scan - Extraction Unverified",
    classification: "UNVERIFIED",
    subject_reference: "IMG_7781_blurry.jpg",
    source_paths: [
      "/volume1/NGO_Projects/Solar_Water_2026/receipts/IMG_7781_blurry.jpg"
    ],
    expected_value: "Readable numerical amount & date",
    observed_value: "Unreadable / Smudged optical data",
    variance_explanation: "Receipt photo contains smudged numbers and low optical resolution. Amount remains unverified.",
    recommended_action: "Obtain high-resolution scan or manual confirmation from field team.",
    created_at: "2026-03-10T14:15:00Z",
    source_document_ids: [],
    extracted_fields_used: { optical_status: "SMUDGED" },
    comparison_details: { ocr_status: "failed", legible: false },
    evidence_limitations: "Optical blur prevents confident data extraction.",
    missing_evidence_details: "Legible high-resolution re-scan.",
    classification_rationale: "Classified as UNVERIFIED because financial numbers cannot be read with confidence."
  }
];

export const DEMO_LEDGER_ENTRIES: EvidenceLedgerEntry[] = [
  {
    id: 1,
    investigation_id: 1,
    transaction_id: "TXN-DEMO-01",
    supplier_name: "SunPower Ltd",
    item_description: "Solar Inverter Components & Wiring",
    po_reference: "PO-2026-081",
    po_amount: 8500.0,
    invoice_number: "INV-SP-1092",
    invoice_amount: 8500.0,
    receipt_proof: "REC-BNK-993",
    receipt_amount: 8500.0,
    paid_amount: 8500.0,
    currency: "USD",
    reconciliation_status: "RECONCILED_MATCH",
    match_confidence: "EXACT_MATCH",
    requires_human_review: false,
    source_file_paths: [
      "/volume1/NGO_Projects/Solar_Water_2026/orders/PO-2026-081.pdf",
      "/volume1/NGO_Projects/Solar_Water_2026/invoices/INV-SP-1092.pdf",
      "/volume1/NGO_Projects/Solar_Water_2026/receipts/REC-BNK-993.pdf"
    ],
    po_document_id: 101,
    invoice_document_id: 102,
    receipt_document_id: 103,
    source_document_ids: [101, 102, 103],
    matching_criteria: { matched_by: "EXACT_MATCH", po_number: "PO-2026-081", invoice_number: "INV-SP-1092" },
    created_at: "2026-03-10T14:00:00Z"
  },
  {
    id: 2,
    investigation_id: 1,
    transaction_id: "TXN-DEMO-02",
    supplier_name: "MedSupply Co",
    item_description: "Adjustable Clinic Beds Batch 1",
    po_reference: "PO-MED-441",
    po_amount: 18000.0,
    invoice_number: "INV-MED-7712",
    invoice_amount: 21500.0,
    receipt_proof: "VOUCH-331",
    receipt_amount: 21500.0,
    paid_amount: 21500.0,
    variance_amount: 3500.0,
    variance_reason: "Invoiced billing exceeds approved PO authorization by +3,500.00 USD.",
    currency: "USD",
    reconciliation_status: "VARIANCE_HOLD",
    match_confidence: "EXACT_MATCH",
    requires_human_review: true,
    human_review_reason: "Unsubstantiated billing variance exceeding approved purchase order limit.",
    source_file_paths: [
      "/volume1/NGO_Projects/Clinic_Rehab/orders/PO-MED-441.pdf",
      "/volume1/NGO_Projects/Clinic_Rehab/invoices/INV-MED-7712.pdf",
      "/volume1/NGO_Projects/Clinic_Rehab/receipts/VOUCH-331.pdf"
    ],
    po_document_id: 104,
    invoice_document_id: 105,
    source_document_ids: [104, 105],
    matching_criteria: { matched_by: "EXACT_MATCH", po_number: "PO-MED-441", invoice_number: "INV-MED-7712" },
    created_at: "2026-03-10T14:00:00Z"
  }
];

export const DEMO_INVESTIGATIONS: Investigation[] = [
  {
    id: 1,
    project_id: 1,
    title: "Routine Financial Evidence Audit - Q1 2026",
    scope_path: "/volume1/NGO_Projects/Solar_Water_2026",
    status: "COMPLETED",
    summary: "Analyzed 8 documents across 4 transactions. Identified 1 Confirmed Discrepancy, 1 Potential Anomaly, 1 Missing Evidence, 1 Unverified Record. Total verified spend: $8,500.00 USD.",
    verified_totals: { USD: 8500.0 },
    document_count: 8,
    created_at: "2026-03-10T13:45:00Z",
    completed_at: "2026-03-10T13:46:12Z",
    findings: DEMO_FINDINGS,
    ledger_entries: DEMO_LEDGER_ENTRIES
  }
];

export const DEMO_DASHBOARD_STATS: DashboardStats = {
  total_projects: 2,
  total_investigations: 1,
  total_documents_analyzed: 8,
  verified_spend_by_currency: { USD: 8500.0 },
  findings_by_classification: {
    CONFIRMED_DISCREPANCY: 1,
    POTENTIAL_ANOMALY: 1,
    MISSING_EVIDENCE: 1,
    UNVERIFIED: 1,
  },
  ledger_status_breakdown: {
    RECONCILED_MATCH: 1,
    VARIANCE_HOLD: 1,
    MISSING_RECEIPT: 1,
    MISSING_PO: 0,
    UNVERIFIED: 1,
  }
};

// Application Data-Source State Management
let currentDataSourceState: DataSourceState = 'LIVE_BACKEND';
let isManualDemoMode = false;
const listeners = new Set<(state: DataSourceState) => void>();

function updateState(newState: DataSourceState) {
  if (currentDataSourceState !== newState) {
    currentDataSourceState = newState;
    listeners.forEach(fn => fn(newState));
  }
}

export const apiService = {
  getDataSourceState(): DataSourceState {
    return isManualDemoMode ? 'DEMO_DATA' : currentDataSourceState;
  },

  isDemoModeActive(): boolean {
    return isManualDemoMode || currentDataSourceState === 'DEMO_DATA';
  },

  setDemoMode(enabled: boolean): void {
    isManualDemoMode = enabled;
    if (enabled) {
      updateState('DEMO_DATA');
    } else {
      this.checkBackendHealth();
    }
  },

  subscribeToDataSource(listener: (state: DataSourceState) => void): () => void {
    listeners.add(listener);
    listener(this.getDataSourceState());
    return () => listeners.delete(listener);
  },

  async checkBackendHealth(): Promise<DataSourceState> {
    if (isManualDemoMode) {
      updateState('DEMO_DATA');
      return 'DEMO_DATA';
    }
    try {
      const res = await fetch('/');
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return 'LIVE_BACKEND';
      } else {
        updateState('BACKEND_OFFLINE');
        return 'BACKEND_OFFLINE';
      }
    } catch {
      updateState('BACKEND_OFFLINE');
      return 'BACKEND_OFFLINE';
    }
  },

  async getDashboardStats(): Promise<DashboardStats> {
    if (isManualDemoMode) {
      return DEMO_DASHBOARD_STATS;
    }
    try {
      const res = await fetch(`${API_BASE}/dashboard/stats`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    return DEMO_DASHBOARD_STATS;
  },

  async getProjects(): Promise<Project[]> {
    if (isManualDemoMode) {
      return DEMO_PROJECTS;
    }
    try {
      const res = await fetch(`${API_BASE}/projects/`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    return DEMO_PROJECTS;
  },

  async createProject(project: Partial<Project>): Promise<Project> {
    if (isManualDemoMode || currentDataSourceState === 'BACKEND_OFFLINE') {
      const demoNew: Project = {
        id: Date.now(),
        name: project.name || "New Grant Project [DEMO FIXTURE]",
        code: project.code || `PRJ-${Date.now().toString().slice(-4)}`,
        donor: project.donor || "Demonstration Donor",
        budget: project.budget || 10000,
        currency: project.currency || "USD",
        nas_folder_path: project.nas_folder_path || "/volume1/NGO_Projects/Demo",
        description: project.description || "Demo mode project created in browser memory.",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      DEMO_PROJECTS.unshift(demoNew);
      return demoNew;
    }

    try {
      const res = await fetch(`${API_BASE}/projects/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(project)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to create project' }));
        throw new Error(err.detail || 'Failed to create project');
      }
      updateState('LIVE_BACKEND');
      return await res.json();
    } catch (e: any) {
      updateState('BACKEND_OFFLINE');
      throw e;
    }
  },

  async getInvestigations(projectId?: number): Promise<Investigation[]> {
    if (isManualDemoMode) {
      return projectId ? DEMO_INVESTIGATIONS.filter(i => i.project_id === projectId) : DEMO_INVESTIGATIONS;
    }
    try {
      const url = projectId ? `${API_BASE}/investigations/?project_id=${projectId}` : `${API_BASE}/investigations/`;
      const res = await fetch(url);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    return DEMO_INVESTIGATIONS;
  },

  async triggerInvestigation(projectId: number, folderPath: string, title?: string): Promise<Investigation> {
    if (isManualDemoMode || currentDataSourceState === 'BACKEND_OFFLINE') {
      const demoInv: Investigation = {
        id: Date.now(),
        project_id: projectId,
        title: title || "Simulated Demo Audit [DEMO FIXTURE]",
        scope_path: folderPath,
        status: "COMPLETED",
        summary: "Simulated Demo Investigation completed over sample documents.",
        verified_totals: { USD: 8500.0 },
        document_count: 8,
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        findings: DEMO_FINDINGS,
        ledger_entries: DEMO_LEDGER_ENTRIES
      };
      DEMO_INVESTIGATIONS.unshift(demoInv);
      return demoInv;
    }

    try {
      const res = await fetch(`${API_BASE}/investigations/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          folder_path: folderPath,
          title: title || "Routine Project Evidence Audit"
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to trigger investigation' }));
        throw new Error(err.detail || 'Failed to trigger investigation');
      }
      updateState('LIVE_BACKEND');
      return await res.json();
    } catch (e: any) {
      updateState('BACKEND_OFFLINE');
      throw e;
    }
  },

  async getFindings(investigationId?: number, classification?: string): Promise<Finding[]> {
    if (isManualDemoMode) {
      let filtered = DEMO_FINDINGS;
      if (investigationId) filtered = filtered.filter(f => f.investigation_id === investigationId);
      if (classification) filtered = filtered.filter(f => f.classification === classification);
      return filtered;
    }
    try {
      const params = new URLSearchParams();
      if (investigationId) params.append('investigation_id', investigationId.toString());
      if (classification) params.append('classification', classification);
      const res = await fetch(`${API_BASE}/findings/?${params.toString()}`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    return DEMO_FINDINGS;
  },

  async getFindingDetail(findingId: number): Promise<Finding> {
    if (isManualDemoMode) {
      const found = DEMO_FINDINGS.find(f => f.id === findingId) || DEMO_FINDINGS[0];
      return {
        ...found,
        documents: DEMO_DOCUMENTS.filter(d => found.source_document_ids?.includes(d.id))
      };
    }
    try {
      const res = await fetch(`${API_BASE}/findings/${findingId}`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    const found = DEMO_FINDINGS.find(f => f.id === findingId) || DEMO_FINDINGS[0];
    return {
      ...found,
      documents: DEMO_DOCUMENTS.filter(d => found.source_document_ids?.includes(d.id))
    };
  },

  async getLedgerEntries(investigationId?: number, status?: string): Promise<EvidenceLedgerEntry[]> {
    if (isManualDemoMode) {
      let filtered = DEMO_LEDGER_ENTRIES;
      if (investigationId) filtered = filtered.filter(l => l.investigation_id === investigationId);
      if (status) filtered = filtered.filter(l => l.reconciliation_status === status);
      return filtered;
    }
    try {
      const params = new URLSearchParams();
      if (investigationId) params.append('investigation_id', investigationId.toString());
      if (status) params.append('reconciliation_status', status);
      const res = await fetch(`${API_BASE}/ledger/?${params.toString()}`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    return DEMO_LEDGER_ENTRIES;
  },

  async getLedgerEntryDetail(entryId: number): Promise<EvidenceLedgerEntry> {
    if (isManualDemoMode) {
      const found = DEMO_LEDGER_ENTRIES.find(l => l.id === entryId) || DEMO_LEDGER_ENTRIES[0];
      return {
        ...found,
        po_document: DEMO_DOCUMENTS.find(d => d.id === found.po_document_id),
        invoice_document: DEMO_DOCUMENTS.find(d => d.id === found.invoice_document_id),
        receipt_document: DEMO_DOCUMENTS.find(d => d.id === found.receipt_document_id)
      };
    }
    try {
      const res = await fetch(`${API_BASE}/ledger/${entryId}`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    const found = DEMO_LEDGER_ENTRIES.find(l => l.id === entryId) || DEMO_LEDGER_ENTRIES[0];
    return {
      ...found,
      po_document: DEMO_DOCUMENTS.find(d => d.id === found.po_document_id),
      invoice_document: DEMO_DOCUMENTS.find(d => d.id === found.invoice_document_id),
      receipt_document: DEMO_DOCUMENTS.find(d => d.id === found.receipt_document_id)
    };
  },

  async getDocuments(projectId?: number, investigationId?: number): Promise<DocumentRecord[]> {
    if (isManualDemoMode) {
      return DEMO_DOCUMENTS;
    }
    try {
      const params = new URLSearchParams();
      if (projectId) params.append('project_id', projectId.toString());
      if (investigationId) params.append('investigation_id', investigationId.toString());
      const res = await fetch(`${API_BASE}/documents/?${params.toString()}`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    return DEMO_DOCUMENTS;
  },

  async getInvestigationReports(investigationId: number): Promise<InvestigationReportSummary[]> {
    if (isManualDemoMode) {
      return [
        {
          id: 1,
          project_id: 1,
          investigation_id: investigationId,
          report_version: 1,
          report_status: 'FINAL',
          report_title: 'Simulated Demo Audit Dossier [DEMO FIXTURE]',
          generation_timestamp: new Date().toISOString(),
          reporting_schema_version: '1.0.0',
          methodology_version: 'VaultPilot-Audit-Methodology-2.0',
          investigation_scope: '/volume1/NGO_Projects/Demo',
          snapshot_integrity_hash: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
          requires_human_review: false,
          created_at: new Date().toISOString()
        }
      ];
    }
    try {
      const res = await fetch(`${API_BASE}/investigations/${investigationId}/reports`);
      if (res.ok) {
        updateState('LIVE_BACKEND');
        return await res.json();
      }
    } catch {
      updateState('BACKEND_OFFLINE');
    }
    return [];
  },

  async createInvestigationReport(investigationId: number, title?: string): Promise<InvestigationReportSummary> {
    if (isManualDemoMode || currentDataSourceState === 'BACKEND_OFFLINE') {
      return {
        id: Date.now(),
        project_id: 1,
        investigation_id: investigationId,
        report_version: 1,
        report_status: 'FINAL',
        report_title: title || 'Financial Evidence Audit Dossier',
        generation_timestamp: new Date().toISOString(),
        reporting_schema_version: '1.0.0',
        methodology_version: 'VaultPilot-Audit-Methodology-2.0',
        investigation_scope: '/volume1/NGO_Projects/Demo',
        snapshot_integrity_hash: 'demo_sha256_hash_sealed_snapshot_payload_000000000000000000000000',
        requires_human_review: false,
        created_at: new Date().toISOString()
      };
    }
    const res = await fetch(`${API_BASE}/investigations/${investigationId}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title || 'Official Investigation Audit Dossier', report_status: 'FINAL' })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create report snapshot' }));
      throw new Error(err.detail || 'Failed to create report snapshot');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  getReportHtmlUrl(investigationId: number, reportId: number): string {
    return `${API_BASE}/investigations/${investigationId}/reports/${reportId}/html`;
  },

  getReportCsvUrl(investigationId: number, reportId: number, schedule: string = 'reconciliation'): string {
    return `${API_BASE}/investigations/${investigationId}/reports/${reportId}/csv?schedule=${encodeURIComponent(schedule)}`;
  },

  getReportMarkdownUrl(investigationId: number, reportId: number): string {
    return `${API_BASE}/investigations/${investigationId}/reports/${reportId}/markdown`;
  },

  // ==========================================
  // Phase 3.3 Evidence Review & Human Verification
  // ==========================================

  async getPendingReviews(params?: { projectId?: number; investigationId?: number; status?: string }): Promise<FieldReview[]> {
    const query = new URLSearchParams();
    if (params?.projectId) query.append('project_id', params.projectId.toString());
    if (params?.investigationId) query.append('investigation_id', params.investigationId.toString());
    if (params?.status) query.append('status', params.status);

    const res = await fetch(`${API_BASE}/reviews/pending?${query.toString()}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch pending reviews: ${res.statusText}`);
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async getDocumentReviewSummary(documentId: number): Promise<DocumentReviewSummary> {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Failed to fetch document ${documentId} review summary` }));
      throw new Error(err.detail || `Failed to fetch document ${documentId} review summary`);
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async initializeDocumentReviews(documentId: number): Promise<FieldReview[]> {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/initialize`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to initialize reviews' }));
      throw new Error(err.detail || 'Failed to initialize reviews');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async getDocumentReviewHistory(documentId: number): Promise<FieldReviewAuditLog[]> {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/history`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch review history' }));
      throw new Error(err.detail || 'Failed to fetch review history');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async getFieldReview(documentId: number, fieldName: string): Promise<FieldReview> {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/${encodeURIComponent(fieldName)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Field '${fieldName}' not found` }));
      throw new Error(err.detail || `Field '${fieldName}' not found`);
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async verifyField(documentId: number, fieldName: string, notes?: string, reviewerId?: string): Promise<FieldReview> {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/${encodeURIComponent(fieldName)}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes, reviewer_id: reviewerId })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to verify field' }));
      throw new Error(err.detail || 'Failed to verify field');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async correctField(documentId: number, fieldName: string, correctedValue: any, notes?: string, reviewerId?: string): Promise<FieldReview> {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/${encodeURIComponent(fieldName)}/correct`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrected_value: correctedValue, notes, reviewer_id: reviewerId })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to correct field' }));
      throw new Error(err.detail || 'Failed to correct field');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async rejectField(documentId: number, fieldName: string, reason: string, reviewerId?: string): Promise<FieldReview> {
    if (!reason || !reason.trim()) {
      throw new Error('Rejection requires a mandatory audit reason.');
    }
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/${encodeURIComponent(fieldName)}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: reason.trim(), reviewer_id: reviewerId })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to reject field' }));
      throw new Error(err.detail || 'Failed to reject field');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async clarifyField(documentId: number, fieldName: string, question: string, reviewerId?: string): Promise<FieldReview> {
    if (!question || !question.trim()) {
      throw new Error('Clarification request requires a mandatory inquiry question.');
    }
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/${encodeURIComponent(fieldName)}/clarify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clarification_question: question.trim(), reviewer_id: reviewerId })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to request clarification' }));
      throw new Error(err.detail || 'Failed to request clarification');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async reconcileInvestigation(investigationId: number): Promise<Investigation> {
    const res = await fetch(`${API_BASE}/investigations/${investigationId}/reconcile`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to re-evaluate reconciliation' }));
      throw new Error(err.detail || 'Failed to re-evaluate reconciliation');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  },

  async reconcileDocument(documentId: number): Promise<{ status: string; investigation_id: number; document_id: number; verified_totals: Record<string, number>; summary: string }> {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reconcile`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to re-evaluate reconciliation for document' }));
      throw new Error(err.detail || 'Failed to re-evaluate reconciliation for document');
    }
    updateState('LIVE_BACKEND');
    return await res.json();
  }
};
