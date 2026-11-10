import React, { useState, useEffect } from 'react';
import { AlertTriangle, Sparkles, RefreshCw } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { DataSourceState } from '../types';
import { apiService } from '../services/api';

interface MainLayoutProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ currentTab, onSelectTab, children }) => {
  const [dataSource, setDataSource] = useState<DataSourceState>(apiService.getDataSourceState());
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  useEffect(() => {
    const unsub = apiService.subscribeToDataSource((state) => {
      setDataSource(state);
    });
    return () => unsub();
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800">
      {/* Responsive Sidebar (Persistent on desktop, Drawer on mobile) */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={onSelectTab}
        isOpen={isMobileNavOpen}
        onClose={() => setIsMobileNavOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Responsive Header */}
        <Header
          currentTab={currentTab}
          onOpenMobileNav={() => setIsMobileNavOpen(true)}
        />

        {/* Warning Banner when Backend is Offline */}
        {dataSource === 'BACKEND_OFFLINE' && (
          <div className="bg-rose-50 border-b border-rose-200 px-4 sm:px-6 py-2.5 text-xs text-rose-800 flex flex-wrap items-center justify-between gap-2 animate-in fade-in">
            <div className="flex items-center space-x-2 min-w-0">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span className="truncate">
                <strong>Backend Unavailable:</strong> Could not reach FastAPI at <code className="bg-rose-100 px-1 py-0.5 rounded text-rose-900 font-mono">localhost:8000</code>. Displaying fixtures.
              </span>
            </div>
            <button
              onClick={() => apiService.checkBackendHealth()}
              className="flex items-center space-x-1 text-xs font-semibold text-rose-700 hover:text-rose-900 underline shrink-0 cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry Connection</span>
            </button>
          </div>
        )}

        {/* Informative Banner when Demo Mode is explicitly active */}
        {dataSource === 'DEMO_DATA' && (
          <div className="bg-purple-50 border-b border-purple-200 px-4 sm:px-6 py-2 text-xs text-purple-800 flex flex-wrap items-center justify-between gap-2 animate-in fade-in">
            <div className="flex items-center space-x-2 min-w-0">
              <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
              <span className="truncate">
                <strong>Isolated Demo Database Active:</strong> Exploring verified financial evidence scenarios without modifying production data.
              </span>
            </div>
            <button
              onClick={() => apiService.setDemoMode(false)}
              className="text-xs font-semibold text-purple-700 hover:text-purple-900 underline shrink-0 cursor-pointer"
            >
              Switch to Live Backend
            </button>
          </div>
        )}

        {/* Responsive Main Body */}
        <main className="flex-1 p-3.5 sm:p-5 lg:p-8 max-w-7xl w-full mx-auto min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
};
