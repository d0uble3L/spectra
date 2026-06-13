import type {
  AnalyzeResponse,
  ReportListResponse,
  ReportDetail,
  ScannerFormat,
} from './types'

const BASE = '/api'

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.detail) {
        message = typeof body.detail === 'string'
          ? body.detail
          : JSON.stringify(body.detail)
      }
    } catch {
      // ignore JSON parse errors; keep HTTP status message
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

// ─── API Calls ────────────────────────────────────────────────────────────────

/**
 * POST /api/analyze
 * Uploads a scan JSON file and returns the structured analysis report.
 */
export async function analyzeFile(
  file: File,
  scanner: ScannerFormat = 'auto',
  onProgress?: (pct: number) => void,
): Promise<AnalyzeResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('scanner', scanner)

  // Use XMLHttpRequest when caller wants progress events
  if (onProgress) {
    return new Promise<AnalyzeResponse>((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${BASE}/analyze`)
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100))
        }
      })
      xhr.addEventListener('load', async () => {
        try {
          if (xhr.status < 200 || xhr.status >= 300) {
            let message = `HTTP ${xhr.status}`
            try {
              const body = JSON.parse(xhr.responseText)
              if (body?.detail) message = String(body.detail)
            } catch { /* ignore */ }
            reject(new Error(message))
          } else {
            resolve(JSON.parse(xhr.responseText) as AnalyzeResponse)
          }
        } catch (err) {
          reject(err)
        }
      })
      xhr.addEventListener('error', () => reject(new Error('Network error')))
      xhr.addEventListener('abort', () => reject(new Error('Request aborted')))
      xhr.send(form)
    })
  }

  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    body: form,
  })
  return handleResponse<AnalyzeResponse>(res)
}

/**
 * GET /api/reports
 * Returns a page of stored report summaries.
 */
export async function getReports(limit = 20, offset = 0): Promise<ReportListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const res = await fetch(`${BASE}/reports?${params}`)
  return handleResponse<ReportListResponse>(res)
}

/**
 * GET /api/reports/:id
 * Returns the full report detail including markdown.
 */
export async function getReport(id: string): Promise<ReportDetail> {
  const res = await fetch(`${BASE}/reports/${encodeURIComponent(id)}`)
  return handleResponse<ReportDetail>(res)
}

/**
 * DELETE /api/reports/:id
 * Permanently removes a stored report.
 */
export async function deleteReport(id: string): Promise<void> {
  const res = await fetch(`${BASE}/reports/${encodeURIComponent(id)}`, { method: 'DELETE' })
  if (!res.ok && res.status !== 204) {
    await handleResponse(res)
  }
}
