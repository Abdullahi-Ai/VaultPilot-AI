import React from 'react';
import {
  Cpu,
  ShieldCheck,
  HardDrive,
  FileCode,
  AlertTriangle,
  Info
} from 'lucide-react';

export const UgreenBridgePage: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header Bar */}
      <div className="border-b border-slate-200/80 pb-5">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-200">
            Current Status: Offline Local Emulation
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
            Standard: Uliya v0.7.3
          </span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          UGREEN AI NAS Skill Integration Architecture
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5 max-w-3xl">
          Technical orchestration interface showing how VaultPilot AI delegates evidence discovery and OCR extraction
          to UGOS expert agents under local read-only fences.
        </p>
      </div>

      {/* Hardware Connectivity Status Callout */}
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-50/70 border border-amber-200/90 text-amber-900 space-y-2">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <h3 className="font-bold text-sm sm:text-base text-amber-950">
            Hardware Status: Simulated Local Emulation (`EmulatedNASProvider`)
          </h3>
        </div>
        <p className="text-xs text-amber-800 leading-relaxed">
          Physical hardware binding to the <strong>UGREEN AI NAS iDX6011 Pro</strong> is scheduled for <strong>Round 2 finalist validation</strong> following official device assignment. In this local demonstration, all NAS storage APIs and CLI interactions are simulated against an isolated test workspace to protect physical storage integrity.
        </p>
      </div>

      {/* Verified Architectural Safeguards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 space-y-2.5 shadow-xs">
          <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm">Strict Read-Only Fence</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            All evidence analysis utilizes strictly read-only file descriptors. Source invoices, purchase orders, and receipts on the NAS cannot be altered, moved, or deleted.
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 space-y-2.5 shadow-xs">
          <div className="w-9 h-9 rounded-xl bg-sky-50 border border-sky-200 text-sky-700 flex items-center justify-center">
            <HardDrive className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm">Fenced Path Traversal</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            File discovery is bounded strictly to authorized grant project folder scopes (e.g. <code className="text-sky-700 font-mono">/volume1/NGO_Projects/</code>). NAS-wide sweeps are strictly forbidden.
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 space-y-2.5 shadow-xs">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-700 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm">Declarative Orchestration</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            The submitted Skill ZIP contains pure Markdown agent delegation directives conforming to the Uliya v0.7.3 specification, containing zero unverified executable scripts.
          </p>
        </div>
      </div>

      {/* Provisional Capability Mapping Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <FileCode className="w-5 h-5 text-sky-600 shrink-0" />
            <h3 className="font-bold text-slate-900 text-base">
              Provisional Capability Register (Uliya v0.7.3 Mapping)
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Target: UGOS Pro CLI Bridge
          </span>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs min-w-[620px]">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3">Expert Agent</th>
                <th className="px-4 py-3">Proposed UGOS Capability</th>
                <th className="px-4 py-3">Operation</th>
                <th className="px-4 py-3">Parameters Used</th>
                <th className="px-4 py-3">Validation Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="px-4 py-3.5 font-mono font-bold text-slate-800">file-agent</td>
                <td className="px-4 py-3.5 font-mono text-sky-700">ug-filesystem</td>
                <td className="px-4 py-3.5 font-mono text-slate-700">find</td>
                <td className="px-4 py-3.5 font-mono text-slate-500">path, type="file"</td>
                <td className="px-4 py-3.5">
                  <span className="text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full inline-flex items-center space-x-1">
                    <span>Simulated (Round 2 Target)</span>
                  </span>
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3.5 font-mono font-bold text-slate-800">document-agent</td>
                <td className="px-4 py-3.5 font-mono text-sky-700">ug-document</td>
                <td className="px-4 py-3.5 font-mono text-slate-700">extract_text</td>
                <td className="px-4 py-3.5 font-mono text-slate-500">file_path</td>
                <td className="px-4 py-3.5">
                  <span className="text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full inline-flex items-center space-x-1">
                    <span>Simulated (Round 2 Target)</span>
                  </span>
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3.5 font-mono font-bold text-slate-800">document-agent</td>
                <td className="px-4 py-3.5 font-mono text-sky-700">ug-ocr</td>
                <td className="px-4 py-3.5 font-mono text-slate-700">read_receipt</td>
                <td className="px-4 py-3.5 font-mono text-slate-500">image_path</td>
                <td className="px-4 py-3.5">
                  <span className="text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full inline-flex items-center space-x-1">
                    <span>Simulated (Round 2 Target)</span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs text-slate-600 space-y-1">
          <div className="font-bold text-slate-800 flex items-center space-x-1.5">
            <Info className="w-3.5 h-3.5 text-sky-600" />
            <span>UGREEN Hackathon Rule Adherence Note:</span>
          </div>
          <p className="text-[11px] leading-relaxed">
            Per the official hackathon rules, all CLI capabilities and expert-agent mappings are marked as <strong>proposed integrations</strong> until verified on physical NAS hardware during Round 2.
          </p>
        </div>
      </div>
    </div>
  );
};
