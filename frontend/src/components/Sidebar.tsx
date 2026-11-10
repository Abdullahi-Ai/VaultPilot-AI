import React from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  SearchCode,
  TableProperties,
  AlertTriangle,
  Cpu,
  FileCheck2,
  X,
  Shield
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  isOpen = false,
  onClose
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null },
    { id: 'projects', label: 'Grant Projects', icon: FolderKanban, badge: null },
    { id: 'investigations', label: 'Investigations', icon: SearchCode, badge: null },
    { id: 'reviews', label: 'Evidence Review', icon: FileCheck2, badge: 'HITL' },
    { id: 'ledger', label: 'Evidence Ledger', icon: TableProperties, badge: '3-Way' },
    { id: 'findings', label: 'Findings & Gaps', icon: AlertTriangle, badge: '4-Tier' },
    { id: 'ugreen', label: 'UGREEN NAS Skill', icon: Cpu, badge: 'v0.7.3' },
  ];

  const handleSelect = (id: string) => {
    onSelectTab(id);
    if (onClose) {
      onClose();
    }
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-slate-900 text-slate-300 w-64 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-md shadow-sky-500/20 shrink-0">
            VP
          </div>
          <div className="min-w-0">
            <span className="font-bold text-white tracking-tight text-base block truncate">VaultPilot AI</span>
            <span className="text-[10px] text-sky-400 font-semibold tracking-wider uppercase block truncate">Financial Evidence Hub</span>
          </div>
        </div>
        {/* Mobile close button */}
        {onClose && (
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="p-3.5 space-y-1 flex-1 overflow-y-auto custom-scrollbar">
        <div className="px-3 pb-2 pt-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          Compliance Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleSelect(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 font-semibold shadow-sm'
                  : 'hover:bg-slate-800/80 text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0">
                <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-sky-400' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-mono font-semibold uppercase tracking-wide shrink-0 ${
                  active
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Technical Spec Box */}
      <div className="p-3.5 border-t border-slate-800/80 bg-slate-950/40 m-3 rounded-xl border border-slate-800/60">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-1.5 text-slate-300 font-semibold">
            <Shield className="w-3.5 h-3.5 text-sky-400" />
            <span>Uliya v0.7.3</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-1.5 py-0.5 rounded">
            EMULATED
          </span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
          UGOS Pro compliant read-only financial evidence orchestrator.
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:flex shrink-0 min-h-screen sticky top-0 h-screen z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Backdrop & Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/70 backdrop-blur-sm transition-opacity animate-in fade-in duration-200"
            onClick={onClose}
            aria-hidden="true"
          />
          {/* Slide-over Panel */}
          <div className="fixed inset-y-0 left-0 max-w-full flex z-50 animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
