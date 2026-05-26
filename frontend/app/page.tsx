'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { getHistory, type HistoryItem } from '@/lib/api'
import { UrlInput } from '@/components/UrlInput'

export default function HomePage() {
  const [recent, setRecent] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    getHistory()
      .then((items) => {
        if (!mounted) return
        setRecent(items.slice(0, 3))
      })
      .catch(() => {})
      .finally(() => {
        if (!mounted) return
        setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-6 py-12">
      <div className="w-full">
        <h1 className="text-center text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          GEOScope - AI 搜索引擎可见性分析
        </h1>
        <p className="mt-3 text-center text-slate-600">
          检测你的网页在 ChatGPT / Perplexity / Kimi 中的可引用性
        </p>
      </div>

      <div className="mt-8 flex w-full justify-center">
        <UrlInput />
      </div>

      <div className="mt-10 w-full max-w-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">最近分析</h2>
          <Link className="text-sm text-indigo-600 hover:text-indigo-700" href="/history">
            查看全部
          </Link>
        </div>
        <div className="mt-3 space-y-2">
          {loading ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
              加载中...
            </div>
          ) : recent.length === 0 ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
              暂无记录，先从上方输入一个 URL 开始吧。
            </div>
          ) : (
            recent.map((it) => (
              <Link
                key={it.id}
                href={`/analyze/${it.id}`}
                className="block rounded-xl border border-slate-200 bg-white p-4 text-sm shadow-sm hover:bg-slate-50"
              >
                <div className="font-medium text-slate-900">{it.title || it.url}</div>
                <div className="mt-1 text-xs text-slate-600">
                  {new Date(it.created_at).toLocaleString()} · 总分 {it.total_score}
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </main>
  )
}

