import React from 'react';
import { 
  LayoutDashboard, 
  FolderKanban, 
  SearchCode, 
  TableProperties, 
  AlertTriangle, 
  Cpu, 
  FileText
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'projects', label: 'Grant Projects', icon: FolderKanban },
    { id: 'investigations', label: 'Investigations', icon: SearchCode },
    { id: 'ledger', label: 'Evidence Ledger', icon: TableProperties },
    { id: 'findings', label: 'Findings & Gaps', icon: AlertTriangle },
    { id: 'ugreen', label: 'UGREEN NAS Skill', icon: Cpu },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-sky-500/20">
          VP
        </div>
        <div>
          <span className="font-bold text-white tracking-tight text-base block">VaultPilot AI</span>
          <span className="text-[10px] text-sky-400 font-medium tracking-wide uppercase">NGO Evidence Intelligence</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1.5 flex-1">
        <div className="px-3 pb-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          Compliance Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30'
                  : 'hover:bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${active ? 'text-sky-400' : 'text-slate-500'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 m-4 rounded-xl bg-slate-950/60 border">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <FileText className="w-3.5 h-3.5 text-sky-400" />
          <span className="font-semibold text-slate-300">Skill v0.7.3 Spec</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">
          UGOS Pro compliant read-only financial evidence orchestrator.
        </p>
      </div>
    </aside>
  );
};
