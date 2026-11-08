import React, { useState } from 'react';
import { FolderKanban, Plus, ExternalLink, HardDrive, Shield } from 'lucide-react';
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
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [donor, setDonor] = useState('');
  const [budget, setBudget] = useState('50000');
  const [currency, setCurrency] = useState('USD');
  const [nasPath, setNasPath] = useState('/volume1/NGO_Projects/');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onCreateProject({
        name,
        code,
        donor,
        budget: parseFloat(budget) || 0,
        currency,
        nas_folder_path: nasPath,
        description,
      });
      setIsModalOpen(false);
      setName('');
      setCode('');
      setDonor('');
      setDescription('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Configured NGO Grant Projects</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Scoped directories mapped to local UGREEN NAS volumes for read-only evidence investigation.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-sky-600 hover:bg-sky-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors flex items-center space-x-2 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Add Project Scope</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {projects.map((p) => (
          <div key={p.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-mono bg-sky-50 text-sky-700 px-2.5 py-1 rounded-md font-bold uppercase tracking-wider border border-sky-100">
                    {p.code}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 mt-2">{p.name}</h3>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 text-slate-400">
                  <FolderKanban className="w-5 h-5 text-slate-600" />
                </div>
              </div>

              {p.description && (
                <p className="text-xs text-slate-600 leading-relaxed">{p.description}</p>
              )}

              <div className="pt-2 grid grid-cols-2 gap-3 text-xs border-t border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[11px]">Primary Donor</span>
                  <span className="font-semibold text-slate-800">{p.donor || 'Core Institutional'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Authorized Grant Budget</span>
                  <span className="font-semibold text-slate-800">${p.budget.toLocaleString()} {p.currency}</span>
                </div>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-1">
                <div className="flex items-center space-x-1.5 text-[11px] font-semibold text-slate-600">
                  <HardDrive className="w-3.5 h-3.5 text-sky-600" />
                  <span>Scoped NAS Volume Path</span>
                </div>
                <div className="font-mono text-xs text-slate-700 truncate select-all">
                  {p.nas_folder_path}
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
              <div className="flex items-center space-x-1.5 text-xs text-emerald-700 font-medium">
                <Shield className="w-3.5 h-3.5" />
                <span>Read-Only Fenced</span>
              </div>
              <button
                onClick={() => onAuditProject(p.id)}
                className="bg-slate-900 hover:bg-slate-800 text-white font-medium px-4 py-2 rounded-xl text-xs flex items-center space-x-1.5 transition-colors shadow-sm"
              >
                <span>Run Evidence Audit</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* New Project Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Register Project Scope">
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Project Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Rural Water Sanitation Project"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Project Code</label>
              <input
                type="text"
                required
                placeholder="e.g. PRJ-WASH-2026"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Primary Donor</label>
              <input
                type="text"
                placeholder="e.g. Global Humanitarian Fund"
                value={donor}
                onChange={(e) => setDonor(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Grant Budget</label>
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Base Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="KES">KES (KSh)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">NAS Scoped Folder Path</label>
            <input
              type="text"
              required
              placeholder="/volume1/NGO_Projects/..."
              value={nasPath}
              onChange={(e) => setNasPath(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              Search is strictly fenced to this directory. Root searches are prohibited.
            </span>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Project Description</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of grant objectives..."
              className="w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
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
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold transition-colors disabled:opacity-50"
            >
              {submitting ? 'Registering...' : 'Save Project Scope'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
