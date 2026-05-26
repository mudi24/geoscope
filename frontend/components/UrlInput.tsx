'use client'

import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { analyzeUrl } from '@/lib/api'

function isValidUrl(raw: string) {
  try {
    const u = new URL(raw)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

export function UrlInput() {
  const router = useRouter()
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const valid = useMemo(() => isValidUrl(url.trim()), [url])

  async function onSubmit() {
    const value = url.trim()
    if (!isValidUrl(value)) {
      setError('请输入合法的 URL（需包含 http/https）')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const { id } = await analyzeUrl(value)
      router.push(`/analyze/${id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : '分析失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-2xl">
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm outline-none ring-indigo-200 focus:ring-2"
          placeholder="输入文章 URL，如 https://example.com/blog/post"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onSubmit()
          }}
          disabled={loading}
        />
        <button
          className="rounded-lg bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60"
          onClick={onSubmit}
          disabled={loading || !valid}
        >
          {loading ? '分析中…' : '开始分析'}
        </button>
      </div>
      <div className="mt-2 min-h-5 text-sm">
        {loading ? (
          <p className="text-slate-600">正在抓取与 AI 分析...</p>
        ) : error ? (
          <p className="text-red-600">{error}</p>
        ) : (
          <p className="text-slate-500">提示：分析通常需要 5-15 秒。</p>
        )}
      </div>
    </div>
  )
}

