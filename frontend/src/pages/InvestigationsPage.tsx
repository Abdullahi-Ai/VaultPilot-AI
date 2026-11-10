import React, { useState, useEffect } from 'react';
import {
  SearchCode,
  Play,
  Calendar,
  CheckCircle,
  ChevronRight,
  RefreshCw,
  FolderOpen
} from 'lucide-react';
import { Investigation, Project } from '../types';
import { Modal } from '../components/Modal';
import { apiService } from '../services/api';

interface InvestigationsPageProps {
  investigations: Investigation[];
  projects: Project[];
  selectedProjectId?: number;
  onTriggerAudit: (projectId: number, scopePath?: string, title?: string) => Promise<void>;
  onViewInvestigationDetails: (inv: Investigation) => void;
  onRefreshAll?: () => Promise<void>;
}

export const InvestigationsPage: React.FC<InvestigationsPageProps> = ({
  investigations,
  projects,
  selectedProjectId,
  onTriggerAudit,
  onViewInvestigationDetails,
  onRefreshAll
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('modal') === 'run_investigation') {
        setIsModalOpen(true);
      }
    }
  }, []);
  const [projectId, setProjectId] = useState<number>(selectedProjectId || (projects[0]?.id || 1));
  const [title, setTitle] = useState('Routine Financial Evidence Audit');
  const [scopePath, setScopePath] = useState('');
  const [running, setRunning] = useState(false);
  const [reconcilingId, setReconcilingId] = useState<number | null>(null);

  const selectedProj = projects.find(p => p.id === projectId);

  const handleReconcile = async (e: React.MouseEvent, invId: number) => {
    e.stopPropagation();
    setReconcilingId(invId);
    try {
      const updated = await apiService.reconcileInvestigation(invId);
      if (onRefreshAll) {
        await onRefreshAll();
      }
      onViewInvestigationDetails(updated);
    } catch (err: any) {
      alert(`Reconciliation failed: ${err.message || 'Unknown error'}`);
    } finally {
      setReconcilingId(null);
    }
  };

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
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Financial Evidence Investigations
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Audit runs that discover files, extract records, cross-examine evidence chains, and seal immutable reports.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="w-full sm:w-auto bg-sky-600 hover:bg-sky-500 text-white font-semibold px-4 py-2.5 rounded-xl text-xs sm:text-sm transition-all flex items-center justify-center space-x-2 shadow-xs shrink-0 cursor-pointer"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Launch Investigation</span>
        </button>
      </div>

      {/* Investigations List */}
      <div className="space-y-4">
        {investigations.length === 0 ? (
          <div className="bg-white p-10 sm:p-14 text-center rounded-2xl border border-slate-200/90 shadow-xs">
            <SearchCode className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-700">No Investigations Executed Yet</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Launch an audit investigation to scan an authorized NAS folder and correlate financial evidence.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-4 bg-sky-600 text-white px-4 py-2 rounded-xl text-xs font-semibold hover:bg-sky-500 transition-colors shadow-xs"
            >
              Start First Audit
            </button>
          </div>
        ) : (
          investigations.map((inv) => {
            const project = projects.find(p => p.id === inv.project_id);
            const isReconciling = reconcilingId === inv.id;

            return (
              <div
                key={inv.id}
                onClick={() => onViewInvestigationDetails(inv)}
                className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/90 hover:border-sky-300 hover:shadow-md transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
              >
                <div className="space-y-2 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-slate-900 text-base group-hover:text-sky-600 transition-colors truncate">
                      {inv.title}
                    </span>
                    <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80 px-2 py-0.5 rounded-full inline-flex items-center space-x-1 shrink-0">
                      <CheckCircle className="w-2.5 h-2.5" />
                      <span>{inv.status}</span>
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-y-1 gap-x-3 text-xs text-slate-500">
                    <span>Scope: <strong className="text-slate-800">{project?.name || `Project #${inv.project_id}`}</strong></span>
                    <span className="hidden sm:inline text-slate-300">•</span>
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{new Date(inv.created_at).toLocaleDateString()}</span>
                    </span>
                  </div>

                  <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 font-mono truncate">
                    <FolderOpen className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{inv.scope_path}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0 self-end md:self-center">
                  <button
                    onClick={(e) => handleReconcile(e, inv.id)}
                    disabled={isReconciling}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 hover:text-emerald-700 text-slate-600 text-xs font-semibold transition-all flex items-center space-x-1.5"
                    title="Re-run reconciliation matching on this investigation"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isReconciling ? 'animate-spin text-emerald-600' : ''}`} />
                    <span>{isReconciling ? 'Reconciling...' : 'Re-Reconcile'}</span>
                  </button>

                  <div className="p-2 rounded-xl bg-slate-50 text-slate-400 group-hover:bg-sky-50 group-hover:text-sky-600 transition-all">
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Launch Investigation Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Launch Financial Evidence Investigation"
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleStartAudit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Audit Run Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Target Grant Project *
            </label>
            <select
              value={projectId}
              onChange={(e) => {
                const pid = Number(e.target.value);
                setProjectId(pid);
                const p = projects.find(x => x.id === pid);
                if (p) setScopePath(p.nas_folder_path);
              }}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm font-semibold bg-white focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.code}) — ${p.budget.toLocaleString()} {p.currency}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Scoped NAS Folder Path (Read-Only)
            </label>
            <input
              type="text"
              placeholder={selectedProj?.nas_folder_path || '/volume1/NGO_Projects/Audit'}
              value={scopePath}
              onChange={(e) => setScopePath(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm font-mono focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Evidence discovery strictly stays within this folder. No deletion or movement occurs.
            </p>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={running}
              className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition-colors disabled:opacity-50 shadow-xs flex items-center space-x-1.5"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{running ? 'Executing Audit...' : 'Execute Investigation'}</span>
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
