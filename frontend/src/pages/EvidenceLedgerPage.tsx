import React, { useState } from 'react';
import {
  TableProperties,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  FileSearch,
  Filter,
  Layers,
  Split,
  AlertTriangle
} from 'lucide-react';
import { EvidenceLedgerEntry } from '../types';
import { EvidenceReviewDrawer } from '../components/EvidenceReviewDrawer';

interface EvidenceLedgerPageProps {
  entries: EvidenceLedgerEntry[];
}

export const EvidenceLedgerPage: React.FC<EvidenceLedgerPageProps> = ({ entries }) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [activeReviewDocId] = useState<number | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const filteredEntries = filterStatus === 'ALL'
    ? entries
    : entries.filter(e => e.reconciliation_status === filterStatus);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RECONCILED_MATCH':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Reconciled Match</span>
          </span>
        );
      case 'RECONCILED_WITH_VARIATION':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase bg-purple-50 text-purple-700 border border-purple-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Approved Variation</span>
          </span>
        );
      case 'PARTIAL_PAYMENT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase bg-blue-50 text-blue-700 border border-blue-200">
            <Split className="w-3 h-3" />
            <span>Partial Payment</span>
          </span>
        );
      case 'VARIANCE_HOLD':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3 h-3" />
            <span>Variance Hold</span>
          </span>
        );
      case 'MISSING_RECEIPT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-200">
            <FileSearch className="w-3 h-3" />
            <span>Missing Receipt</span>
          </span>
        );
      case 'MISSING_PO':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase bg-rose-50 text-rose-700 border border-rose-200">
            <AlertTriangle className="w-3 h-3" />
            <span>Missing PO Auth</span>
          </span>
        );
      case 'UNVERIFIED':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
            <HelpCircle className="w-3 h-3" />
            <span>Unverified</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            3-Way Evidence Reconciliation Ledger
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Documentary cross-examination: Purchase Orders ↔ Invoices ↔ Disbursement Proofs.
          </p>
        </div>

        {/* Filter Dropdown */}
        <div className="flex items-center space-x-2 bg-white px-3.5 py-2 rounded-xl border border-slate-200/90 text-xs shadow-xs shrink-0">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-slate-500 font-semibold uppercase tracking-wider text-[11px]">Filter:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-transparent font-bold text-slate-900 focus:outline-none cursor-pointer"
          >
            <option value="ALL">All Entries ({entries.length})</option>
            <option value="RECONCILED_MATCH">Reconciled Match</option>
            <option value="VARIANCE_HOLD">Variance Hold</option>
            <option value="MISSING_RECEIPT">Missing Receipt</option>
            <option value="MISSING_PO">Missing PO</option>
            <option value="UNVERIFIED">Unverified</option>
          </select>
        </div>
      </div>

      {/* Filter Quick Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto no-scrollbar pb-1 text-xs">
        {[
          { id: 'ALL', label: `All (${entries.length})` },
          { id: 'RECONCILED_MATCH', label: 'Reconciled Match' },
          { id: 'VARIANCE_HOLD', label: 'Variance Hold' },
          { id: 'MISSING_RECEIPT', label: 'Missing Receipt' },
          { id: 'UNVERIFIED', label: 'Unverified' },
        ].map(pill => (
          <button
            key={pill.id}
            onClick={() => setFilterStatus(pill.id)}
            className={`px-3 py-1.5 rounded-xl font-semibold transition shrink-0 cursor-pointer ${
              filterStatus === pill.id
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-white hover:bg-slate-50 text-slate-600 border border-slate-200/80'
            }`}
          >
            {pill.label}
          </button>
        ))}
      </div>

      {/* Mobile Scroll Indicator */}
      <div className="md:hidden flex items-center justify-between px-3 py-1.5 rounded-lg bg-sky-50/70 border border-sky-100 text-[11px] text-sky-800 font-medium">
        <span>← Swipe horizontally to inspect complete 3-way matching ledger →</span>
      </div>

      {/* Main Ledger Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs min-w-[760px]">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3.5">Txn / Scope</th>
                <th className="px-4 py-3.5">Line Item &amp; Vendor</th>
                <th className="px-4 py-3.5">PO Authorization</th>
                <th className="px-4 py-3.5">Invoice (Billed)</th>
                <th className="px-4 py-3.5">Payment (Disbursed)</th>
                <th className="px-4 py-3.5">Match &amp; Status</th>
                <th className="px-4 py-3.5">Variance / Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    <TableProperties className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <span>No ledger items found matching the selected filter.</span>
                  </td>
                </tr>
              ) : (
                filteredEntries.map((e) => {
                  const hasDiscrepancy = e.variance_amount && e.variance_amount > 0;
                  const itemCurrency = e.currency || 'USD';
                  const effectivePayment = e.paid_amount ?? e.receipt_amount;

                  return (
                    <tr key={e.id} className="hover:bg-slate-50/70 transition-colors">
                      {/* Origin & Audit ID */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="space-y-1">
                          <span className="font-mono text-[11px] font-bold text-slate-900 block">
                            {e.transaction_id || `TXN-${e.id}`}
                          </span>
                          <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md border border-slate-200 inline-flex items-center space-x-1">
                            <Layers className="w-2.5 h-2.5 text-slate-400" />
                            <span>Audit #{e.investigation_id}</span>
                          </span>
                        </div>
                      </td>

                      {/* Description & Vendor */}
                      <td className="px-4 py-3.5 font-bold text-slate-900 max-w-[200px]">
                        <div className="truncate">{e.item_description}</div>
                        {e.supplier_name && (
                          <div className="text-[11px] text-slate-500 font-medium truncate mt-0.5">
                            Vendor: <span className="text-slate-800">{e.supplier_name}</span>
                          </div>
                        )}
                      </td>

                      {/* PO Auth */}
                      <td className="px-4 py-3.5 whitespace-nowrap font-mono">
                        {e.po_amount !== null && e.po_amount !== undefined ? (
                          <div className="space-y-0.5">
                            <span className="text-slate-900 font-bold">
                              ${e.po_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </span>
                            <span className="text-[10px] text-slate-400 block font-normal">
                              {itemCurrency} ({e.po_reference || 'PO'})
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic text-[11px]">Missing PO</span>
                        )}
                      </td>

                      {/* Invoice Billed */}
                      <td className="px-4 py-3.5 whitespace-nowrap font-mono">
                        {e.invoice_amount !== null && e.invoice_amount !== undefined ? (
                          <div className="space-y-0.5">
                            <span className="text-slate-900 font-bold">
                              ${e.invoice_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </span>
                            <span className="text-[10px] text-slate-400 block font-normal">
                              {itemCurrency} ({e.invoice_number || 'INV'})
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic text-[11px]">Missing Invoice</span>
                        )}
                      </td>

                      {/* Payment Proof */}
                      <td className="px-4 py-3.5 whitespace-nowrap font-mono">
                        {effectivePayment !== null && effectivePayment !== undefined ? (
                          <div className="space-y-0.5">
                            <span className="text-emerald-700 font-bold">
                              ${effectivePayment.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </span>
                            <span className="text-[10px] text-slate-400 block font-normal">
                              {itemCurrency} ({e.receipt_proof || 'REC'})
                            </span>
                          </div>
                        ) : (
                          <span className="text-amber-700 italic text-[11px] font-semibold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                            Unpaid / No Voucher
                          </span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        {getStatusBadge(e.reconciliation_status)}
                      </td>

                      {/* Variance & Notes */}
                      <td className="px-4 py-3.5 max-w-[220px]">
                        {hasDiscrepancy ? (
                          <div className="space-y-1">
                            <span className="font-mono text-rose-700 font-bold text-xs bg-rose-50 px-2 py-0.5 rounded border border-rose-200 inline-block">
                              +${e.variance_amount?.toLocaleString(undefined, { minimumFractionDigits: 2 })} {itemCurrency}
                            </span>
                            {e.variance_reason && (
                              <p className="text-[11px] text-slate-600 leading-tight">
                                {e.variance_reason}
                              </p>
                            )}
                          </div>
                        ) : e.variance_reason ? (
                          <span className="text-[11px] text-slate-500 leading-tight block">
                            {e.variance_reason}
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[11px]">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <EvidenceReviewDrawer
        documentId={activeReviewDocId}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
};
