import React, { useState } from 'react';
import { 
  TableProperties, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  FileSearch, 
  Filter, 
  Database, 
  Layers, 
  UserCheck, 
  Split, 
  Receipt, 
  FileSpreadsheet,
  AlertTriangle
} from 'lucide-react';
import { EvidenceLedgerEntry } from '../types';

interface EvidenceLedgerPageProps {
  entries: EvidenceLedgerEntry[];
}

export const EvidenceLedgerPage: React.FC<EvidenceLedgerPageProps> = ({ entries }) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const filteredEntries = filterStatus === 'ALL'
    ? entries
    : entries.filter(e => e.reconciliation_status === filterStatus);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RECONCILED_MATCH':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Reconciled Match</span>
          </span>
        );
      case 'RECONCILED_WITH_VARIATION':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Approved Variation</span>
          </span>
        );
      case 'PARTIAL_PAYMENT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Split className="w-3 h-3" />
            <span>Partial Payment</span>
          </span>
        );
      case 'MULTI_INVOICE_PO':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
            <Receipt className="w-3 h-3" />
            <span>Multi-Invoice (1:N)</span>
          </span>
        );
      case 'MULTI_RECEIPT_INVOICE':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
            <Split className="w-3 h-3" />
            <span>Multi-Receipt (1:N)</span>
          </span>
        );
      case 'VARIANCE_HOLD':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3 h-3" />
            <span>Variance Hold</span>
          </span>
        );
      case 'MISSING_RECEIPT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <FileSearch className="w-3 h-3" />
            <span>Missing Receipt Proof</span>
          </span>
        );
      case 'MISSING_PO':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-orange-50 text-orange-700 border border-orange-200">
            <AlertTriangle className="w-3 h-3" />
            <span>Missing PO</span>
          </span>
        );
      case 'UNAPPLIED_RECEIPT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <Receipt className="w-3 h-3" />
            <span>Unapplied Receipt</span>
          </span>
        );
      case 'UNVERIFIED':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <HelpCircle className="w-3 h-3" />
            <span>Unverified / Optical</span>
          </span>
        );
    }
  };

  const getConfidenceBadge = (confidence?: string) => {
    switch (confidence) {
      case 'EXACT_MATCH':
        return <span className="text-[10px] font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">EXACT MATCH</span>;
      case 'PROBABLE_MATCH':
        return <span className="text-[10px] font-bold bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">PROBABLE MATCH</span>;
      case 'PARTIAL_MATCH':
        return <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded">PARTIAL MATCH</span>;
      case 'CONFLICTING_EVIDENCE':
        return <span className="text-[10px] font-bold bg-rose-100 text-rose-800 px-2 py-0.5 rounded">CONFLICTING</span>;
      case 'UNMATCHED':
      default:
        return <span className="text-[10px] font-bold bg-slate-200 text-slate-700 px-2 py-0.5 rounded">UNMATCHED</span>;
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Multi-Source Financial Reconciliation Ledger</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Three-way documentary reconciliation: Purchase Orders ↔ Invoices ↔ Payment Proofs ↔ Financial Reports.
          </p>
        </div>

        {/* Filter bar */}
        <div className="flex items-center space-x-2 bg-white px-3 py-1.5 rounded-xl border border-slate-200 text-xs shadow-sm">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-500 font-medium">Filter:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-transparent font-semibold text-slate-800 focus:outline-none cursor-pointer"
          >
            <option value="ALL">All Entries ({entries.length})</option>
            <option value="RECONCILED_MATCH">Reconciled Match</option>
            <option value="RECONCILED_WITH_VARIATION">Approved Variation</option>
            <option value="PARTIAL_PAYMENT">Partial Payment</option>
            <option value="MULTI_INVOICE_PO">Multi-Invoice (1:N)</option>
            <option value="MULTI_RECEIPT_INVOICE">Multi-Receipt (1:N)</option>
            <option value="VARIANCE_HOLD">Variance Hold</option>
            <option value="MISSING_RECEIPT">Missing Receipt</option>
            <option value="MISSING_PO">Missing PO</option>
            <option value="UNAPPLIED_RECEIPT">Unapplied Receipt</option>
            <option value="UNVERIFIED">Unverified</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3.5">Txn / Investigation</th>
                <th className="px-4 py-3.5">Transaction & Vendor</th>
                <th className="px-4 py-3.5">PO (Expected Auth)</th>
                <th className="px-4 py-3.5">Invoice (Billed)</th>
                <th className="px-4 py-3.5">Payment (Supported Paid)</th>
                <th className="px-4 py-3.5">Match & Status</th>
                <th className="px-4 py-3.5">Variance / Review Required</th>
                <th className="px-4 py-3.5">Traceable Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                    <TableProperties className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <span>No ledger items found matching the selected filter.</span>
                  </td>
                </tr>
              ) : (
                filteredEntries.map((e) => {
                  const isDemo = e.id >= 100 || e.item_description.includes('[DEMO');
                  return (
                    <tr key={e.id} className="hover:bg-slate-50/60 transition-colors">
                      {/* Origin & Investigation */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="space-y-1">
                          <span className="font-mono text-[10px] font-bold text-slate-700 block">
                            {e.transaction_id || `TXN-${e.id}`}
                          </span>
                          <span className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full border border-slate-200 inline-flex items-center space-x-1">
                            <Layers className="w-2.5 h-2.5 text-slate-500" />
                            <span>Audit #{e.investigation_id}</span>
                          </span>
                          <div>
                            {isDemo ? (
                              <span className="text-[9px] font-bold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded border border-purple-200 block w-max">
                                DEMO FIXTURE
                              </span>
                            ) : (
                              <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 inline-flex items-center space-x-0.5">
                                <Database className="w-2 h-2" />
                                <span>DB #{e.id}</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Description & Vendor */}
                      <td className="px-4 py-4 font-bold text-slate-900 max-w-[160px]">
                        <div>{e.item_description}</div>
                        {e.supplier_name && (
                          <div className="text-[11px] text-slate-500 font-medium mt-0.5">
                            Vendor: <span className="text-slate-800">{e.supplier_name}</span>
                          </div>
                        )}
                        {e.project_report_reference && (
                          <div className="text-[10px] text-sky-700 flex items-center space-x-1 mt-1 font-semibold">
                            <FileSpreadsheet className="w-3 h-3" />
                            <span className="truncate">{e.project_report_reference}</span>
                          </div>
                        )}
                      </td>

                      {/* PO Column */}
                      <td className="px-4 py-4">
                        {e.po_reference ? (
                          <div className="space-y-0.5">
                            <div className="flex items-center space-x-1">
                              <span className="font-mono font-semibold text-slate-800">{e.po_reference}</span>
                              {e.po_document_id && (
                                <span className="text-[9px] font-mono bg-sky-50 text-sky-700 px-1 rounded border border-sky-200 font-bold">
                                  Doc #{e.po_document_id}
                                </span>
                              )}
                            </div>
                            <span className="text-slate-500 font-mono block">${e.po_amount?.toFixed(2)} {e.currency || 'N/A'}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">No PO Reference</span>
                        )}
                      </td>

                      {/* Invoice Column */}
                      <td className="px-4 py-4">
                        {e.invoice_number ? (
                          <div className="space-y-0.5">
                            <div className="flex items-center space-x-1">
                              <span className="font-mono font-semibold text-slate-800 truncate max-w-[110px]" title={e.invoice_number}>
                                {e.invoice_number}
                              </span>
                              {e.invoice_document_id && (
                                <span className="text-[9px] font-mono bg-sky-50 text-sky-700 px-1 rounded border border-sky-200 font-bold">
                                  Doc #{e.invoice_document_id}
                                </span>
                              )}
                            </div>
                            <span className="text-slate-900 font-mono font-bold block">${e.invoice_amount?.toFixed(2)} {e.currency || 'N/A'}</span>
                            {e.multiple_invoices_breakdown && e.multiple_invoices_breakdown.length > 1 && (
                              <span className="text-[9px] font-bold text-cyan-700 bg-cyan-50 px-1 rounded">
                                {e.multiple_invoices_breakdown.length} Invoices
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">No Invoice</span>
                        )}
                      </td>

                      {/* Receipt Column */}
                      <td className="px-4 py-4">
                        {e.receipt_proof ? (
                          <div className="space-y-0.5">
                            <div className="flex items-center space-x-1">
                              <span className="font-mono font-semibold text-slate-800 truncate max-w-[110px]" title={e.receipt_proof}>
                                {e.receipt_proof}
                              </span>
                              {e.receipt_document_id && (
                                <span className="text-[9px] font-mono bg-sky-50 text-sky-700 px-1 rounded border border-sky-200 font-bold">
                                  Doc #{e.receipt_document_id}
                                </span>
                              )}
                            </div>
                            {e.paid_amount !== null && e.paid_amount !== undefined ? (
                              <span className="text-emerald-700 font-mono font-bold block">${e.paid_amount.toFixed(2)} {e.currency || 'N/A'}</span>
                            ) : (
                              <span className="text-slate-400 text-[11px] italic block">Unverified Amount</span>
                            )}
                            {e.multiple_receipts_breakdown && e.multiple_receipts_breakdown.length > 1 && (
                              <span className="text-[9px] font-bold text-teal-700 bg-teal-50 px-1 rounded">
                                {e.multiple_receipts_breakdown.length} Receipts
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-amber-600 font-medium italic">Missing in scope</span>
                        )}
                      </td>

                      {/* Status & Confidence */}
                      <td className="px-4 py-4 space-y-1">
                        <div>{getStatusBadge(e.reconciliation_status)}</div>
                        <div>{getConfidenceBadge(e.match_confidence)}</div>
                      </td>

                      {/* Variance & Review Required */}
                      <td className="px-4 py-4 max-w-[170px]">
                        {e.requires_human_review ? (
                          <div className="bg-amber-50 p-2 rounded-xl border border-amber-200 space-y-1">
                            <span className="text-[10px] font-bold text-amber-800 flex items-center space-x-1">
                              <UserCheck className="w-3 h-3 text-amber-600" />
                              <span>Review Required</span>
                            </span>
                            <p className="text-[10px] text-amber-700 leading-tight">
                              {e.human_review_reason || e.variance_reason || 'Requires manual auditor verification.'}
                            </p>
                          </div>
                        ) : (
                          <div className="text-[11px] text-emerald-700 font-medium flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Reconciled Clean</span>
                          </div>
                        )}
                      </td>

                      {/* Traceable Source Documents */}
                      <td className="px-4 py-4 max-w-[200px]">
                        <div className="space-y-1">
                          {e.source_file_paths.map((p, idx) => {
                            const linkedDocId = e.source_document_ids && e.source_document_ids[idx];
                            return (
                              <div key={idx} className="font-mono text-[10px] text-slate-600 truncate bg-slate-50 px-2 py-0.5 rounded border border-slate-200/70 flex items-center justify-between" title={p}>
                                <span className="truncate">{p.split('/').pop()}</span>
                                {linkedDocId && (
                                  <span className="text-[9px] font-bold text-sky-700 ml-1">#{linkedDocId}</span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
