import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  FileSearch,
  HelpCircle,
  FileText,
  ChevronRight,
  ShieldAlert,
  Scale
} from 'lucide-react';
import { Finding, FindingClassification } from '../types';
import { EvidenceReviewDrawer } from '../components/EvidenceReviewDrawer';

interface FindingsPageProps {
  findings: Finding[];
}

export const FindingsPage: React.FC<FindingsPageProps> = ({ findings }) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [activeReviewDocId, setActiveReviewDocId] = useState<number | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const filteredFindings = selectedFilter === 'ALL'
    ? findings
    : findings.filter(f => f.classification === selectedFilter);

  const getBadgeStyle = (classification: FindingClassification) => {
    switch (classification) {
      case 'CONFIRMED_DISCREPANCY':
        return {
          bg: 'bg-rose-50 border-rose-200/90 text-rose-800',
          icon: AlertCircle,
          label: 'Tier 1: Confirmed Discrepancy'
        };
      case 'POTENTIAL_ANOMALY':
        return {
          bg: 'bg-indigo-50 border-indigo-200/90 text-indigo-800',
          icon: AlertTriangle,
          label: 'Tier 2: Potential Anomaly'
        };
      case 'MISSING_EVIDENCE':
        return {
          bg: 'bg-amber-50 border-amber-200/90 text-amber-800',
          icon: FileSearch,
          label: 'Tier 3: Missing Supporting Evidence'
        };
      case 'UNVERIFIED':
      default:
        return {
          bg: 'bg-slate-100 border-slate-200 text-slate-800',
          icon: HelpCircle,
          label: 'Tier 4: Optical Degradation / Unverified'
        };
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Four-Tier Classified Findings &amp; Evidence Traceability
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Rule-guided evidence cross-examination. Every observation is strictly traceable to document source paths.
          </p>
        </div>

        {/* Filter Quick Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto no-scrollbar py-0.5 text-xs shrink-0">
          {[
            { id: 'ALL', label: `All (${findings.length})` },
            { id: 'CONFIRMED_DISCREPANCY', label: 'Discrepancies' },
            { id: 'POTENTIAL_ANOMALY', label: 'Anomalies' },
            { id: 'MISSING_EVIDENCE', label: 'Missing Evidence' },
            { id: 'UNVERIFIED', label: 'Unverified' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedFilter(tab.id)}
              className={`px-3 py-1.5 rounded-xl font-semibold transition shrink-0 cursor-pointer ${
                selectedFilter === tab.id
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-white hover:bg-slate-50 text-slate-600 border border-slate-200/80'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-white border border-slate-200/90 rounded-2xl shadow-xs text-xs sm:text-sm">
            <ShieldAlert className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <span>No classified findings recorded under this severity filter.</span>
          </div>
        ) : (
          filteredFindings.map((finding) => {
            const badge = getBadgeStyle(finding.classification);
            const Icon = badge.icon;
            const hasExpected = finding.expected_value || finding.observed_value;

            return (
              <div
                key={finding.id}
                className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:border-slate-300 transition-all space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold uppercase border ${badge.bg}`}>
                        <Icon className="w-3 h-3" />
                        <span>{badge.label}</span>
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        Audit #{finding.investigation_id}
                      </span>
                    </div>

                    <h3 className="text-base sm:text-lg font-bold text-slate-900 leading-snug">
                      {finding.title}
                    </h3>
                  </div>

                  {finding.subject_reference && (
                    <div className="bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-xl shrink-0 self-start sm:self-auto font-mono text-xs text-slate-700">
                      Ref: <strong className="text-slate-900">{finding.subject_reference}</strong>
                    </div>
                  )}
                </div>

                {/* Variance Explanation */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-700 leading-relaxed">
                  {finding.variance_explanation}
                </div>

                {/* Expected vs Observed Details */}
                {hasExpected && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200/60 font-mono">
                    {finding.expected_value && (
                      <div className="space-y-0.5">
                        <span className="text-slate-400 text-[10px] uppercase block font-sans font-bold">Authorized / Expected:</span>
                        <span className="text-slate-800 font-bold">{finding.expected_value}</span>
                      </div>
                    )}
                    {finding.observed_value && (
                      <div className="space-y-0.5">
                        <span className="text-slate-400 text-[10px] uppercase block font-sans font-bold">Observed on Evidence:</span>
                        <span className="text-rose-700 font-bold">{finding.observed_value}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Recommended Action */}
                {finding.recommended_action && (
                  <div className="text-xs text-slate-600 bg-sky-50/50 p-3 rounded-xl border border-sky-100 flex items-start space-x-2">
                    <Scale className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-sky-950 block">Recommended Audit Action:</span>
                      <p className="mt-0.5 text-slate-700 leading-relaxed">{finding.recommended_action}</p>
                    </div>
                  </div>
                )}

                {/* Traceable Supporting Documents */}
                {finding.documents && finding.documents.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-2 text-xs">
                    <span className="text-slate-400 font-semibold text-[11px]">Traceable Evidence:</span>
                    {finding.documents.map((doc) => (
                      <button
                        key={doc.id}
                        onClick={() => {
                          setActiveReviewDocId(doc.id);
                          setIsDrawerOpen(true);
                        }}
                        className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-sky-50 hover:bg-sky-100/80 text-sky-800 border border-sky-200 text-xs font-medium transition cursor-pointer"
                      >
                        <FileText className="w-3 h-3 text-sky-600" />
                        <span className="font-mono text-[11px] truncate max-w-[160px] sm:max-w-xs">{doc.filename}</span>
                        <ChevronRight className="w-3 h-3 text-sky-400" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <EvidenceReviewDrawer
        documentId={activeReviewDocId}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
};
