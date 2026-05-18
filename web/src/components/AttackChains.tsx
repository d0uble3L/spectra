import { useState } from 'react'
import type { AttackChain, Finding } from '../types'
import SeverityBadge from './SeverityBadge'

interface AttackChainsProps {
  chains: AttackChain[]
  findings: Finding[]
}

interface ChainCardProps {
  chain: AttackChain
  findings: Finding[]
  index: number
}

function ChainCard({ chain, findings, index }: ChainCardProps) {
  const [open, setOpen] = useState(false)

  const relatedFindings = findings.filter((f) => chain.finding_ids.includes(f.id))

  return (
    <div className="border border-slate-700 rounded-xl overflow-hidden bg-slate-900/60 transition-all duration-150">
      {/* Header / toggle */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-slate-800/60 transition-colors duration-100"
        aria-expanded={open}
      >
        {/* Chain index badge */}
        <span className="shrink-0 flex items-center justify-center w-7 h-7 rounded-full bg-cyan-400/10 border border-cyan-400/30 text-cyan-400 text-xs font-bold">
          {index + 1}
        </span>

        <span className="flex-1 font-semibold text-slate-100">{chain.name}</span>

        <span className="text-slate-500 text-xs mr-1">
          {relatedFindings.length} finding{relatedFindings.length !== 1 ? 's' : ''}
        </span>

        {/* Chevron */}
        <svg
          className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded body */}
      {open && (
        <div className="px-5 pb-5 border-t border-slate-700/60 animate-slide-down">
          {/* Description */}
          <p className="mt-4 text-sm text-slate-300 leading-relaxed">{chain.description}</p>

          {/* Related findings */}
          {relatedFindings.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">
                Related Findings
              </p>
              <div className="space-y-2">
                {relatedFindings.map((finding) => (
                  <div
                    key={finding.id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-slate-800 border border-slate-700"
                  >
                    <SeverityBadge severity={finding.severity} size="sm" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{finding.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5 font-mono truncate">
                        {finding.affected_component}
                      </p>
                    </div>
                    {finding.cvss_score !== null && (
                      <span className="shrink-0 text-xs font-mono text-slate-400">
                        CVSS {finding.cvss_score.toFixed(1)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Finding ID list (when no full finding data available) */}
          {relatedFindings.length === 0 && chain.finding_ids.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">
                Finding IDs
              </p>
              <div className="flex flex-wrap gap-2">
                {chain.finding_ids.map((id) => (
                  <span
                    key={id}
                    className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700"
                  >
                    {id}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AttackChains({ chains, findings }: AttackChainsProps) {
  if (chains.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <span className="section-label">Attack Chains</span>
        </div>
        <div className="px-5 py-8 text-center text-slate-500 text-sm">
          No attack chains identified.
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <span className="section-label">Attack Chains</span>
        <span className="text-xs text-slate-500">
          {chains.length} chain{chains.length !== 1 ? 's' : ''} identified
        </span>
      </div>
      <div className="p-4 space-y-2">
        {chains.map((chain, i) => (
          <ChainCard key={chain.name + i} chain={chain} findings={findings} index={i} />
        ))}
      </div>
    </div>
  )
}
