import { useState, useRef, useCallback } from 'react'
import type { ScannerFormat } from '../types'
import { SCANNER_FORMATS } from '../types'

interface UploadZoneProps {
  onAnalyze: (file: File, scanner: ScannerFormat) => void
  isAnalyzing: boolean
  error: string | null
}

function UploadIcon() {
  return (
    <svg className="w-10 h-10 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  )
}

function SpinnerIcon() {
  return (
    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

export default function UploadZone({ onAnalyze, isAnalyzing, error }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [scanner, setScanner] = useState<ScannerFormat>('auto')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback((file: File) => {
    setSelectedFile(file)
  }, [])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else setDragActive(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    if (selectedFile && !isAnalyzing) onAnalyze(selectedFile, scanner)
  }, [selectedFile, scanner, isAnalyzing, onAnalyze])

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12">
      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-400/10 border border-cyan-400/20 mb-4">
            <svg className="w-7 h-7 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Analyze a Scan</h2>
          <p className="mt-2 text-sm text-slate-400">
            Upload output from Trivy, Semgrep, or any scanner to get an AI-powered security report.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Drop zone */}
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => !isAnalyzing && inputRef.current?.click()}
            className={`
              relative flex flex-col items-center justify-center gap-3 px-6 py-10
              border-2 border-dashed rounded-xl cursor-pointer transition-all duration-150
              ${dragActive
                ? 'border-cyan-400 bg-cyan-400/5'
                : selectedFile
                  ? 'border-cyan-500/50 bg-cyan-500/5'
                  : 'border-slate-700 hover:border-slate-500 bg-slate-800/50 hover:bg-slate-800'
              }
              ${isAnalyzing ? 'pointer-events-none opacity-60' : ''}
            `}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".json,.txt,.sarif"
              className="hidden"
              onChange={handleInputChange}
              disabled={isAnalyzing}
            />

            {selectedFile ? (
              <>
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-cyan-400/10 border border-cyan-400/30">
                  <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round"
                      d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-200">{selectedFile.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {(selectedFile.size / 1024).toFixed(1)} KB · Click to change
                  </p>
                </div>
              </>
            ) : (
              <>
                <UploadIcon />
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-300">
                    Drop your scan file here
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    or <span className="text-cyan-400">click to browse</span> · .json, .txt, .sarif
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Scanner selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">
              Scanner Format
            </label>
            <div className="grid grid-cols-4 gap-2">
              {SCANNER_FORMATS.map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setScanner(value)}
                  disabled={isAnalyzing}
                  className={`
                    py-2 px-3 rounded-lg text-xs font-semibold border transition-all duration-100
                    disabled:opacity-40 disabled:cursor-not-allowed
                    ${scanner === value
                      ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-400'
                      : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                    }
                  `}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <svg className="w-4 h-4 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={!selectedFile || isAnalyzing}
            className="btn-primary w-full justify-center py-3 text-sm"
          >
            {isAnalyzing ? (
              <>
                <SpinnerIcon />
                Analyzing with Claude…
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 3l14 9-14 9V3z" />
                </svg>
                Run Analysis
              </>
            )}
          </button>
        </form>

        {/* Supported scanners hint */}
        <p className="mt-6 text-center text-xs text-slate-600">
          Supports Trivy · Semgrep · Nessus · Burp Suite · Generic text
        </p>
      </div>
    </div>
  )
}
