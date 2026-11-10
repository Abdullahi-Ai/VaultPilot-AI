import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle2,
  Edit3,
  XCircle,
  HelpCircle,
  Clock,
  ShieldCheck,
  Copy,
  Check,
  History,
  RefreshCw,
  Send,
  User,
  MapPin,
  FileCheck
} from 'lucide-react';
import { apiService } from '../services/api';
import { DocumentReviewSummary, FieldReview, FieldReviewAuditLog, ReviewStatus } from '../types';

interface EvidenceReviewDrawerProps {
  documentId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onReviewUpdated?: () => void;
}

export const EvidenceReviewDrawer: React.FC<EvidenceReviewDrawerProps> = ({
  documentId,
  isOpen,
  onClose,
  onReviewUpdated
}) => {
  const [summary, setSummary] = useState<DocumentReviewSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'fields' | 'history'>('fields');
  const [copiedSha, setCopiedSha] = useState(false);

  // Audit history state
  const [auditHistory, setAuditHistory] = useState<FieldReviewAuditLog[]>([]);

  // Action dialog state
  const [selectedField, setSelectedField] = useState<FieldReview | null>(null);
  const [actionType, setActionType] = useState<'VERIFY' | 'CORRECT' | 'REJECT' | 'CLARIFY' | null>(null);
  const [actionNotes, setActionNotes] = useState('');
  const [correctedValueInput, setCorrectedValueInput] = useState('');
  const [reviewerIdentifier, setReviewerIdentifier] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Re-reconciliation state
  const [reconciling, setReconciling] = useState(false);
  const [reconcileSuccessMsg, setReconcileSuccessMsg] = useState<string | null>(null);

  const handleReconcileNow = async () => {
    if (!documentId) return;
    setReconciling(true);
    setReconcileSuccessMsg(null);
    try {
      const res = await apiService.reconcileDocument(documentId);
      setReconcileSuccessMsg(`Reconciliation updated! ${res.summary}`);
      if (onReviewUpdated) {
        onReviewUpdated();
      }
      setTimeout(() => setReconcileSuccessMsg(null), 6000);
    } catch (err: any) {
      setError(err.message || 'Failed to re-evaluate reconciliation.');
    } finally {
      setReconciling(false);
    }
  };

  const fetchDocumentSummary = async (docId: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getDocumentReviewSummary(docId);
      setSummary(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load document review data.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditHistory = async (docId: number) => {
    try {
      const logs = await apiService.getDocumentReviewHistory(docId);
      setAuditHistory(logs);
    } catch (err) {
      console.warn('Could not load audit history:', err);
    }
  };

  useEffect(() => {
    if (isOpen && documentId) {
      fetchDocumentSummary(documentId);
      fetchAuditHistory(documentId);
      setActiveTab('fields');
      setSelectedField(null);
      setActionType(null);
      setActionError(null);
      setReconcileSuccessMsg(null);
    }
  }, [isOpen, documentId]);

  if (!isOpen) return null;

  const handleCopySha = (sha: string) => {
    navigator.clipboard.writeText(sha);
    setCopiedSha(true);
    setTimeout(() => setCopiedSha(false), 2000);
  };

  const openActionDialog = (field: FieldReview, type: 'VERIFY' | 'CORRECT' | 'REJECT' | 'CLARIFY') => {
    setSelectedField(field);
    setActionType(type);
    setActionNotes('');
    setCorrectedValueInput(field.reviewed_value || field.original_value || '');
    setReviewerIdentifier('lead-auditor');
    setActionError(null);
  };

  const closeActionDialog = () => {
    setSelectedField(null);
    setActionType(null);
    setActionError(null);
  };

  const handleSubmitAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!documentId || !selectedField || !actionType) return;

    if (actionType === 'CORRECT' && !correctedValueInput.trim()) {
      setActionError('Corrected value is required.');
      return;
    }
    if (!actionNotes.trim()) {
      setActionError('Audit justification note is required.');
      return;
    }

    setSubmittingAction(true);
    setActionError(null);
    try {
      if (actionType === 'VERIFY') {
        await apiService.verifyField(
          documentId,
          selectedField.field_name,
          actionNotes.trim(),
          reviewerIdentifier.trim() || undefined
        );
      } else if (actionType === 'CORRECT') {
        await apiService.correctField(
          documentId,
          selectedField.field_name,
          correctedValueInput.trim(),
          actionNotes.trim(),
          reviewerIdentifier.trim() || undefined
        );
      } else if (actionType === 'REJECT') {
        await apiService.rejectField(
          documentId,
          selectedField.field_name,
          actionNotes.trim(),
          reviewerIdentifier.trim() || undefined
        );
      } else if (actionType === 'CLARIFY') {
        await apiService.clarifyField(
          documentId,
          selectedField.field_name,
          actionNotes.trim(),
          reviewerIdentifier.trim() || undefined
        );
      }

      await fetchDocumentSummary(documentId);
      await fetchAuditHistory(documentId);
      if (onReviewUpdated) {
        onReviewUpdated();
      }
      closeActionDialog();
    } catch (err: any) {
      setActionError(err.message || 'Review action failed.');
    } finally {
      setSubmittingAction(false);
    }
  };

  const renderStatusBadge = (status: ReviewStatus) => {
    switch (status) {
      case 'VERIFIED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-2.5 h-2.5" />
            <span>Verified</span>
          </span>
        );
      case 'CORRECTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-sky-50 text-sky-700 border border-sky-200">
            <Edit3 className="w-2.5 h-2.5" />
            <span>Corrected</span>
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-2.5 h-2.5" />
            <span>Rejected</span>
          </span>
        );
      case 'REQUIRES_CLARIFICATION':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-purple-50 text-purple-700 border border-purple-200">
            <HelpCircle className="w-2.5 h-2.5" />
            <span>Clarification</span>
          </span>
        );
      case 'PENDING':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-2.5 h-2.5" />
            <span>Pending</span>
          </span>
        );
    }
  };

  const formatFieldName = (name: string) => {
    return name
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  const formatValue = (val: string | null | undefined) => {
    if (val === null || val === undefined || val === '') {
      return <span className="text-slate-400 italic">None / Unextracted</span>;
    }
    return val;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-4 sm:pl-10">
        <div className="w-screen max-w-full sm:max-w-xl md:max-w-2xl lg:max-w-3xl bg-white border-l border-slate-200 shadow-2xl flex flex-col h-full animate-in slide-in-from-right duration-250">

          {/* Drawer Header */}
          <div className="p-4 sm:p-6 border-b border-slate-200/90 bg-slate-50/70 shrink-0 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-slate-200 text-slate-800 font-mono">
                    {summary?.document_type || 'DOCUMENT'}
                  </span>
                  {summary?.is_fully_reviewed ? (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-purple-50 text-purple-700 border border-purple-200">
                      <ShieldCheck className="w-3 h-3" />
                      <span>Certified Audit Complete</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-200">
                      <Clock className="w-3 h-3" />
                      <span>Review In Progress</span>
                    </span>
                  )}
                </div>

                <h2 className="text-lg sm:text-xl font-bold text-slate-900 truncate">
                  {summary?.filename || 'Evidence File Review'}
                </h2>

                <p className="text-xs text-slate-500 font-mono truncate">
                  Document ID: #{summary?.document_id}
                </p>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/70 transition-colors shrink-0 cursor-pointer"
                aria-label="Close drawer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* SHA-256 Hash Display */}
            {summary?.sha256 && (
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-100 border border-slate-200 text-[11px] font-mono text-slate-600 gap-2">
                <span className="truncate">
                  SHA-256: {summary.sha256}
                </span>
                <button
                  onClick={() => handleCopySha(summary.sha256!)}
                  className="px-2 py-1 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-[10px] font-semibold flex items-center space-x-1 shrink-0 cursor-pointer"
                >
                  {copiedSha ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedSha ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            )}

            {/* Navigation Tabs & Dynamic Re-Reconciliation Trigger */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-200/80">
              <div className="flex items-center space-x-4 text-xs font-semibold">
                <button
                  onClick={() => setActiveTab('fields')}
                  className={`pb-2 flex items-center space-x-1.5 border-b-2 transition cursor-pointer ${
                    activeTab === 'fields'
                      ? 'border-sky-600 text-sky-600 font-bold'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <FileCheck className="w-4 h-4" />
                  <span>Extracted Fields ({summary?.fields?.length || 0})</span>
                </button>

                <button
                  onClick={() => setActiveTab('history')}
                  className={`pb-2 flex items-center space-x-1.5 border-b-2 transition cursor-pointer ${
                    activeTab === 'history'
                      ? 'border-sky-600 text-sky-600 font-bold'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <History className="w-4 h-4" />
                  <span>Audit Trail ({auditHistory.length})</span>
                </button>
              </div>

              <button
                onClick={handleReconcileNow}
                disabled={reconciling}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center justify-center space-x-1.5 shadow-xs disabled:opacity-50 cursor-pointer"
                title="Re-run reconciliation matching incorporating human adjustments"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? 'animate-spin' : ''}`} />
                <span>{reconciling ? 'Re-evaluating...' : 'Re-evaluate Matching'}</span>
              </button>
            </div>

            {reconcileSuccessMsg && (
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2 animate-in fade-in">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                <span>{reconcileSuccessMsg}</span>
              </div>
            )}
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 custom-scrollbar bg-slate-50/50">
            {loading ? (
              <div className="flex items-center justify-center py-20 text-slate-400 space-x-2">
                <RefreshCw className="w-6 h-6 animate-spin text-sky-600" />
                <span className="text-sm font-medium">Loading document review data...</span>
              </div>
            ) : error ? (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs sm:text-sm">
                {error}
              </div>
            ) : activeTab === 'fields' ? (
              <div className="space-y-4">
                {summary?.fields && summary.fields.length > 0 ? (
                  summary.fields.map((field) => {
                    const locationTag = field.source_provenance?.source_location || field.source_provenance?.filename;

                    return (
                      <div
                        key={field.id}
                        className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs hover:border-slate-300 transition space-y-3"
                      >
                        {/* Field Header */}
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-900 text-sm sm:text-base">
                              {formatFieldName(field.field_name)}
                            </span>
                            {locationTag && (
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200">
                                <MapPin className="w-2.5 h-2.5 text-sky-600" />
                                <span>{locationTag}</span>
                              </span>
                            )}
                          </div>
                          <div>{renderStatusBadge(field.status)}</div>
                        </div>

                        {/* Side-by-Side Values Comparison */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs">
                          {/* Original Value */}
                          <div className="space-y-1">
                            <span className="text-[10px] font-bold text-slate-400 block uppercase tracking-wider">
                              Original Extracted:
                            </span>
                            <span className="font-mono text-slate-800 text-xs sm:text-sm font-semibold break-all">
                              {formatValue(field.original_value)}
                            </span>
                          </div>

                          {/* Effective Value */}
                          <div className="space-y-1">
                            <span className="text-[10px] font-bold text-slate-400 block uppercase tracking-wider">
                              Reviewed / Effective:
                            </span>
                            {field.status === 'CORRECTED' ? (
                              <span className="font-mono text-sky-700 text-xs sm:text-sm font-bold break-all">
                                {formatValue(field.reviewed_value)}
                              </span>
                            ) : field.status === 'REJECTED' ? (
                              <span className="text-rose-600 text-xs italic font-medium block">
                                Excluded from calculations
                              </span>
                            ) : (
                              <span className="font-mono text-slate-800 text-xs sm:text-sm font-semibold break-all">
                                {formatValue(field.reviewed_value || field.original_value)}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-100">
                          <button
                            onClick={() => openActionDialog(field, 'VERIFY')}
                            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 hover:bg-emerald-100/80 text-emerald-700 border border-emerald-200 transition flex items-center space-x-1 cursor-pointer"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Verify</span>
                          </button>

                          <button
                            onClick={() => openActionDialog(field, 'CORRECT')}
                            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-sky-50 hover:bg-sky-100/80 text-sky-700 border border-sky-200 transition flex items-center space-x-1 cursor-pointer"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                            <span>Correct</span>
                          </button>

                          <button
                            onClick={() => openActionDialog(field, 'REJECT')}
                            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-rose-50 hover:bg-rose-100/80 text-rose-700 border border-rose-200 transition flex items-center space-x-1 cursor-pointer"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>

                          <button
                            onClick={() => openActionDialog(field, 'CLARIFY')}
                            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-purple-50 hover:bg-purple-100/80 text-purple-700 border border-purple-200 transition flex items-center space-x-1 cursor-pointer"
                          >
                            <HelpCircle className="w-3.5 h-3.5" />
                            <span>Clarify</span>
                          </button>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    No individual field extractions found for this document.
                  </div>
                )}
              </div>
            ) : (
              /* Immutable Audit Trail Tab */
              <div className="space-y-4">
                {auditHistory.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs bg-white rounded-2xl border border-slate-200/90 shadow-xs">
                    No human review adjustments have been recorded for this document yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {auditHistory.map((log) => (
                      <div
                        key={log.id}
                        className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-xs space-y-2 text-xs"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-1 border-b border-slate-100 pb-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-900">
                              {formatFieldName(log.field_name)}
                            </span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                              {log.action}
                            </span>
                          </div>
                          <span className="text-[10px] text-slate-400">
                            {new Date(log.action_timestamp).toLocaleString()}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          <div>
                            <span className="text-slate-400 block">Previous:</span>
                            <span className="font-mono text-slate-700 font-medium line-through">
                              {log.previous_value || 'None'}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-400 block">Adjusted:</span>
                            <span className="font-mono text-sky-700 font-bold">
                              {log.new_value || 'None'}
                            </span>
                          </div>
                        </div>

                        {log.notes && (
                          <p className="text-slate-600 text-xs italic bg-amber-50/40 p-2 rounded border border-amber-100">
                            "{log.notes}"
                          </p>
                        )}

                        <div className="text-[10px] text-slate-400 flex items-center space-x-1">
                          <User className="w-3 h-3 text-slate-400" />
                          <span>Auditor: <strong className="text-slate-700">{log.reviewer_id || 'System'}</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Dialog Modal / Overlay */}
          {selectedField && actionType && (
            <div className="p-4 sm:p-6 border-t border-slate-200 bg-white shrink-0 shadow-lg space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h4 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                  <span>Record Action: {actionType} ({formatFieldName(selectedField.field_name)})</span>
                </h4>
                <button
                  onClick={closeActionDialog}
                  className="text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {actionError && (
                <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                  {actionError}
                </div>
              )}

              <form onSubmit={handleSubmitAction} className="space-y-3">
                {actionType === 'CORRECT' && (
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Corrected Value *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 12000.00"
                      value={correctedValueInput}
                      onChange={(e) => setCorrectedValueInput(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm font-mono focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
                    />
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Auditor Identifier
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. lead-auditor"
                      value={reviewerIdentifier}
                      onChange={(e) => setReviewerIdentifier(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 text-xs focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Action Notes &amp; Justification *
                  </label>
                  <textarea
                    rows={2}
                    required
                    placeholder="Provide specific audit rationale (e.g. PO authorization PO-MED-441 matched with Credit Memo CM-01)."
                    value={actionNotes}
                    onChange={(e) => setActionNotes(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-slate-900 text-xs focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={closeActionDialog}
                    className="px-3.5 py-1.5 rounded-xl border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50 transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingAction}
                    className="px-4 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition-colors disabled:opacity-50 shadow-xs flex items-center space-x-1 cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{submittingAction ? 'Submitting...' : 'Submit Action'}</span>
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
