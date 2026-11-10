import React, { useState, useEffect } from 'react';
import {
  FolderKanban,
  Plus,
  HardDrive,
  ArrowRight
} from 'lucide-react';
import { Project } from '../types';
import { Modal } from '../components/Modal';

interface ProjectsPageProps {
  projects: Project[];
  onRefresh: () => void;
  onAuditProject: (projectId: number) => void;
  onCreateProject: (proj: Partial<Project>) => Promise<void>;
}

export const ProjectsPage: React.FC<ProjectsPageProps> = ({
  projects,
  onAuditProject,
  onCreateProject,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('modal') === 'create_project') {
        setIsModalOpen(true);
      }
    }
  }, []);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [donor, setDonor] = useState('');
  const [budget, setBudget] = useState('50000');
  const [currency, setCurrency] = useState('USD');
  const [nasPath, setNasPath] = useState('/volume1/NGO_Projects/');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !code.trim()) {
      setErrorMsg('Project Name and Code are required.');
      return;
    }
    setErrorMsg(null);
    setSubmitting(true);
    try {
      await onCreateProject({
        name: name.trim(),
        code: code.trim().toUpperCase(),
        donor: donor.trim() || 'Core NGO Fund',
        budget: parseFloat(budget) || 0,
        currency,
        nas_folder_path: nasPath.trim(),
        description: description.trim(),
      });
      setIsModalOpen(false);
      setName('');
      setCode('');
      setDonor('');
      setDescription('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to register project scope.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Configured NGO Grant Projects
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Scoped directories mapped to local UGREEN NAS volumes for read-only evidence investigation.
          </p>
        </div>
        <button
          onClick={() => { setErrorMsg(null); setIsModalOpen(true); }}
          className="w-full sm:w-auto bg-sky-600 hover:bg-sky-500 text-white font-semibold px-4 py-2.5 rounded-xl text-xs sm:text-sm transition-all flex items-center justify-center space-x-2 shadow-xs shrink-0 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Add Project Scope</span>
        </button>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {projects.map((p) => (
          <div
            key={p.id}
            className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <span className="text-[10px] font-mono bg-sky-50 text-sky-700 px-2 py-0.5 rounded-md font-bold uppercase tracking-wider border border-sky-200/70 inline-block">
                    {p.code}
                  </span>
                  <h3 className="text-base font-bold text-slate-900 mt-1.5 leading-snug truncate">
                    {p.name}
                  </h3>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-slate-500 shrink-0">
                  <FolderKanban className="w-5 h-5 text-slate-600" />
                </div>
              </div>

              {p.description && (
                <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                  {p.description}
                </p>
              )}

              <div className="pt-2 grid grid-cols-2 gap-3 text-xs border-t border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[11px] font-medium uppercase tracking-wider">Donor</span>
                  <span className="font-semibold text-slate-800 truncate block">
                    {p.donor || 'Core Institutional'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px] font-medium uppercase tracking-wider">Grant Budget</span>
                  <span className="font-bold text-slate-900 font-mono">
                    ${p.budget.toLocaleString()} {p.currency}
                  </span>
                </div>
              </div>

              {/* Scoped NAS Folder Path */}
              <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100/90 text-[11px] font-mono text-slate-600 flex items-center space-x-1.5 truncate">
                <HardDrive className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="truncate">{p.nas_folder_path}</span>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={() => onAuditProject(p.id)}
                className="w-full bg-slate-50 hover:bg-sky-50 hover:border-sky-300 hover:text-sky-700 border border-slate-200 text-slate-700 font-semibold py-2 px-3 rounded-xl text-xs transition-all flex items-center justify-center space-x-1.5 cursor-pointer"
              >
                <span>Initiate Audit Investigation</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Project Scope Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Configure New Grant Project"
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Project Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Solar Primary Clinic Clean Water"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Project Code *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. PRJ-WASH-2026"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm font-mono uppercase focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Primary Donor
              </label>
              <input
                type="text"
                placeholder="e.g. Global Humanitarian Fund"
                value={donor}
                onChange={(e) => setDonor(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Authorized Budget
              </label>
              <input
                type="number"
                min="0"
                step="100"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm font-mono focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Currency
              </label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm font-semibold bg-white focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="CHF">CHF (Fr)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Scoped NAS Folder Path (Read-Only)
            </label>
            <input
              type="text"
              required
              placeholder="/volume1/NGO_Projects/..."
              value={nasPath}
              onChange={(e) => setNasPath(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm font-mono focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Fenced path traversal enforces zero searches outside this folder.
            </p>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Description
            </label>
            <textarea
              rows={2}
              placeholder="Operational scope, targeted clinical supplies or infrastructure."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-slate-900 text-xs sm:text-sm focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
            />
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
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition-colors disabled:opacity-50 shadow-xs"
            >
              {submitting ? 'Registering...' : 'Register Project'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
