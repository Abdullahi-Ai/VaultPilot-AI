import React from 'react';
import { Cpu, ShieldCheck, HardDrive, FileCode, CheckCircle2 } from 'lucide-react';

export const UgreenBridgePage: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      <div>
        <h2 className="text-xl font-bold text-slate-900">UGREEN AI NAS Skill Integration Architecture</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          How the VaultPilot AI Web Application interfaces safely with the Uliya Skill Standard v0.7.3.
        </p>
      </div>

      {/* Grid of Key Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-2 shadow-sm">
          <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm">Strict Read-Only Fence</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            All operations preserve original source documents. Zero file deletion, moving, or modifying capabilities are enabled.
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-2 shadow-sm">
          <div className="w-9 h-9 rounded-xl bg-sky-50 border border-sky-200 text-sky-700 flex items-center justify-center">
            <HardDrive className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm">Fenced Path Traversal</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Discovery is strictly bounded to user-authorized project folders (e.g. <code className="text-sky-700 font-mono">/volume1/NGO_Projects/</code>). Drive-wide searches are blocked.
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-2 shadow-sm">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-700 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm">Declarative Orchestration</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            The core Skill uses pure Markdown delegation to <code className="text-indigo-700 font-mono">file-agent</code> and <code className="text-indigo-700 font-mono">document-agent</code>.
          </p>
        </div>
      </div>

      {/* Capability Mapping Table */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center space-x-2">
          <FileCode className="w-5 h-5 text-sky-600" />
          <h3 className="font-bold text-slate-900 text-base">Provisional Capability Mapping (v0.7.3)</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3">Expert Agent</th>
                <th className="px-4 py-3">UGOS Capability</th>
                <th className="px-4 py-3">Provisional Operation</th>
                <th className="px-4 py-3">Parameters Used</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="px-4 py-3 font-mono font-bold text-slate-800">file-agent</td>
                <td className="px-4 py-3 font-mono text-sky-700">ug-filesystem</td>
                <td className="px-4 py-3 font-mono text-slate-700">find</td>
                <td className="px-4 py-3 font-mono text-slate-500">path, type="file"</td>
                <td className="px-4 py-3">
                  <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full inline-flex items-center space-x-1">
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    <span>Mapped (Provisional)</span>
                  </span>
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono font-bold text-slate-800">document-agent</td>
                <td className="px-4 py-3 font-mono text-sky-700">ug-document</td>
                <td className="px-4 py-3 font-mono text-slate-700">extract</td>
                <td className="px-4 py-3 font-mono text-slate-500">query, file, schema</td>
                <td className="px-4 py-3">
                  <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full inline-flex items-center space-x-1">
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    <span>Mapped (Provisional)</span>
                  </span>
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono font-bold text-slate-800">document-agent</td>
                <td className="px-4 py-3 font-mono text-sky-700">ug-document</td>
                <td className="px-4 py-3 font-mono text-slate-700">reconcile</td>
                <td className="px-4 py-3 font-mono text-slate-500">file, query</td>
                <td className="px-4 py-3">
                  <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full inline-flex items-center space-x-1">
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    <span>Mapped (Provisional)</span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Package Separation Notice */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-sm space-y-2">
        <h4 className="font-bold text-sm text-sky-400">Architectural Separation Guarantee</h4>
        <p className="text-xs text-slate-300 leading-relaxed">
          The UGREEN NAS Skill submission package (<code className="text-sky-300 font-mono">dist/vaultpilot-skill.zip</code>) 
          contains strictly Markdown files conforming to the Uliya Skill Standard. 
          This web application (React + Vite + FastAPI + PostgreSQL) exists as a separate post-hackathon foundation 
          and is never bundled into the submission archive.
        </p>
      </div>
    </div>
  );
};
