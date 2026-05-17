import type { Severity, RiskLevel } from '../types'
import { SEVERITY_COLOR, SEVERITY_DOT } from '../types'

interface SeverityBadgeProps {
  severity: Severity | RiskLevel
  size?: 'sm' | 'md'
}

const BADGE_BG: Record<string, string> = {
  CRITICAL: 'bg-red-500/15 border border-red-500/40',
  HIGH:     'bg-orange-500/15 border border-orange-500/40',
  MEDIUM:   'bg-yellow-500/15 border border-yellow-500/40',
  LOW:      'bg-blue-400/15 border border-blue-400/40',
  INFO:     'bg-slate-500/15 border border-slate-500/40',
}

export default function SeverityBadge({ severity, size = 'md' }: SeverityBadgeProps) {
  const textColor = SEVERITY_COLOR[severity as Severity] ?? 'text-slate-400'
  const bg = BADGE_BG[severity] ?? 'bg-slate-500/15 border border-slate-500/40'
  const dot = SEVERITY_DOT[severity as Severity] ?? 'bg-slate-400'

  const sizeClasses = size === 'sm'
    ? 'text-xs px-2 py-0.5 gap-1.5'
    : 'text-xs px-2.5 py-1 gap-2'

  return (
    <span
      className={`inline-flex items-center rounded-full font-semibold tracking-wide ${bg} ${textColor} ${sizeClasses}`}
    >
      <span className={`shrink-0 rounded-full ${dot} ${size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2'}`} />
      {severity}
    </span>
  )
}
