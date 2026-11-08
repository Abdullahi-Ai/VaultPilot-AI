import React, { useState } from 'react';
import { 
  AlertCircle, 
  AlertTriangle, 
  FileSearch, 
  HelpCircle, 
  Filter, 
  CheckSquare, 
  FileText,
  Database,
  Layers,
  Calculator,
  Info
} from 'lucide-react';
import { Finding, FindingClassification } from '../types';

interface FindingsPageProps {
  findings: Finding[];
}

export const FindingsPage: React.FC<FindingsPageProps> = ({ findings }) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');

  const filteredFindings = selectedFilter === 'ALL'
    ? findings
    : findings.filter(f => f.classification === selectedFilter);

  const getBadgeStyle = (classification: FindingClassification) => {
    switch (classification) {
      case 'CONFIRMED_DISCREPANCY':
        return {
          bg: 'bg-rose-50 border-rose-200 text-rose-800',
          icon: AlertCircle,
          label: 'Tier 1: Confirmed Discrepancy'
        };
      case 'POTENTIAL_ANOMALY':
        return {
          bg: 'bg-indigo-50 border-indigo-200 text-indigo-800',
          icon: AlertTriangle,
          label: 'Tier 2: Potential Anomaly'
        };
      case 'MISSING_EVIDENCE':
        return {
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          icon: FileSearch,
          label: 'Tier 3: Missing Evidence'
        };
      case 'UNVERIFIED':
      default:
        return {
          bg: 'bg-slate-100 border-slate-200 text-slate-800',
          icon: HelpCircle,
          label: 'Tier 4: Unverified'
        };
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Four-Tier Classified Findings & Evidence Traceability</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Rule-guided evidence assessment. Every observation is traceable to document records, extracted fields, and calculation formulas.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center space-x-1.5 bg-white p-1 rounded-xl border border-slate-200 text-xs shadow-sm overflow-x-auto">
          {['ALL', 'CONFIRMED_DISCREPANCY', 'POTENTIAL_ANOMALY', 'MISSING_EVIDENCE', 'UNVERIFIED'].map((tab) => (
            <button
              key={tab}
              onClick={() => setSelectedFilter(tab)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors whitespace-nowrap ${
                selectedFilter === tab
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {tab === 'ALL' ? 'All Findings' : tab.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="bg-white p-12 text-center rounded-2xl border border-slate-200">
            <Filter className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-slate-700">No findings matching the selected classification</h3>
          </div>
        ) : (
          filteredFindings.map((f) => {
            const style = getBadgeStyle(f.classification);
            const Icon = style.icon;
            const isDemoFixture = f.title.includes('[DEMO') || f.evidence_limitations?.includes('Demonstration') || f.id >= 1000;

            return (
              <div 
                key={f.id}
                className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4 hover:shadow-md transition-shadow"
              >
                {/* Header row with Investigation & Source Metadata */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center flex-wrap gap-2">
                    <span className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border ${style.bg}`}>
                      <Icon className="w-3.5 h-3.5" />
                      <span>{style.label}</span>
                    </span>

                    {/* Investigation Identifier */}
                    <span className="text-[11px] font-semibold bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-full border border-slate-200 flex items-center space-x-1">
                      <Layers className="w-3 h-3 text-slate-500" />
                      <span>Investigation #{f.investigation_id}</span>
                    </span>

                    {/* Live vs Demo Distinction */}
                    {isDemoFixture ? (
                      <span className="text-[10px] font-bold bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full border border-purple-200">
                        SIMULATED DEMO FIXTURE
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200 flex items-center space-x-1">
                        <Database className="w-2.5 h-2.5" />
                        <span>DB PERSISTED RECORD #{f.id}</span>
                      </span>
                    )}

                    <span className="font-mono text-xs font-semibold text-slate-500">
                      Ref: {f.subject_reference || 'General Scope'}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    Logged: {new Date(f.created_at).toLocaleDateString()}
                  </span>
                </div>

                {/* Title */}
                <div>
                  <h3 className="text-base font-bold text-slate-900">{f.title}</h3>
                  {f.classification_rationale && (
                    <p className="text-xs text-slate-500 mt-1 italic">
                      <strong className="text-slate-700 not-italic">Classification Rationale:</strong> {f.classification_rationale}
                    </p>
                  )}
                </div>

                {/* Expected vs Observed Grid */}
                {(f.expected_value || f.observed_value) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                      <span className="text-slate-400 font-semibold block text-[10px] uppercase tracking-wider">
                        Expected Value / Authorized Limit
                      </span>
                      <span className="font-mono font-semibold text-slate-700 block">
                        {f.expected_value || 'None specified'}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-rose-50/50 border border-rose-100 space-y-1">
                      <span className="text-rose-500 font-semibold block text-[10px] uppercase tracking-wider">
                        Observed Value / Evidence Found
                      </span>
                      <span className="font-mono font-bold text-rose-900 block">
                        {f.observed_value || 'None observed'}
                      </span>
                    </div>
                  </div>
                )}

                {/* Calculation Details (Task 3 & 5) */}
                {f.comparison_details && f.comparison_details.calculation && (
                  <div className="bg-sky-50/60 p-3 rounded-xl border border-sky-100 text-xs space-y-1">
                    <div className="flex items-center space-x-1.5 text-sky-800 font-semibold">
                      <Calculator className="w-3.5 h-3.5 text-sky-600" />
                      <span>Mathematical Calculation & Variance:</span>
                    </div>
                    <code className="block font-mono text-xs font-bold text-sky-900 bg-white/80 p-2 rounded-lg border border-sky-200">
                      {f.comparison_details.calculation}
                    </code>
                  </div>
                )}

                {/* Variance Explanation */}
                <div className="text-xs text-slate-600 leading-relaxed bg-slate-50/50 p-3.5 rounded-xl border border-slate-100">
                  <span className="font-bold text-slate-800 block mb-0.5">Variance Analysis:</span>
                  {f.variance_explanation}
                </div>

                {/* Missing Evidence & Limitations (Task 3 & 5) */}
                {(f.missing_evidence_details || f.evidence_limitations) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {f.missing_evidence_details && (
                      <div className="p-3 rounded-xl bg-amber-50/50 border border-amber-100">
                        <span className="font-bold text-amber-800 flex items-center space-x-1 mb-1">
                          <FileSearch className="w-3.5 h-3.5 text-amber-600" />
                          <span>Missing Documentation in Scope:</span>
                        </span>
                        <p className="text-slate-600 text-[11px]">{f.missing_evidence_details}</p>
                      </div>
                    )}

                    {f.evidence_limitations && (
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="font-bold text-slate-700 flex items-center space-x-1 mb-1">
                          <Info className="w-3.5 h-3.5 text-slate-500" />
                          <span>Evidence Limitations & Boundary:</span>
                        </span>
                        <p className="text-slate-600 text-[11px]">{f.evidence_limitations}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Traceable Source Document Records (Task 1 & 5) */}
                <div className="pt-2 text-xs border-t border-slate-100 space-y-2">
                  <span className="font-bold text-slate-800 flex items-center space-x-1">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    <span>Traceable Supporting Document Records:</span>
                  </span>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {f.source_paths.map((p, idx) => {
                      const docId = f.source_document_ids && f.source_document_ids[idx];
                      return (
                        <div key={idx} className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/70 space-y-1">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-semibold text-slate-800 truncate font-mono">
                              {p.split('/').pop()}
                            </span>
                            {docId ? (
                              <span className="text-[10px] font-mono bg-sky-100 text-sky-800 px-1.5 py-0.5 rounded font-bold">
                                Doc #{docId}
                              </span>
                            ) : (
                              <span className="text-[10px] font-mono bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded">
                                Path Ref
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono block truncate" title={p}>
                            {p}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Action Required */}
                <div className="pt-2 text-xs border-t border-slate-100">
                  <span className="font-bold text-slate-800 flex items-center space-x-1 mb-1">
                    <CheckSquare className="w-3.5 h-3.5 text-sky-600" />
                    <span>Recommended Human Review Action:</span>
                  </span>
                  <p className="text-slate-600">{f.recommended_action}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
