import React, { useState } from 'react';
import { SearchCode, Play, Calendar, CheckCircle, FileText, ChevronRight } from 'lucide-react';
import { Investigation, Project } from '../types';
import { Modal } from '../components/Modal';

interface InvestigationsPageProps {
  investigations: Investigation[];
  projects: Project[];
  selectedProjectId?: number;
  onTriggerAudit: (projectId: number, scopePath?: string, title?: string) => Promise<void>;
  onViewInvestigationDetails: (inv: Investigation) => void;
}

export const InvestigationsPage: React.FC<InvestigationsPageProps> = ({
  investigations,
  projects,
  selectedProjectId,
  onTriggerAudit,
  onViewInvestigationDetails
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [projectId, setProjectId] = useState<number>(selectedProjectId || (projects[0]?.id || 1));
  const [title, setTitle] = useState('Routine Financial Evidence Audit');
  const [scopePath, setScopePath] = useState('');
  const [running, setRunning] = useState(false);

  const selectedProj = projects.find(p => p.id === projectId);

  const handleStartAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunning(true);
    try {
      const targetFolder = scopePath.trim() || selectedProj?.nas_folder_path || '/volume1/NGO_Projects/Audit';
      await onTriggerAudit(projectId, targetFolder, title);
      setIsModalOpen(false);
      setTitle('Routine Financial Evidence Audit');
      setScopePath('');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Financial Evidence Investigations</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit runs that discover files, extract records, and cross-examine evidence chains.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-sky-600 hover:bg-sky-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors flex items-center space-x-2 shadow-sm"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Launch Investigation</span>
        </button>
      </div>

      <div className="space-y-4">
        {investigations.length === 0 ? (
          <div className="bg-white p-12 text-center rounded-2xl border border-slate-200">
            <SearchCode className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-700">No Investigations Executed Yet</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Launch an investigation to scan an authorized NAS folder and correlate financial evidence.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-4 bg-sky-600 text-white px-4 py-2 rounded-xl text-xs font-semibold hover:bg-sky-500 transition-colors"
            >
              Start First Audit
            </button>
          </div>
        ) : (
          investigations.map((inv) => {
            const project = projects.find(p => p.id === inv.project_id);
            return (
              <div
                key={inv.id}
                onClick={() => onViewInvestigationDetails(inv)}
                className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-sky-300 hover:shadow-sm transition-all cursor-pointer flex items-center justify-between group"
              >
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-slate-900 text-base group-hover:text-sky-600 transition-colors">
                      {inv.title}
                    </span>
                    <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center space-x-1">
                      <CheckCircle className="w-2.5 h-2.5" />
                      <span>{inv.status}</span>
                    </span>
                  </div>

                  <div className="flex items-center space-x-4 text-xs text-slate-500">
                    <span>Project: <strong className="text-slate-800">{project?.name || `Project #${inv.project_id}`}</strong></span>
                    <span>•</span>
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{new Date(inv.created_at).toLocaleDateString()}</span>
                    </span>
                    <span>•</span>
                    <span className="flex items-center space-x-1">
                      <FileText className="w-3.5 h-3.5 text-slate-400" />
                      <span>{inv.document_count} files analyzed</span>
                    </span>
                  </div>

                  {inv.summary && (
                    <p className="text-xs text-slate-600 max-w-3xl line-clamp-2">
                      {inv.summary}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-3 pl-4">
                  <div className="text-right">
                    <span className="text-[11px] text-slate-400 block font-medium">Verified Total</span>
                    <span className="font-bold text-slate-900 text-sm">
                      ${(inv.verified_totals['USD'] || 0).toLocaleString()} USD
                    </span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-sky-500 group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Trigger Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Launch Financial Evidence Investigation">
        <form onSubmit={handleStartAudit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Target Project</label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(Number(e.target.value))}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.code}) — {p.nas_folder_path}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Audit Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Override Scoped Folder Path (Optional)</label>
            <input
              type="text"
              placeholder={selectedProj?.nas_folder_path || '/volume1/NGO_Projects/...'}
              value={scopePath}
              onChange={(e) => setScopePath(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              Leave blank to use default project path ({selectedProj?.nas_folder_path}).
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
            <span className="font-bold text-slate-800 block text-[11px]">Workflow Execution Notice</span>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Execution triggers the 6-stage evidence pipeline: discovery via file-agent, extraction via document-agent, 
              cross-document reconciliation, and 4-tier finding classification. All source records remain read-only.
            </p>
          </div>

          <div className="pt-3 flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 font-medium text-slate-600 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={running}
              className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold transition-colors disabled:opacity-50"
            >
              {running ? 'Executing Audit...' : 'Execute Investigation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
