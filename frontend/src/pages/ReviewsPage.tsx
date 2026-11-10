import React, { useState, useEffect } from 'react';
import {
  FileCheck2,
  Clock,
  CheckCircle2,
  Edit3,
  XCircle,
  HelpCircle,
  RefreshCw,
  Filter,
  FileText,
  ArrowRight,
  FolderKanban,
  ShieldCheck
} from 'lucide-react';
import { apiService } from '../services/api';
import { DocumentRecord, DocumentReviewSummary, Project } from '../types';
import { EvidenceReviewDrawer } from '../components/EvidenceReviewDrawer';

interface ReviewsPageProps {
  projects: Project[];
}

export const ReviewsPage: React.FC<ReviewsPageProps> = ({ projects }) => {
  const [selectedProjectId, setSelectedProjectId] = useState<number | undefined>();
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [docSummaries, setDocSummaries] = useState<Record<number, DocumentReviewSummary>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Review Drawer State
  const [activeReviewDocId, setActiveReviewDocId] = useState<number | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const loadReviewData = async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await apiService.getDocuments(selectedProjectId);
      setDocuments(docs);

      const summariesMap: Record<number, DocumentReviewSummary> = {};
      await Promise.all(
        docs.map(async (doc) => {
          try {
            const summary = await apiService.getDocumentReviewSummary(doc.id);
            summariesMap[doc.id] = summary;
          } catch (e) {
            // Ignore missing reviews for uninitialized documents
          }
        })
      );
      setDocSummaries(summariesMap);
    } catch (err: any) {
      setError(err.message || 'Failed to load evidence review data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviewData();
  }, [selectedProjectId, statusFilter]);

  useEffect(() => {
    if (typeof window !== 'undefined' && documents.length > 0) {
      const params = new URLSearchParams(window.location.search);
      const docParam = params.get('drawer_doc');
      if (docParam) {
        const id = parseInt(docParam, 10);
        if (!isNaN(id)) {
          setActiveReviewDocId(id);
          setIsDrawerOpen(true);
        } else {
          setActiveReviewDocId(documents[0].id);
          setIsDrawerOpen(true);
        }
      }
    }
  }, [documents]);

  const handleOpenDrawer = (docId: number) => {
    setActiveReviewDocId(docId);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
    setActiveReviewDocId(null);
  };

  const handleReviewUpdated = () => {
    loadReviewData();
  };

  // Compute aggregate review metrics
  let totalPending = 0;
  let totalVerified = 0;
  let totalCorrected = 0;
  let totalRejected = 0;
  let totalClarification = 0;

  Object.values(docSummaries).forEach((s) => {
    totalPending += s.pending_count;
    totalVerified += s.verified_count;
    totalCorrected += s.corrected_count;
    totalRejected += s.rejected_count;
    totalClarification += s.clarification_count;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center space-x-2 text-sky-600 text-xs font-bold tracking-wider uppercase mb-1">
            <FileCheck2 className="w-4 h-4" />
            <span>Human-in-the-Loop Audit Quality Control</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight break-words">
            Evidence Review & Human Verification
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Cross-examine extracted metadata against immutable source files, record adjustments, and preserve full provenance.
          </p>
        </div>
        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={loadReviewData}
            disabled={loading}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold border border-slate-200/90 shadow-xs transition flex items-center justify-center space-x-2 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-600' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Aggregate Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
        <div className="bg-white p-3 rounded-xl border border-slate-200/90 shadow-xs space-y-1 min-w-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block truncate">Pending Review</span>
          <div className="flex items-center space-x-1.5 text-amber-600">
            <Clock className="w-4 h-4 shrink-0" />
            <span className="text-lg font-bold font-mono">{totalPending}</span>
          </div>
        </div>

        <div className="bg-white p-3 rounded-xl border border-slate-200/90 shadow-xs space-y-1 min-w-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block truncate">Human Verified</span>
          <div className="flex items-center space-x-1.5 text-emerald-600">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span className="text-lg font-bold font-mono">{totalVerified}</span>
          </div>
        </div>

        <div className="bg-white p-3 rounded-xl border border-slate-200/90 shadow-xs space-y-1 min-w-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block truncate">Corrected Fields</span>
          <div className="flex items-center space-x-1.5 text-sky-600">
            <Edit3 className="w-4 h-4 shrink-0" />
            <span className="text-lg font-bold font-mono">{totalCorrected}</span>
          </div>
        </div>

        <div className="bg-white p-3 rounded-xl border border-slate-200/90 shadow-xs space-y-1 min-w-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block truncate">Rejected / Excluded</span>
          <div className="flex items-center space-x-1.5 text-rose-600">
            <XCircle className="w-4 h-4 shrink-0" />
            <span className="text-lg font-bold font-mono">{totalRejected}</span>
          </div>
        </div>

        <div className="bg-white p-3 rounded-xl border border-slate-200/90 shadow-xs space-y-1 col-span-2 sm:col-span-1 min-w-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block truncate">Clarification Asked</span>
          <div className="flex items-center space-x-1.5 text-purple-600">
            <HelpCircle className="w-4 h-4 shrink-0" />
            <span className="text-lg font-bold font-mono">{totalClarification}</span>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3.5 bg-white border border-slate-200/90 rounded-2xl shadow-xs text-xs min-w-0">
        <div className="flex items-center space-x-2.5 min-w-0 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider shrink-0">Scope:</span>
          <select
            value={selectedProjectId || ''}
            onChange={(e) => setSelectedProjectId(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 text-xs font-semibold focus:outline-none focus:border-sky-500 cursor-pointer w-full sm:w-auto"
          >
            <option value="">All Scoped Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.code})
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto no-scrollbar py-0.5 w-full md:w-auto min-w-0 max-w-full">
          {['ALL', 'PENDING', 'VERIFIED', 'CORRECTED', 'REJECTED'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition shrink-0 cursor-pointer ${
                statusFilter === status
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-slate-200/70'
              }`}
            >
              {status === 'ALL' ? 'All Statuses' : status.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Document Review List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-16 text-center text-slate-500 flex items-center justify-center space-x-3 bg-white border border-slate-200/90 rounded-2xl shadow-xs">
            <RefreshCw className="w-6 h-6 animate-spin text-sky-600" />
            <span className="text-xs sm:text-sm font-medium">Scanning evidence documents and review records...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs sm:text-sm">
            {error}
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-white border border-slate-200/90 rounded-2xl shadow-xs text-xs sm:text-sm">
            No evidence documents discovered within the selected project scope.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {documents.map((doc) => {
              const summary = docSummaries[doc.id];
              const project = projects.find((p) => p.id === doc.project_id);
              const isUnverified = doc.extraction_status === 'UNVERIFIED';

              return (
                <div
                  key={doc.id}
                  className="p-4 sm:p-5 bg-white border border-slate-200/90 hover:border-sky-300 rounded-2xl transition shadow-xs space-y-3"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200 shrink-0">
                          {doc.document_type}
                        </span>
                        <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase border shrink-0 ${
                          isUnverified
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        }`}>
                          Extraction: {doc.extraction_status}
                        </span>
                        {summary?.is_fully_reviewed && (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase bg-purple-50 text-purple-700 border border-purple-200 shrink-0">
                            <ShieldCheck className="w-3 h-3" />
                            <span>Verified Certified</span>
                          </span>
                        )}
                        {project && (
                          <span className="text-xs text-slate-500 flex items-center space-x-1 shrink-0">
                            <FolderKanban className="w-3.5 h-3.5 text-slate-400" />
                            <span>{project.name}</span>
                          </span>
                        )}
                      </div>

                      <h3 className="text-base sm:text-lg font-bold text-slate-900 flex items-center space-x-2 truncate">
                        <FileText className="w-4 h-4 text-sky-600 shrink-0" />
                        <span className="truncate">{doc.filename}</span>
                      </h3>

                      <p className="text-xs text-slate-400 font-mono truncate max-w-2xl">
                        {doc.file_path}
                      </p>
                    </div>

                    <div className="flex items-center space-x-3 shrink-0 self-start md:self-center">
                      <button
                        onClick={() => handleOpenDrawer(doc.id)}
                        className="w-full sm:w-auto px-4 py-2 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white transition flex items-center justify-center space-x-2 shadow-xs cursor-pointer"
                      >
                        <span>Review &amp; Verify Fields</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Summary Breakdown Pills */}
                  {summary && (
                    <div className="pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-2 text-xs">
                      <span className="text-slate-400 font-medium text-[11px]">Field Statuses:</span>
                      {summary.pending_count > 0 && (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200 text-[11px] font-semibold">
                          <Clock className="w-3 h-3" />
                          <span>{summary.pending_count} Pending</span>
                        </span>
                      )}
                      {summary.verified_count > 0 && (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-semibold">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>{summary.verified_count} Verified</span>
                        </span>
                      )}
                      {summary.corrected_count > 0 && (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 border border-sky-200 text-[11px] font-semibold">
                          <Edit3 className="w-3 h-3" />
                          <span>{summary.corrected_count} Corrected</span>
                        </span>
                      )}
                      {summary.rejected_count > 0 && (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200 text-[11px] font-semibold">
                          <XCircle className="w-3 h-3" />
                          <span>{summary.rejected_count} Rejected</span>
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Human Review Slide-Over Drawer */}
      <EvidenceReviewDrawer
        documentId={activeReviewDocId}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onReviewUpdated={handleReviewUpdated}
      />
    </div>
  );
};
