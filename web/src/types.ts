// ─── Severity & Risk ────────────────────────────────────────────────────────

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

// ─── Core Report Entities ────────────────────────────────────────────────────

export interface Finding {
  id: string
  severity: Severity
  title: string
  description: string
  affected_component: string
  cvss_score: number | null
  exploitability: string
  remediation: string
  references: string[]
}

export interface AttackChain {
  name: string
  description: string
  finding_ids: string[]
}

export interface ScanMetadata {
  total_raw_findings: number
  after_dedup: number
  scan_timestamp: string | null
}

export interface FindingsBySeverity {
  CRITICAL: number
  HIGH: number
  MEDIUM: number
  LOW: number
  INFO: number
}

export interface AnalysisReport {
  executive_summary: string
  overall_risk_score: number
  risk_level: RiskLevel
  scanner_type: string
  scan_metadata: ScanMetadata
  findings_by_severity: FindingsBySeverity
  findings: Finding[]
  attack_chains: AttackChain[]
  immediate_actions: string[]
  strategic_recommendations: string[]
}

// ─── API Response Types ──────────────────────────────────────────────────────

export interface AnalyzeResponse {
  id: string
  report: AnalysisReport
}

export interface ReportSummary {
  id: string
  created_at: string
  filename: string
  scanner_type: string
  risk_level: RiskLevel
  overall_risk_score: number
}

export interface ReportDetail {
  id: string
  report: AnalysisReport
  markdown: string
  created_at: string
  filename: string
}

// ─── Scanner Format ──────────────────────────────────────────────────────────

export type ScannerFormat = 'auto' | 'trivy' | 'semgrep' | 'generic'

export const SCANNER_FORMATS: { value: ScannerFormat; label: string }[] = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'trivy', label: 'Trivy (CVE)' },
  { value: 'semgrep', label: 'Semgrep (SAST)' },
  { value: 'generic', label: 'Generic' },
]

// ─── App State Machine ───────────────────────────────────────────────────────

export type AppState = 'idle' | 'analyzing' | 'done'

// ─── UI Helpers ──────────────────────────────────────────────────────────────

export const SEVERITY_ORDER: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']

export const SEVERITY_COLOR: Record<Severity, string> = {
  CRITICAL: 'text-red-500',
  HIGH:     'text-orange-500',
  MEDIUM:   'text-yellow-500',
  LOW:      'text-blue-400',
  INFO:     'text-slate-400',
}

export const SEVERITY_BG: Record<Severity, string> = {
  CRITICAL: 'bg-red-500/10 border-red-500/30',
  HIGH:     'bg-orange-500/10 border-orange-500/30',
  MEDIUM:   'bg-yellow-500/10 border-yellow-500/30',
  LOW:      'bg-blue-400/10 border-blue-400/30',
  INFO:     'bg-slate-500/10 border-slate-500/30',
}

export const SEVERITY_DOT: Record<Severity, string> = {
  CRITICAL: 'bg-red-500',
  HIGH:     'bg-orange-500',
  MEDIUM:   'bg-yellow-500',
  LOW:      'bg-blue-400',
  INFO:     'bg-slate-400',
}

export const RISK_COLOR: Record<RiskLevel, string> = {
  CRITICAL: 'text-red-500',
  HIGH:     'text-orange-500',
  MEDIUM:   'text-yellow-500',
  LOW:      'text-blue-400',
}

export const RISK_BG: Record<RiskLevel, string> = {
  CRITICAL: 'bg-red-500/10 border-red-500/40 text-red-400',
  HIGH:     'bg-orange-500/10 border-orange-500/40 text-orange-400',
  MEDIUM:   'bg-yellow-500/10 border-yellow-500/40 text-yellow-400',
  LOW:      'bg-blue-400/10 border-blue-400/40 text-blue-300',
}
