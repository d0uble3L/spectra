import { useState, useCallback } from 'react'
import type { AnalysisReport, ScannerFormat } from './types'
import { analyzeFile, getReport } from './api'
import UploadZone from './components/UploadZone'
import ReportView from './components/ReportView'
import ReportList from './components/ReportList'

type ViewState =
  | { kind: 'idle' }
  | { kind: 'analyzing' }
  | { kind: 'report'; id: string; report: AnalysisReport; filename: string; createdAt: string }

function LoadingOverlay() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-2 border-cyan-400/20 border-t-cyan-400 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
      </div>
      <div className="text-center">
        <p className="text-slate-200 font-semibold">Analyzing with Claude…</p>
        <p className="text-slate-500 text-sm mt-1">This may take 30–90 seconds</p>
      </div>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState<ViewState>({ kind: 'idle' })
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const activeReportId = view.kind === 'report' ? view.id : null

  const handleAnalyze = useCallback(async (file: File, scanner: ScannerFormat) => {
    setError(null)
    setView({ kind: 'analyzing' })
    try {
      const { id, report } = await analyzeFile(file, scanner)
      setView({
        kind: 'report',
        id,
        report,
        filename: file.name,
        createdAt: new Date().toISOString(),
      })
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setView({ kind: 'idle' })
    }
  }, [])

  const handleSelectReport = useCallback(async (id: string) => {
    setError(null)
    setView({ kind: 'analyzing' })
    try {
      const detail = await getReport(id)
      setView({
        kind: 'report',
        id: detail.id,
        report: detail.report,
        filename: detail.filename,
        createdAt: detail.created_at,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
      setView({ kind: 'idle' })
    }
  }, [])

  const handleNewScan = useCallback(() => {
    setError(null)
    setView({ kind: 'idle' })
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      {/* Sidebar */}
      <aside
        className={`
          flex-shrink-0 h-full bg-slate-900 border-r border-slate-700/60 overflow-hidden
          transition-all duration-200
          ${sidebarOpen ? 'w-64' : 'w-0'}
        `}
      >
        <div className="w-64 h-full">
          <ReportList
            activeReportId={activeReportId}
            refreshKey={refreshKey}
            onSelect={handleSelectReport}
            onNewScan={handleNewScan}
          />
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="flex-shrink-0 h-12 flex items-center gap-3 px-4 border-b border-slate-700/60 bg-slate-900/50">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="p-1.5 rounded-md text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            aria-label="Toggle sidebar"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <span className="text-sm font-semibold text-slate-300 tracking-tight">
            {view.kind === 'report'
              ? view.filename
              : view.kind === 'analyzing'
                ? 'Analyzing…'
                : 'New Scan'}
          </span>

          {view.kind === 'report' && (
            <button
              onClick={handleNewScan}
              className="ml-auto btn-ghost text-xs"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              New Scan
            </button>
          )}
        </header>

        {/* Content */}
        <main className="flex-1 overflow-hidden">
          {view.kind === 'idle' && (
            <UploadZone
              onAnalyze={handleAnalyze}
              isAnalyzing={false}
              error={error}
            />
          )}
          {view.kind === 'analyzing' && <LoadingOverlay />}
          {view.kind === 'report' && (
            <ReportView
              report={view.report}
              filename={view.filename}
              createdAt={view.createdAt}
            />
          )}
        </main>
      </div>
    </div>
  )
}
