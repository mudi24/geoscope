'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { getHistory, type HistoryItem } from '@/lib/api'
import { UrlInput } from '@/components/UrlInput'

const FEATURES = [
  {
    icon: '🤖',
    title: 'AI 可引用性检测',
    desc: '分析你的内容是否符合 ChatGPT、Perplexity、Kimi 等 AI 搜索引擎的引用标准',
  },
  {
    icon: '📊',
    title: '多维度评分',
    desc: '从权威性、内容质量、结构化数据、技术 SEO 等维度全面评估页面表现',
  },
  {
    icon: '💡',
    title: '优化建议',
    desc: '针对每个评分维度给出具体可执行的改进建议，帮助你快速提升 GEO 得分',
  },
  {
    icon: '📄',
    title: 'PDF 报告导出',
    desc: '一键导出完整分析报告，方便团队协作与留存归档',
  },
]

const DIMENSIONS = [
  { label: '权威性', color: 'bg-indigo-500', desc: '域名信誉 & 外链质量' },
  { label: '内容质量', color: 'bg-violet-500', desc: '深度、原创性、可读性' },
  { label: '结构化数据', color: 'bg-sky-500', desc: 'Schema.org & 语义标记' },
  { label: '技术 SEO', color: 'bg-emerald-500', desc: '速度、可访问性、移动端' },
  { label: '新鲜度', color: 'bg-amber-500', desc: '内容更新频率与时效性' },
]

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
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-16">
      {/* ── Hero ── */}
      <section className="flex flex-col items-center text-center">
        <span className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
          ✨ GEO · Generative Engine Optimization
        </span>
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          让你的内容被&nbsp;
          <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
            AI 搜索引擎
          </span>
          &nbsp;引用
        </h1>
        <p className="mt-4 max-w-xl text-base text-slate-600">
          GEOScope 分析你的网页在 ChatGPT、Perplexity、Kimi 等 AI 搜索引擎中的可引用性，
          并给出可执行的优化建议，帮助你在 AI 时代抢占流量入口。
        </p>

        <div className="mt-8 w-full max-w-2xl">
          <UrlInput />
        </div>
      </section>

      {/* ── 评分维度 ── */}
      <section className="mt-20">
        <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-slate-400">
          评分维度
        </h2>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          {DIMENSIONS.map((d) => (
            <div
              key={d.label}
              className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 shadow-sm"
            >
              <span className={`h-2 w-2 rounded-full ${d.color}`} />
              <span className="text-sm font-medium text-slate-800">{d.label}</span>
              <span className="text-xs text-slate-400">{d.desc}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── 功能亮点 ── */}
      <section className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="mb-3 text-2xl">{f.icon}</div>
            <h3 className="text-sm font-semibold text-slate-900">{f.title}</h3>
            <p className="mt-1 text-xs leading-relaxed text-slate-500">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* ── 最近分析 ── */}
      <section className="mt-16">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">最近分析</h2>
          <Link className="text-sm text-indigo-600 hover:text-indigo-700" href="/history">
            查看全部 →
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
                className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 text-sm shadow-sm transition-colors hover:bg-slate-50"
              >
                <div>
                  <div className="font-medium text-slate-900">{it.title || it.url}</div>
                  <div className="mt-0.5 text-xs text-slate-500">
                    {new Date(it.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="ml-4 flex-shrink-0">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${
                      it.total_score >= 80
                        ? 'bg-emerald-50 text-emerald-700'
                        : it.total_score >= 60
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-red-50 text-red-600'
                    }`}
                  >
                    {it.total_score} 分
                  </span>
                </div>
              </Link>
            ))
          )}
        </div>
      </section>
    </main>
  )
}
