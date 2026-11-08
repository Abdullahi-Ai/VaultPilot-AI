import React, { useEffect, useState } from 'react';
import { 
  DollarSign, 
  AlertCircle, 
  FileSearch, 
  HelpCircle, 
  CheckCircle2, 
  ArrowRight,
  TrendingUp,
  FolderOpen
} from 'lucide-react';
import { StatsCard } from '../components/StatsCard';
import { apiService } from '../services/api';
import { DashboardStats, Project } from '../types';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
  onSelectProjectForAudit: (projectId: number) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate, onSelectProjectForAudit }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiService.getDashboardStats(),
      apiService.getProjects()
    ]).then(([statsData, projectsData]) => {
      setStats(statsData);
      setProjects(projectsData);
      setLoading(false);
    });
  }, []);

  if (loading || !stats) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading compliance dashboard...</div>;
  }

  const usdTotal = stats.verified_spend_by_currency['USD'] || 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-3xl p-8 shadow-lg relative overflow-hidden">
        <div className="max-w-2xl relative z-10">
          <div className="inline-flex items-center space-x-2 bg-sky-500/20 text-sky-300 px-3 py-1 rounded-full text-xs font-semibold mb-4 border border-sky-400/30">
            <span>Uliya v0.7.3 Standard Active</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Financial Evidence Investigation Hub</h2>
          <p className="mt-2 text-slate-300 text-sm leading-relaxed">
            Reconstructing documentary evidence chains across purchase orders, vendor billings, and payment proofs.
            All findings are strictly backed by source paths with zero file mutations on your NAS.
          </p>
          <div className="mt-6 flex items-center space-x-4">
            <button
              onClick={() => onNavigate('investigations')}
              className="bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold px-4 py-2 rounded-xl text-sm transition-colors flex items-center space-x-2"
            >
              <span>View Audit Runs</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('ledger')}
              className="bg-white/10 hover:bg-white/20 text-white font-medium px-4 py-2 rounded-xl text-sm transition-colors"
            >
              Inspect Three-Way Ledger
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatsCard
          title="Verified Spend (USD)"
          value={`$${usdTotal.toLocaleString()}`}
          subtitle="Matching 3-way documented proof"
          icon={DollarSign}
          badge="Reconciled"
          badgeColor="emerald"
        />
        <StatsCard
          title="Confirmed Discrepancies"
          value={stats.findings_by_classification.CONFIRMED_DISCREPANCY}
          subtitle="Direct conflicts between PO & Invoices"
          icon={AlertCircle}
          badge="High Priority"
          badgeColor="rose"
        />
        <StatsCard
          title="Missing Supporting Evidence"
          value={stats.findings_by_classification.MISSING_EVIDENCE}
          subtitle="Invoices lacking payment vouchers"
          icon={FileSearch}
          badge="Scope Bounded"
          badgeColor="amber"
        />
        <StatsCard
          title="Unverified / Blurred Scans"
          value={stats.findings_by_classification.UNVERIFIED}
          subtitle="Partial fields or smudged optical receipts"
          icon={HelpCircle}
          badge="Manual Check"
          badgeColor="sky"
        />
      </div>

      {/* Two Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Projects List */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Active NGO Grant Projects</h3>
              <p className="text-xs text-slate-500 mt-0.5">Configured local NAS storage paths for investigation</p>
            </div>
            <button
              onClick={() => onNavigate('projects')}
              className="text-sky-600 hover:text-sky-700 text-xs font-semibold flex items-center space-x-1"
            >
              <span>Manage Projects</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3.5">
            {projects.map((project) => (
              <div 
                key={project.id}
                className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-900 text-sm">{project.name}</span>
                    <span className="text-[10px] font-mono bg-slate-200/70 text-slate-700 px-2 py-0.5 rounded font-semibold">
                      {project.code}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-slate-500">
                    <span>Donor: <strong className="text-slate-700">{project.donor || 'Core Fund'}</strong></span>
                    <span>•</span>
                    <span>Budget: <strong className="text-slate-700">${project.budget.toLocaleString()} {project.currency}</strong></span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 font-mono">
                    <FolderOpen className="w-3 h-3 text-slate-400" />
                    <span>{project.nas_folder_path}</span>
                  </div>
                </div>

                <button
                  onClick={() => onSelectProjectForAudit(project.id)}
                  className="bg-white border border-slate-200 hover:border-sky-500 hover:text-sky-600 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-sm"
                >
                  Start Audit
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Evidence Status Breakdown */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Reconciliation Status</h3>
            <p className="text-xs text-slate-500 mt-0.5">Evidence completeness across discovered records</p>

            <div className="mt-6 space-y-4">
              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-600 flex items-center space-x-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Reconciled Match</span>
                  </span>
                  <span className="font-bold text-slate-900">{stats.ledger_status_breakdown.RECONCILED_MATCH} items</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '33%' }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-600 flex items-center space-x-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                    <span>Variance Hold</span>
                  </span>
                  <span className="font-bold text-slate-900">{stats.ledger_status_breakdown.VARIANCE_HOLD} items</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-rose-500 h-2 rounded-full" style={{ width: '33%' }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-600 flex items-center space-x-1.5">
                    <FileSearch className="w-3.5 h-3.5 text-amber-600" />
                    <span>Missing Receipt Proof</span>
                  </span>
                  <span className="font-bold text-slate-900">{stats.ledger_status_breakdown.MISSING_RECEIPT} items</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-amber-500 h-2 rounded-full" style={{ width: '33%' }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-slate-600 flex items-center space-x-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-sky-600" />
                    <span>Unverified Smudged</span>
                  </span>
                  <span className="font-bold text-slate-900">{stats.ledger_status_breakdown.UNVERIFIED} items</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-sky-500 h-2 rounded-full" style={{ width: '33%' }}></div>
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 mt-6">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-800">
              <TrendingUp className="w-4 h-4 text-sky-600" />
              <span>Conservative Audit Principle</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
              Missing evidence establishes only absence from the searched folder scope. It does not claim payment never occurred.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
