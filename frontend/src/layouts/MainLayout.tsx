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

  useEffect(() => {
    const unsub = apiService.subscribeToDataSource((state) => {
      setDataSource(state);
    });
    return () => unsub();
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar currentTab={currentTab} onSelectTab={onSelectTab} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header currentTab={currentTab} />

        {/* Warning Banner when Backend is Offline */}
        {dataSource === 'BACKEND_OFFLINE' && (
          <div className="bg-rose-50 border-b border-rose-200 px-8 py-2.5 text-xs text-rose-800 flex items-center justify-between animate-in fade-in">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>
                <strong>Backend Unavailable:</strong> Could not connect to FastAPI server at <code className="bg-rose-100 px-1 py-0.5 rounded text-rose-900 font-mono">http://localhost:8000</code>.
                Displaying offline demonstration fixtures. Live database updates are paused.
              </span>
            </div>
            <button
              onClick={() => apiService.checkBackendHealth()}
              className="flex items-center space-x-1 text-xs font-semibold text-rose-700 hover:text-rose-900 underline ml-4 flex-shrink-0"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry Connection</span>
            </button>
          </div>
        )}

        {/* Informative Banner when Demo Mode is explicitly active */}
        {dataSource === 'DEMO_DATA' && (
          <div className="bg-purple-50 border-b border-purple-200 px-8 py-2 text-xs text-purple-800 flex items-center justify-between animate-in fade-in">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-purple-600 flex-shrink-0" />
              <span>
                <strong>Demo Mode Active:</strong> You are exploring verified NGO financial audit demonstration scenarios.
              </span>
            </div>
            <button
              onClick={() => apiService.setDemoMode(false)}
              className="text-xs font-semibold text-purple-700 hover:text-purple-900 underline ml-4 flex-shrink-0"
            >
              Switch to Live Backend
            </button>
          </div>
        )}

        <main className="flex-1 p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
