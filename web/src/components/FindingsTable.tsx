import { useState, useMemo } from 'react'
import type { Finding, Severity } from '../types'
import { SEVERITY_ORDER, SEVERITY_COLOR } from '../types'
import SeverityBadge from './SeverityBadge'

interface FindingsTableProps {
  findings: Finding[]
  findingsBySeverity: Record<Severity, number>
}

type SeverityFilter = Severity | 'ALL'

function ExternalLinkIcon() {
  return (
    <svg className="w-3 h-3 inline-block ml-0.5 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
  )
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  )
}

interface FindingRowProps {
  finding: Finding
}

function FindingRow({ finding }: FindingRowProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <tr
        className="border-b border-slate-700/60 hover:bg-slate-800/50 cursor-pointer transition-colors duration-100 group"
        onClick={() => setOpen((o) => !o)}
      >
        <td className="px-3 py-3 w-8">
          <ChevronIcon open={open} />
        </td>
        <td className="px-3 py-3">
          <SeverityBadge severity={finding.severity} size="sm" />
        </td>
        <td className="px-3 py-3">
          <span className="text-sm font-medium text-slate-200 line-clamp-1 group-hover:text-white">
            {finding.title}
          </span>
        </td>
        <td className="px-3 py-3 max-w-xs hidden md:table-cell">
          <span className="text-xs font-mono text-slate-400 truncate block">
            {finding.affected_component}
          </span>
        </td>
        <td className="px-3 py-3 text-center hidden sm:table-cell">
          {finding.cvss_score !== null ? (
            <span className={`text-sm font-mono font-semibold ${
              finding.cvss_score >= 9 ? 'text-red-400' :
              finding.cvss_score >= 7 ? 'text-orange-400' :
              finding.cvss_score >= 4 ? 'text-yellow-400' : 'text-slate-400'
            }`}>
              {finding.cvss_score.toFixed(1)}
            </span>
          ) : (
            <span className="text-slate-600 text-xs">—</span>
          )}
        </td>
        <td className="px-3 py-3 hidden lg:table-cell">
          <span className="text-xs text-slate-400 truncate block max-w-[120px]">
            {finding.exploitability}
          </span>
        </td>
      </tr>

      {/* Expanded detail row */}
      {open && (
        <tr className="border-b border-slate-700/60 bg-slate-900/80 animate-slide-down">
          <td colSpan={6} className="px-5 py-5">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Description */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">
                  Description
                </p>
                <p className="text-sm text-slate-300 leading-relaxed">{finding.description}</p>

                {/* Affected component (mobile) */}
                <div className="mt-3 md:hidden">
                  <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-1">
                    Affected Component
                  </p>
                  <p className="text-xs font-mono text-slate-400">{finding.affected_component}</p>
                </div>

                {/* Finding ID */}
                <div className="mt-3">
                  <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-1">
                    Finding ID
                  </p>
                  <p className="text-xs font-mono text-slate-400">{finding.id}</p>
                </div>
              </div>

              {/* Remediation */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">
                  Remediation
                </p>
                <p className="text-sm text-slate-300 leading-relaxed">{finding.remediation}</p>

                {/* References */}
                {finding.references.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">
                      References
                    </p>
                    <ul className="space-y-1">
                      {finding.references.map((ref, i) => (
                        <li key={i}>
                          <a
                            href={ref}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-cyan-400 hover:text-cyan-300 hover:underline break-all"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {ref}
                            <ExternalLinkIcon />
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function FindingsTable({ findings, findingsBySeverity }: FindingsTableProps) {
  const [activeFilter, setActiveFilter] = useState<SeverityFilter>('ALL')

  const filtered = useMemo(() => {
    if (activeFilter === 'ALL') return findings
    return findings.filter((f) => f.severity === activeFilter)
  }, [findings, activeFilter])

  const totalCount = findings.length

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <span className="section-label">Findings</span>
        <span className="text-xs text-slate-500">
          {filtered.length} of {totalCount}
        </span>
      </div>

      {/* Severity filter bar */}
      <div className="px-4 py-3 border-b border-slate-700 flex flex-wrap gap-1.5">
        {/* ALL button */}
        <button
          onClick={() => setActiveFilter('ALL')}
          className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors duration-100 ${
            activeFilter === 'ALL'
              ? 'bg-slate-600 text-white'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          ALL{' '}
          <span className={`ml-1 ${activeFilter === 'ALL' ? 'text-slate-300' : 'text-slate-600'}`}>
            {totalCount}
          </span>
        </button>

        {SEVERITY_ORDER.map((sev) => {
          const count = findingsBySeverity[sev] ?? 0
          const isActive = activeFilter === sev
          return (
            <button
              key={sev}
              onClick={() => setActiveFilter(sev)}
              disabled={count === 0}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors duration-100 disabled:opacity-30 disabled:cursor-not-allowed ${
                isActive
                  ? `${SEVERITY_COLOR[sev]} bg-slate-700`
                  : `text-slate-400 hover:text-slate-200 hover:bg-slate-800`
              }`}
            >
              <span className={isActive ? SEVERITY_COLOR[sev] : ''}>{sev}</span>{' '}
              <span className={`ml-1 ${isActive ? 'text-slate-300' : 'text-slate-600'}`}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="px-5 py-10 text-center text-slate-500 text-sm">
          No findings match the selected filter.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-700 text-xs text-slate-500 uppercase tracking-wider">
                <th className="px-3 py-2 w-8" />
                <th className="px-3 py-2 w-32">Severity</th>
                <th className="px-3 py-2">Title</th>
                <th className="px-3 py-2 hidden md:table-cell">Component</th>
                <th className="px-3 py-2 text-center hidden sm:table-cell w-20">CVSS</th>
                <th className="px-3 py-2 hidden lg:table-cell w-36">Exploitability</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((finding) => (
                <FindingRow key={finding.id} finding={finding} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
