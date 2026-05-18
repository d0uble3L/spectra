import { useEffect, useState, useCallback } from 'react'
import type { ReportSummary } from '../types'
import { RISK_COLOR } from '../types'
import { getReports } from '../api'

interface ReportListProps {
  activeReportId: string | null
  refreshKey: number
  onSelect: (id: string) => void
  onNewScan: () => void
}

function ScannerIcon({ type }: { type: string }) {
  const lower = type.toLowerCase()
  if (lower === 'trivy') {
    return (
      <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
        CVE
      </span>
    )
  }
  if (lower === 'semgrep') {
    return (
      <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-400 border border-purple-500/30">
        SAST
      </span>
    )
  }
  return (
    <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-slate-500/20 text-slate-400 border border-slate-600">
      {type.slice(0, 4).toUpperCase()}
    </span>
  )
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString()
  } catch {
    return iso
  }
}

export default function ReportList({ activeReportId, refreshKey, onSelect, onNewScan }: ReportListProps) {
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchReports = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getReports()
      // Sort newest first
      const sorted = [...data].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      setReports(sorted)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchReports()
  }, [fetchReports, refreshKey])

  return (
    <nav className="flex flex-col h-full">
      {/* Sidebar header */}
      <div className="px-4 pt-5 pb-4 border-b border-slate-700/60">
        <div className="flex items-center gap-2.5 mb-4">
          {/* Logo mark */}
          <div className="w-8 h-8 rounded-lg bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center">
            <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 tracking-tight">SPECTRA</h1>
            <p className="text-xs text-slate-500 leading-none">Security Analysis</p>
          </div>
        </div>

        {/* New scan button */}
        <button
          onClick={onNewScan}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                     bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm
                     transition-colors duration-150"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          New Scan
        </button>
      </div>

      {/* Report list */}
      <div className="flex-1 overflow-y-auto px-2 py-3">
        <div className="flex items-center justify-between px-2 mb-2">
          <span className="section-label">Recent Reports</span>
          <button
            onClick={fetchReports}
            disabled={loading}
            className="text-slate-500 hover:text-slate-300 transition-colors p-1 rounded"
            title="Refresh"
          >
            <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mx-2 mb-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-400">
            {error}
          </div>
        )}

        {!loading && reports.length === 0 && !error && (
          <div className="px-2 py-6 text-center text-slate-600 text-xs">
            No reports yet. Upload a scan file to get started.
          </div>
        )}

        <ul className="space-y-1">
          {reports.map((r) => {
            const isActive = r.id === activeReportId
            const riskColor = RISK_COLOR[r.risk_level]

            return (
              <li key={r.id}>
                <button
                  onClick={() => onSelect(r.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors duration-100 group ${
                    isActive
                      ? 'bg-slate-700 text-slate-100'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="text-xs font-medium truncate flex-1">
                      {r.filename || 'Unknown file'}
                    </span>
                    <span className={`text-xs font-bold tabular-nums shrink-0 ${riskColor}`}>
                      {r.overall_risk_score}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ScannerIcon type={r.scanner_type} />
                    <span className={`text-xs font-semibold ${riskColor}`}>{r.risk_level}</span>
                    <span className="text-xs text-slate-600 ml-auto">{formatDate(r.created_at)}</span>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-700/60">
        <p className="text-xs text-slate-600 text-center">
          Powered by Claude AI
        </p>
      </div>
    </nav>
  )
}
