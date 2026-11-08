import React, { useState, useEffect } from 'react';
import { ShieldCheck, HardDrive, Bell, Database, AlertCircle, Sparkles, RefreshCw } from 'lucide-react';
import { DataSourceState } from '../types';
import { apiService } from '../services/api';

interface HeaderProps {
  currentTab: string;
}

export const Header: React.FC<HeaderProps> = ({ currentTab }) => {
  const [dataSource, setDataSource] = useState<DataSourceState>(apiService.getDataSourceState());
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    const unsubscribe = apiService.subscribeToDataSource((state) => {
      setDataSource(state);
    });
    // Initial health check on mount
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
      case 'ledger': return 'Three-Way Evidence Traceability Ledger';
      case 'findings': return 'Four-Tier Classified Findings & Gaps';
      case 'ugreen': return 'UGREEN AI NAS Skill Integration Status';
      default: return 'VaultPilot AI';
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{getTitle()}</h1>
        <p className="text-xs text-slate-500 mt-0.5">Every transaction needs evidence. Every finding needs a source.</p>
      </div>

      <div className="flex items-center space-x-3">
        {/* Explicit Data Source Indicator Badge */}
        {dataSource === 'LIVE_BACKEND' && (
          <div
            title="Connected to live FastAPI backend at http://localhost:8000"
            className="flex items-center space-x-2 bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full text-xs font-semibold border border-emerald-300 shadow-sm"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <Database className="w-3.5 h-3.5" />
            <span>LIVE BACKEND</span>
          </div>
        )}

        {dataSource === 'DEMO_DATA' && (
          <div
            title="Viewing demonstration audit fixtures. Live database queries are paused."
            className="flex items-center space-x-2 bg-purple-50 text-purple-700 px-3 py-1 rounded-full text-xs font-semibold border border-purple-300 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>DEMO DATA</span>
          </div>
        )}

        {dataSource === 'BACKEND_OFFLINE' && (
          <div
            title="Backend at localhost:8000 is unreachable. Displaying cached demo fixtures."
            className="flex items-center space-x-2 bg-rose-50 text-rose-700 px-3 py-1 rounded-full text-xs font-semibold border border-rose-300 shadow-sm animate-pulse"
          >
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>BACKEND OFFLINE</span>
          </div>
        )}

        {/* Mode Switcher / Refresh */}
        <button
          onClick={handleToggleDemo}
          className="text-xs font-medium px-2.5 py-1 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
          title="Toggle between Live Backend and Demo Mode"
        >
          {dataSource === 'DEMO_DATA' ? 'Exit Demo' : 'Demo Mode'}
        </button>

        <button
          onClick={handleManualCheck}
          disabled={checking}
          className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          title="Refresh backend connectivity"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${checking ? 'animate-spin text-sky-600' : ''}`} />
        </button>

        <div className="h-4 w-px bg-slate-200 mx-1"></div>

        {/* NAS Status Badge */}
        <div className="flex items-center space-x-2 bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-medium border border-slate-200">
          <HardDrive className="w-3.5 h-3.5 text-slate-500" />
          <span>UGOS NAS: Read-Only Scoped</span>
        </div>

        {/* Security Badge */}
        <div className="flex items-center space-x-1.5 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-medium border border-blue-200">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Fenced Sandbox</span>
        </div>

        <button className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-amber-500 rounded-full"></span>
        </button>
      </div>
    </header>
  );
};
