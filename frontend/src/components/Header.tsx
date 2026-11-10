import React, { useState, useEffect } from 'react';
import {
  Menu,
  HardDrive,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { DataSourceState } from '../types';
import { apiService } from '../services/api';

interface HeaderProps {
  currentTab: string;
  onOpenMobileNav?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onOpenMobileNav }) => {
  const [dataSource, setDataSource] = useState<DataSourceState>(apiService.getDataSourceState());
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    const unsubscribe = apiService.subscribeToDataSource((state) => {
      setDataSource(state);
    });
    apiService.checkBackendHealth();
    return () => unsubscribe();
  }, []);

  const handleToggleDemo = () => {
    if (dataSource === 'DEMO_DATA') {
      apiService.setDemoMode(false);
    } else {
      apiService.setDemoMode(true);
    }
  };

  const handleManualCheck = async () => {
    setChecking(true);
    try {
      await apiService.checkBackendHealth();
    } finally {
      setChecking(false);
    }
  };

  const getTitle = () => {
    switch (currentTab) {
      case 'dashboard': return 'Executive Financial Compliance Overview';
      case 'projects': return 'Grant Projects & Scoped Volumes';
      case 'investigations': return 'Evidence Audits & Investigations';
      case 'reviews': return 'Evidence Review & Verification Queue';
      case 'ledger': return 'Three-Way Evidence Reconciliation Ledger';
      case 'findings': return 'Four-Tier Classified Findings & Gaps';
      case 'ugreen': return 'UGREEN AI NAS Skill Integration Architecture';
      default: return 'VaultPilot AI';
    }
  };

  const getShortTitle = () => {
    switch (currentTab) {
      case 'dashboard': return 'Dashboard';
      case 'projects': return 'Grant Projects';
      case 'investigations': return 'Investigations';
      case 'reviews': return 'Evidence Review';
      case 'ledger': return 'Reconciliation Ledger';
      case 'findings': return 'Audit Findings';
      case 'ugreen': return 'NAS Skill Bridge';
      default: return 'VaultPilot AI';
    }
  };

  return (
    <header className="bg-white border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 py-3.5 sticky top-0 z-20 shadow-xs">
      <div className="flex items-center justify-between gap-3 min-w-0">
        {/* Left: Mobile Toggle + Title */}
        <div className="flex items-center space-x-3 min-w-0">
          {onOpenMobileNav && (
            <button
              onClick={onOpenMobileNav}
              className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 shrink-0"
              aria-label="Open mobile navigation"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div className="min-w-0">
            <h1 className="text-base sm:text-lg lg:text-xl font-bold text-slate-900 tracking-tight truncate hidden sm:block">
              {getTitle()}
            </h1>
            <h1 className="text-base font-bold text-slate-900 tracking-tight truncate sm:hidden">
              {getShortTitle()}
            </h1>
            <p className="text-[11px] text-slate-500 hidden md:block truncate">
              Every transaction needs evidence. Every finding needs a source.
            </p>
          </div>
        </div>

        {/* Right: Status Badges & Mode Indicators */}
        <div className="flex items-center space-x-2 shrink-0">
          {/* Backend Status Pill */}
          {dataSource === 'LIVE_BACKEND' ? (
            <div
              onClick={handleManualCheck}
              className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-pointer hover:bg-emerald-100/70 transition-colors"
              title="Connected to live FastAPI backend at localhost:8000"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="hidden sm:inline">Live Backend</span>
              <span className="sm:hidden text-[10px]">Live</span>
            </div>
          ) : (
            <div
              onClick={handleManualCheck}
              className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 cursor-pointer hover:bg-rose-100 transition-colors"
              title="Backend disconnected. Click to recheck."
            >
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              <span className="hidden sm:inline">Offline</span>
              <RefreshCw className={`w-3 h-3 ${checking ? 'animate-spin' : ''}`} />
            </div>
          )}

          {/* Demo Mode Toggle Button */}
          <button
            onClick={handleToggleDemo}
            className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all ${
              dataSource === 'DEMO_DATA'
                ? 'bg-purple-100 text-purple-800 border-purple-300 shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
            }`}
            title="Toggle between Isolated Demo Mode and Direct Backend Mode"
          >
            <Sparkles className="w-3 h-3 text-purple-600" />
            <span className="hidden sm:inline">Demo Mode</span>
            <span className="sm:hidden text-[10px]">Demo</span>
          </button>

          {/* Read-Only NAS Badge */}
          <div className="hidden md:inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <HardDrive className="w-3 h-3 text-slate-500" />
            <span className="text-[11px] font-mono">NAS: Read-Only</span>
          </div>
        </div>
      </div>
    </header>
  );
};
