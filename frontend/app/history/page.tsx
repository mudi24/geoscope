'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { HistoryTable } from '@/components/HistoryTable'
import { getHistory, type HistoryItem } from '@/lib/api'

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    let mounted = true
    getHistory()
      .then((rows) => {
        if (!mounted) return
        setItems(rows)
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

  const filtered = useMemo(() => {
    const f = filter.trim().toLowerCase()
    if (!f) return items
    return items.filter((it) => (it.url || '').toLowerCase().includes(f))
  }, [items, filter])

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-12">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">历史记录</h1>
          <p className="mt-1 text-sm text-slate-600">最近 20 条分析记录</p>
        </div>
        <div className="flex gap-2">
          <input
            className="w-72 max-w-full rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm shadow-sm outline-none ring-indigo-200 focus:ring-2"
            placeholder="按域名/URL 过滤"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <Link
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            href="/"
          >
            去分析
          </Link>
        </div>
      </div>

      <div className="mt-6">
        {loading ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
            加载中...
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
            暂无分析记录，去首页开始。
          </div>
        ) : (
          <HistoryTable items={filtered} />
        )}
      </div>
    </main>
  )
}

