import type { AnalysisReport, Severity } from '../types'
import { RISK_COLOR, RISK_BG, SEVERITY_COLOR, SEVERITY_ORDER } from '../types'
import SeverityBadge from './SeverityBadge'

interface RiskOverviewProps {
  report: AnalysisReport
}

const SEVERITY_LABEL_SHORT: Record<Severity, string> = {
  CRITICAL: 'Crit',
  HIGH:     'High',
  MEDIUM:   'Med',
  LOW:      'Low',
  INFO:     'Info',
}

const SEVERITY_BOX_BG: Record<Severity, string> = {
  CRITICAL: 'bg-red-500/10 border border-red-500/30',
  HIGH:     'bg-orange-500/10 border border-orange-500/30',
  MEDIUM:   'bg-yellow-500/10 border border-yellow-500/30',
  LOW:      'bg-blue-400/10 border border-blue-400/30',
  INFO:     'bg-slate-500/10 border border-slate-500/30',
}

function riskScoreColor(score: number): string {
  if (score >= 80) return 'text-red-500'
  if (score >= 60) return 'text-orange-500'
  if (score >= 40) return 'text-yellow-500'
  return 'text-blue-400'
}

export default function RiskOverview({ report }: RiskOverviewProps) {
  const { overall_risk_score, risk_level, findings_by_severity, scan_metadata, scanner_type } = report
  const scoreColor = riskScoreColor(overall_risk_score)
  const riskBadge = RISK_BG[risk_level]
  const riskTextColor = RISK_COLOR[risk_level]

  return (
    <div className="card animate-fade-in">
      <div className="card-header flex items-center justify-between">
        <span className="section-label">Risk Overview</span>
        <span className="text-xs text-slate-500 font-mono">
          {scanner_type.toUpperCase()}
        </span>
      </div>

      <div className="px-5 py-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-6">
          {/* Score block */}
          <div className="flex items-end gap-4">
            <div className="flex flex-col">
              <span className="section-label mb-1">Risk Score</span>
              <span className={`text-7xl font-black tabular-nums leading-none ${scoreColor}`}>
                {overall_risk_score}
              </span>
              <span className="text-slate-500 text-xs mt-1">out of 100</span>
            </div>

            {/* Vertical divider */}
            <div className="hidden sm:block w-px h-20 bg-slate-700 self-center" />

            {/* Risk level */}
            <div className="flex flex-col gap-2">
              <span className="section-label">Risk Level</span>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-lg border font-bold text-sm ${riskBadge}`}>
                <span className={`mr-2 w-2.5 h-2.5 rounded-full ${riskTextColor.replace('text-', 'bg-')}`} />
                {risk_level}
              </span>
            </div>
          </div>

          {/* Severity count grid */}
          <div className="flex-1">
            <span className="section-label block mb-3">Findings by Severity</span>
            <div className="grid grid-cols-5 gap-2">
              {SEVERITY_ORDER.map((sev) => {
                const count = findings_by_severity[sev] ?? 0
                return (
                  <div
                    key={sev}
                    className={`flex flex-col items-center py-3 px-1 rounded-lg ${SEVERITY_BOX_BG[sev]}`}
                  >
                    <span className={`text-2xl font-bold tabular-nums ${SEVERITY_COLOR[sev]}`}>
                      {count}
                    </span>
                    <span className={`text-xs font-semibold mt-1 ${SEVERITY_COLOR[sev]} opacity-80`}>
                      {SEVERITY_LABEL_SHORT[sev]}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Scan metadata footer */}
        <div className="mt-5 pt-4 border-t border-slate-700 flex flex-wrap gap-4 text-xs text-slate-500">
          <span>
            Raw findings:{' '}
            <span className="text-slate-300 font-medium">{scan_metadata.total_raw_findings}</span>
          </span>
          <span>
            After dedup:{' '}
            <span className="text-slate-300 font-medium">{scan_metadata.after_dedup}</span>
          </span>
          {scan_metadata.scan_timestamp && (
            <span>
              Scanned:{' '}
              <span className="text-slate-300 font-medium">
                {new Date(scan_metadata.scan_timestamp).toLocaleString()}
              </span>
            </span>
          )}
          <span className="ml-auto flex items-center gap-1.5">
            <SeverityBadge severity={risk_level} size="sm" />
          </span>
        </div>
      </div>
    </div>
  )
}
