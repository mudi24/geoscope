'use client'

import { useState } from 'react'
import { API_BASE } from '@/lib/api'

interface Props {
  analysisId: number
  domain?: string | null
}

export function ExportPDFButton({ analysisId, domain }: Props) {
  const [loading, setLoading] = useState(false)

  async function handleExport() {
    setLoading(true)
    try {
      // Get the client id the same way api.ts does
      const clientId =
        typeof window !== 'undefined'
          ? window.localStorage.getItem('geoscope_client_id') ?? ''
          : ''

      const res = await fetch(`${API_BASE}/api/export/pdf/${analysisId}`, {
        headers: clientId ? { 'X-Client-Id': clientId } : {},
      })

      if (!res.ok) {
        const msg = await res.text().catch(() => '')
        throw new Error(msg || `${res.status} ${res.statusText}`)
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const safe = (domain || 'report').replace(/[^a-zA-Z0-9.-]/g, '_')
      a.download = `geoscope_${safe}_${new Date().toISOString().slice(0, 10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('PDF 导出失败', err)
      alert('PDF 导出失败，请稍后重试。')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleExport}
      disabled={loading}
      className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {loading ? (
        <>
          <svg
            className="h-4 w-4 animate-spin text-slate-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          生成中…
        </>
      ) : (
        <>
          <svg
            className="h-4 w-4 text-slate-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
          </svg>
          导出 PDF
        </>
      )}
    </button>
  )
}
