import { useState, useEffect } from 'react';
import { MainLayout } from './layouts/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { InvestigationsPage } from './pages/InvestigationsPage';
import { EvidenceLedgerPage } from './pages/EvidenceLedgerPage';
import { FindingsPage } from './pages/FindingsPage';
import { UgreenBridgePage } from './pages/UgreenBridgePage';
import { ReviewsPage } from './pages/ReviewsPage';
import { apiService } from './services/api';
import { Project, Investigation, Finding, EvidenceLedgerEntry, InvestigationReportSummary } from './types';
import { Modal } from './components/Modal';
import { FileDown, FileSpreadsheet, FileCode, CheckCircle2, ShieldCheck, RefreshCw } from 'lucide-react';

export function App() {
  const getInitialTab = (): string => {
    if (typeof window !== 'undefined') {
      const hash = window.location.hash.replace('#', '');
      if (['dashboard', 'projects', 'investigations', 'reviews', 'ledger', 'findings', 'ugreen'].includes(hash)) {
        return hash;
      }
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab');
      if (tab && ['dashboard', 'projects', 'investigations', 'reviews', 'ledger', 'findings', 'ugreen'].includes(tab)) {
        return tab;
      }
    }
    return 'dashboard';
  };

  const [currentTab, setCurrentTab] = useState<string>(getInitialTab);
  const [projects, setProjects] = useState<Project[]>([]);
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [ledgerEntries, setLedgerEntries] = useState<EvidenceLedgerEntry[]>([]);
  const [selectedAuditProjectId, setSelectedAuditProjectId] = useState<number | undefined>();
  const [selectedInvestigation, setSelectedInvestigation] = useState<Investigation | null>(null);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (['dashboard', 'projects', 'investigations', 'reviews', 'ledger', 'findings', 'ugreen'].includes(hash)) {
        setCurrentTab(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleTabSelect = (tab: string) => {
    setCurrentTab(tab);
    if (typeof window !== 'undefined' && window.location.hash !== `#${tab}`) {
      window.location.hash = tab;
    }
  };

  // Reporting and Export states
  const [investigationReports, setInvestigationReports] = useState<InvestigationReportSummary[]>([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<string>('reconciliation');

  const loadAllData = async () => {
    try {
      const [projs, invs, fnds, ldgr] = await Promise.all([
        apiService.getProjects(),
        apiService.getInvestigations(),
        apiService.getFindings(),
        apiService.getLedgerEntries(),
      ]);
      setProjects(projs);
      setInvestigations(invs);
      setFindings(fnds);
      setLedgerEntries(ldgr);

      if (typeof window !== 'undefined' && invs.length > 0) {
        const params = new URLSearchParams(window.location.search);
        const invParam = params.get('modal_inv');
        if (invParam) {
          const id = parseInt(invParam, 10);
          const match = invs.find(i => i.id === id) || invs[0];
          if (match) {
            handleSelectInvestigation(match);
          }
        }
      }
    } catch (e) {
      console.warn('Failed to load initial data from API:', e);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleCreateProject = async (proj: Partial<Project>) => {
    await apiService.createProject(proj);
    await loadAllData();
  };

  const handleTriggerAudit = async (projectId: number, scopePath?: string, title?: string) => {
    const targetFolder = scopePath || '/volume1/NGO_Projects/Solar_Water_2026';
    const newInv = await apiService.triggerInvestigation(projectId, targetFolder, title);
    await loadAllData();
    handleSelectInvestigation(newInv);
  };

  const handleSelectProjectForAudit = (projectId: number) => {
    setSelectedAuditProjectId(projectId);
    handleTabSelect('investigations');
  };

  const handleSelectInvestigation = async (inv: Investigation) => {
    setSelectedInvestigation(inv);
    setLoadingReports(true);
    try {
      const reports = await apiService.getInvestigationReports(inv.id);
      setInvestigationReports(reports);
    } catch (err) {
      console.warn('Could not load reports for investigation:', err);
    } finally {
      setLoadingReports(false);
    }
  };

  const handleGenerateReportSnapshot = async () => {
    if (!selectedInvestigation) return;
    setGeneratingReport(true);
    try {
      const newReport = await apiService.createInvestigationReport(
        selectedInvestigation.id,
        `${selectedInvestigation.title} — Official Audit Dossier`
      );
      setInvestigationReports(prev => [newReport, ...prev]);
    } catch (err: any) {
      alert(`Report snapshot creation failed: ${err.message || 'Unknown error'}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <MainLayout currentTab={currentTab} onSelectTab={handleTabSelect}>
      {currentTab === 'dashboard' && (
        <DashboardPage
          onNavigate={handleTabSelect}
          onSelectProjectForAudit={handleSelectProjectForAudit}
        />
      )}

      {currentTab === 'projects' && (
        <ProjectsPage
          projects={projects}
          onRefresh={loadAllData}
          onAuditProject={handleSelectProjectForAudit}
          onCreateProject={handleCreateProject}
        />
      )}

      {currentTab === 'investigations' && (
        <InvestigationsPage
          investigations={investigations}
          projects={projects}
          selectedProjectId={selectedAuditProjectId}
          onTriggerAudit={handleTriggerAudit}
          onViewInvestigationDetails={handleSelectInvestigation}
          onRefreshAll={loadAllData}
        />
      )}

      {currentTab === 'reviews' && (
        <ReviewsPage projects={projects} />
      )}

      {currentTab === 'ledger' && (
        <EvidenceLedgerPage entries={ledgerEntries} />
      )}

      {currentTab === 'findings' && (
        <FindingsPage findings={findings} />
      )}

      {currentTab === 'ugreen' && (
        <UgreenBridgePage />
      )}

      {/* Investigation Details & Sealed Dossier Modal */}
      <Modal
        isOpen={selectedInvestigation !== null}
        onClose={() => setSelectedInvestigation(null)}
        title={selectedInvestigation?.title || 'Investigation Summary'}
        maxWidth="max-w-3xl"
      >
        {selectedInvestigation && (
          <div className="space-y-5 text-xs">
            {/* Scoped Summary Card */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-2.5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                <span className="text-slate-500 font-medium">Scoped NAS Path:</span>
                <span className="font-mono text-slate-900 font-semibold break-all text-[11px] sm:text-xs">
                  {selectedInvestigation.scope_path}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-medium">Discovered Files Analyzed:</span>
                <span className="font-semibold text-slate-900">{selectedInvestigation.document_count} files</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-medium">Execution Status:</span>
                <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  {selectedInvestigation.status}
                </span>
              </div>
              <div className="flex justify-between items-center pt-1 border-t border-slate-200/60">
                <span className="text-slate-600 font-bold">Verified Reconciled Spend:</span>
                <span className="font-bold text-slate-900 font-mono text-sm">
                  ${(selectedInvestigation.verified_totals['USD'] || 0).toLocaleString()} USD
                </span>
              </div>
            </div>

            {selectedInvestigation.summary && (
              <div className="p-3.5 rounded-xl bg-sky-50/60 border border-sky-100 space-y-1">
                <span className="font-bold text-sky-950 block">Audit Summary:</span>
                <p className="text-slate-700 leading-relaxed text-xs">{selectedInvestigation.summary}</p>
              </div>
            )}

            {/* Findings List */}
            <div className="space-y-2">
              <span className="font-bold text-slate-800 text-xs block">
                Classified Findings ({selectedInvestigation.findings.length}):
              </span>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
                {selectedInvestigation.findings.map(f => (
                  <div key={f.id} className="p-3 rounded-xl border border-slate-200/80 bg-white shadow-xs space-y-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-bold text-slate-900 text-xs">{f.title}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {f.classification}
                      </span>
                    </div>
                    <p className="text-slate-600 text-[11px] leading-relaxed">{f.variance_explanation}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Audit Dossier & Export Controls Section */}
            <div className="p-4 sm:p-5 rounded-2xl bg-slate-900 text-white space-y-3.5 shadow-md">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-slate-100 text-xs sm:text-sm">Official Audit Dossier & Exports</span>
                </div>
                <button
                  type="button"
                  disabled={generatingReport}
                  onClick={handleGenerateReportSnapshot}
                  className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold rounded-xl text-xs flex items-center justify-center space-x-1.5 transition-colors shadow-xs cursor-pointer self-start sm:self-auto"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${generatingReport ? 'animate-spin' : ''}`} />
                  <span>{generatingReport ? 'Sealing Snapshot...' : 'Seal New Audit Snapshot'}</span>
                </button>
              </div>

              {loadingReports ? (
                <p className="text-slate-400 text-xs">Loading report snapshots...</p>
              ) : investigationReports.length === 0 ? (
                <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700/60 text-slate-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <span>No sealed report snapshot exists for this investigation yet.</span>
                  <button
                    type="button"
                    onClick={handleGenerateReportSnapshot}
                    disabled={generatingReport}
                    className="text-sky-400 hover:text-sky-300 font-semibold underline text-xs cursor-pointer self-start sm:self-auto"
                  >
                    Generate Snapshot
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="space-y-3 max-h-56 overflow-y-auto pr-1 custom-scrollbar">
                    {investigationReports.map(rep => (
                      <div key={rep.id} className="p-3.5 bg-slate-800/90 rounded-xl border border-slate-700 space-y-2.5">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                          <div>
                            <span className="font-bold text-slate-100 text-xs block">
                              IR-{rep.id}-V{rep.report_version}: {rep.report_title}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              Generated: {new Date(rep.generation_timestamp).toLocaleString()}
                            </span>
                          </div>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 inline-flex items-center space-x-1 self-start sm:self-auto">
                            <CheckCircle2 className="w-2.5 h-2.5" />
                            <span>SEALED &amp; VERIFIED</span>
                          </span>
                        </div>

                        <div className="text-[10px] text-slate-400 font-mono break-all bg-slate-950/80 p-2 rounded-lg border border-slate-800">
                          SHA-256: {rep.snapshot_integrity_hash}
                        </div>

                        {/* Export Buttons */}
                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          <a
                            href={apiService.getReportHtmlUrl(selectedInvestigation.id, rep.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg text-xs flex items-center space-x-1.5 transition-colors shadow-xs"
                          >
                            <FileCode className="w-3.5 h-3.5" />
                            <span>Printable HTML Dossier</span>
                          </a>

                          <a
                            href={apiService.getReportMarkdownUrl(selectedInvestigation.id, rep.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg text-xs flex items-center space-x-1.5 transition-colors"
                          >
                            <FileDown className="w-3.5 h-3.5" />
                            <span>Markdown (.md)</span>
                          </a>

                          <div className="flex items-center space-x-1 bg-slate-950 border border-slate-700 rounded-lg p-0.5">
                            <select
                              value={selectedSchedule}
                              onChange={(e) => setSelectedSchedule(e.target.value)}
                              className="bg-transparent text-slate-200 text-xs px-2 py-1 focus:outline-none cursor-pointer"
                            >
                              <option value="reconciliation">Reconciliation Schedule</option>
                              <option value="summary">Currency Summary</option>
                              <option value="findings">Findings Register</option>
                              <option value="evidence">Evidence Register</option>
                            </select>
                            <a
                              href={apiService.getReportCsvUrl(selectedInvestigation.id, rep.id, selectedSchedule)}
                              download
                              className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded text-xs flex items-center space-x-1 transition-colors"
                            >
                              <FileSpreadsheet className="w-3.5 h-3.5" />
                              <span>CSV</span>
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedInvestigation(null)}
                className="w-full sm:w-auto px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl transition-colors cursor-pointer text-center"
              >
                Close Summary
              </button>
            </div>
          </div>
        )}
      </Modal>
    </MainLayout>
  );
}

export default App;
