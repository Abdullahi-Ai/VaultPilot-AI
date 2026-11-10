import React, { useEffect, useState } from 'react';
import {
  DollarSign,
  AlertCircle,
  FileSearch,
  HelpCircle,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  FolderOpen,
  ShieldCheck,
  Building2
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
    return (
      <div className="p-12 text-center text-slate-500 font-medium flex items-center justify-center space-x-2 animate-pulse">
        <span>Loading executive compliance dashboard...</span>
      </div>
    );
  }

  const usdTotal = stats.verified_spend_by_currency['USD'] || 0;
  const totalLedgerItems = Object.values(stats.ledger_status_breakdown).reduce((a, b) => a + b, 0) || 1;

  const getPercent = (count: number) => {
    return Math.min(100, Math.max(5, Math.round((count / totalLedgerItems) * 100)));
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-200">
      {/* Executive Hero Banner */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 text-white rounded-2xl sm:rounded-3xl p-5 sm:p-7 lg:p-8 shadow-xl relative overflow-hidden border border-slate-800">
        <div className="max-w-3xl relative z-10 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center space-x-1.5 bg-sky-500/20 text-sky-300 px-3 py-1 rounded-full text-xs font-semibold border border-sky-400/30">
              <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
              <span>UGOS / Uliya Standard v0.7.3 Active</span>
            </span>
            <span className="text-slate-400 text-xs hidden sm:inline">•</span>
            <span className="text-slate-300 text-xs font-mono">Zero Cloud Egress Architecture</span>
          </div>

          <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold tracking-tight text-white">
            Financial Evidence Intelligence Hub
          </h2>

          <p className="text-slate-300 text-xs sm:text-sm leading-relaxed max-w-2xl">
            Correlating documentary proof across Purchase Orders, Commercial Invoices, and Payment Vouchers.
            All findings are strictly pinned to verifiable NAS filesystem paths with read-only integrity.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('investigations')}
              className="w-full sm:w-auto bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold px-4 py-2.5 rounded-xl text-xs sm:text-sm transition-colors flex items-center justify-center space-x-2 shadow-sm"
            >
              <span>Explore Audit Investigations</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('ledger')}
              className="w-full sm:w-auto bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700 font-semibold px-4 py-2.5 rounded-xl text-xs sm:text-sm transition-colors flex items-center justify-center space-x-2"
            >
              <span>Inspect Three-Way Ledger</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <StatsCard
          title="Verified Spend (USD)"
          value={`$${usdTotal.toLocaleString()}`}
          subtitle="Strict 3-way documented proof (PO + Invoice + Receipt)"
          icon={DollarSign}
          badge="Reconciled"
          badgeColor="emerald"
        />
        <StatsCard
          title="Confirmed Discrepancies"
          value={stats.findings_by_classification.CONFIRMED_DISCREPANCY}
          subtitle="Direct conflicts between PO authorization & Invoice"
          icon={AlertCircle}
          badge="High Priority"
          badgeColor="rose"
        />
        <StatsCard
          title="Missing Supporting Evidence"
          value={stats.findings_by_classification.MISSING_EVIDENCE}
          subtitle="Invoices lacking verified disbursement vouchers"
          icon={FileSearch}
          badge="Scope Bounded"
          badgeColor="amber"
        />
        <StatsCard
          title="Unverified / Blurry Scans"
          value={stats.findings_by_classification.UNVERIFIED}
          subtitle="Degraded optical scans requiring manual verification"
          icon={HelpCircle}
          badge="HITL Review"
          badgeColor="sky"
        />
      </div>

      {/* Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8 items-start">
        {/* Active Projects List */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
            <div>
              <h3 className="font-bold text-slate-900 text-base sm:text-lg">Configured Grant Scopes</h3>
              <p className="text-xs text-slate-500 mt-0.5">Authorized project directories mapped to local NAS volumes</p>
            </div>
            <button
              onClick={() => onNavigate('projects')}
              className="text-sky-600 hover:text-sky-700 text-xs font-bold inline-flex items-center space-x-1 self-start sm:self-auto"
            >
              <span>View All Scopes</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {projects.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                No active grant projects registered yet.
              </div>
            ) : (
              projects.map((project) => (
                <div
                  key={project.id}
                  className="p-4 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-slate-50 hover:border-slate-200 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-bold text-slate-900 text-sm truncate">
                        {project.name}
                      </span>
                      <span className="text-[10px] font-mono bg-sky-100/70 text-sky-800 border border-sky-200/60 px-2 py-0.5 rounded font-bold uppercase shrink-0">
                        {project.code}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-y-1 gap-x-3 text-xs text-slate-500">
                      <span className="flex items-center space-x-1">
                        <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>Donor: <strong className="text-slate-700">{project.donor || 'Core NGO Fund'}</strong></span>
                      </span>
                      <span className="hidden sm:inline text-slate-300">•</span>
                      <span>Budget: <strong className="text-slate-800 font-mono">${project.budget.toLocaleString()} {project.currency}</strong></span>
                    </div>

                    <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 font-mono truncate">
                      <FolderOpen className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="truncate">{project.nas_folder_path}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => onSelectProjectForAudit(project.id)}
                    className="w-full sm:w-auto bg-white border border-slate-200 hover:border-sky-500 hover:text-sky-600 text-slate-700 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all shadow-xs shrink-0 text-center"
                  >
                    Run Audit
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Reconciliation Status Breakdown */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col justify-between space-y-6">
          <div className="space-y-5">
            <div className="border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base sm:text-lg">Reconciliation Status</h3>
              <p className="text-xs text-slate-500 mt-0.5">Evidence completeness across analyzed documents</p>
            </div>

            <div className="space-y-4">
              {/* Reconciled Match */}
              <div>
                <div className="flex justify-between text-xs font-medium mb-1.5">
                  <span className="text-slate-700 flex items-center space-x-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Reconciled Match</span>
                  </span>
                  <span className="font-bold text-slate-900 font-mono">
                    {stats.ledger_status_breakdown.RECONCILED_MATCH} items
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${getPercent(stats.ledger_status_breakdown.RECONCILED_MATCH)}%` }}
                  />
                </div>
              </div>

              {/* Variance Hold */}
              <div>
                <div className="flex justify-between text-xs font-medium mb-1.5">
                  <span className="text-slate-700 flex items-center space-x-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                    <span>Variance Hold</span>
                  </span>
                  <span className="font-bold text-slate-900 font-mono">
                    {stats.ledger_status_breakdown.VARIANCE_HOLD} items
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-rose-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${getPercent(stats.ledger_status_breakdown.VARIANCE_HOLD)}%` }}
                  />
                </div>
              </div>

              {/* Missing Receipt Proof */}
              <div>
                <div className="flex justify-between text-xs font-medium mb-1.5">
                  <span className="text-slate-700 flex items-center space-x-1.5">
                    <FileSearch className="w-3.5 h-3.5 text-amber-600" />
                    <span>Missing Receipt Proof</span>
                  </span>
                  <span className="font-bold text-slate-900 font-mono">
                    {stats.ledger_status_breakdown.MISSING_RECEIPT} items
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${getPercent(stats.ledger_status_breakdown.MISSING_RECEIPT)}%` }}
                  />
                </div>
              </div>

              {/* Unverified */}
              <div>
                <div className="flex justify-between text-xs font-medium mb-1.5">
                  <span className="text-slate-700 flex items-center space-x-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-sky-600" />
                    <span>Unverified Smudged</span>
                  </span>
                  <span className="font-bold text-slate-900 font-mono">
                    {stats.ledger_status_breakdown.UNVERIFIED} items
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-sky-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${getPercent(stats.ledger_status_breakdown.UNVERIFIED)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Conservative Audit Principle Callout */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="flex items-center space-x-2 text-xs font-bold text-slate-800">
              <TrendingUp className="w-4 h-4 text-sky-600" />
              <span>Conservative Audit Rule</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
              Missing evidence establishes absence from the scoped folder; it never asserts payment did not occur elsewhere.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
