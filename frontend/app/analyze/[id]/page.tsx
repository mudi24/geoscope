'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { AIReport } from '@/components/AIReport'
import { ExportPDFButton } from '@/components/ExportPDFButton'
import { ScoreCard } from '@/components/ScoreCard'
import { ScoreEvidence } from '@/components/ScoreEvidence'
import { ScoreRadar } from '@/components/ScoreRadar'
import { SuggestionList } from '@/components/SuggestionList'
import { getAnalysis, type AnalysisResponse } from '@/lib/api'

/** 总分对应的颜色档位 */
function totalScoreStyle(score: number) {
  if (score >= 80) return { ring: 'stroke-emerald-500', text: 'text-emerald-600', label: '优秀', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
  if (score >= 60) return { ring: 'stroke-amber-400', text: 'text-amber-600', label: '良好', bg: 'bg-amber-50 text-amber-700 border-amber-200' }
  return { ring: 'stroke-red-500', text: 'text-red-600', label: '待优化', bg: 'bg-red-50 text-red-600 border-red-200' }
}

/** SVG 环形进度 */
function ScoreRing({ score }: { score: number }) {
  const R = 36
  const C = 2 * Math.PI * R
  const offset = C - (score / 100) * C
  const s = totalScoreStyle(score)
  return (
    <div className="relative flex h-24 w-24 items-center justify-center">
      <svg className="-rotate-90" width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={R} fill="none" stroke="#e2e8f0" strokeWidth="8" />
        <circle
          cx="48" cy="48" r={R} fill="none"
          className={s.ring}
          strokeWidth="8"
          strokeDasharray={C}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={`text-2xl font-extrabold leading-none ${s.text}`}>{score}</span>
        <span className="mt-0.5 text-[10px] font-medium text-slate-400">{s.label}</span>
      </div>
    </div>
  )
}

/** Loading 骨架屏 */
function LoadingSkeleton({ status }: { status?: string }) {
  return (
    <main className="mx-auto min-h-screen max-w-4xl px-6 py-12">
      <div className="mb-6 h-5 w-40 animate-pulse rounded-full bg-slate-200" />
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-6">
          <div className="h-24 w-24 animate-pulse rounded-full bg-slate-200" />
          <div className="flex-1 space-y-3">
            <div className="h-5 w-2/3 animate-pulse rounded-full bg-slate-200" />
            <div className="h-4 w-1/2 animate-pulse rounded-full bg-slate-200" />
            <div className="h-4 w-3/4 animate-pulse rounded-full bg-slate-200" />
          </div>
        </div>
        <div className="mt-6 flex items-center gap-2 text-sm text-slate-500">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-indigo-400" />
          {status ? `当前状态：${status}` : '正在分析…'}
          <span className="text-xs text-slate-400">（页面自动刷新）</span>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-xl bg-slate-200" />
        ))}
      </div>
    </main>
  )
}

export default function AnalyzePage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const [data, setData] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    let timer: number | null = null

    async function tick() {
      try {
        const d = await getAnalysis(params.id)
        if (!mounted) return
        setData(d)
        if (d.status === 'error') {
          setError(d.error || '分析失败，请重试')
          return
        }
        if (d.status !== 'done') {
          timer = window.setTimeout(tick, 1000)
        }
      } catch (e) {
        if (!mounted) return
        setError(e instanceof Error ? e.message : '分析失败，请重试')
      }
    }

    setData(null)
    setError(null)
    tick()
    return () => {
      mounted = false
      if (timer) window.clearTimeout(timer)
    }
  }, [params.id])

  const radarData = useMemo(() => {
    if (!data) return []
    return [
      { name: '语义清晰', score: data.scores.semantic_clarity },
      { name: '实体完整', score: data.scores.entity_completeness },
      { name: '引用可信', score: data.scores.citation_credibility },
      { name: '问答友好', score: data.scores.qa_friendly },
      { name: '技术标记', score: data.scores.tech_markup },
    ]
  }, [data])

  const insight = useMemo(() => {
    const m = data?.score_insights || {}
    return {
      semantic: m['semantic_clarity'],
      entity: m['entity_completeness'],
      citation: m['citation_credibility'],
      qa: m['qa_friendly'],
      tech: m['tech_markup'],
    }
  }, [data])

  if (error) {
    return (
      <main className="mx-auto min-h-screen max-w-4xl px-6 py-12">
        <nav className="mb-6 text-sm text-slate-500">
          <Link href="/" className="hover:text-slate-700">首页</Link>
          <span className="mx-2">/</span>
          <span className="text-slate-700">分析报告</span>
        </nav>
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 text-xl">⚠️</span>
            <div>
              <h1 className="font-semibold text-slate-900">分析失败</h1>
              <p className="mt-1 text-sm text-slate-600">{error}</p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              onClick={() => router.refresh()}
            >
              重试
            </button>
            <Link
              className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              href="/"
            >
              返回首页
            </Link>
          </div>
        </div>
      </main>
    )
  }

  if (!data || data.status !== 'done') {
    return <LoadingSkeleton status={data?.status} />
  }

  const scoreStyle = totalScoreStyle(data.scores.total_score)

  return (
    <main className="mx-auto min-h-screen max-w-4xl px-6 py-12">

      {/* 面包屑 */}
      <nav className="mb-6 flex items-center gap-1.5 text-sm text-slate-500">
        <Link href="/" className="hover:text-slate-700">首页</Link>
        <span>/</span>
        <Link href="/history" className="hover:text-slate-700">历史记录</Link>
        <span>/</span>
        <span className="text-slate-700 truncate max-w-xs">{data.title || data.url}</span>
      </nav>

      {/* ── 报告头部 ── */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
          {/* 总分环 */}
          <div className="flex flex-col items-center gap-2">
            <ScoreRing score={data.scores.total_score} />
            <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${scoreStyle.bg}`}>
              {scoreStyle.label}
            </span>
          </div>

          {/* 标题 & 元信息 */}
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-slate-900 leading-snug">
              {data.title || '（无标题）'}
            </h1>
            <a
              className="mt-1 block truncate text-sm text-indigo-600 hover:text-indigo-700"
              href={data.url}
              target="_blank"
              rel="noreferrer"
            >
              {data.url}
            </a>

            <div className="mt-3 flex flex-wrap gap-2">
              {data.domain && (
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                  🌐 {data.domain}
                </span>
              )}
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                🕐 {new Date(data.created_at).toLocaleString()}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                📡 {data.fetch_method}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                # {data.id}
              </span>
            </div>
          </div>
        </div>

        {/* 五维小分条 */}
        <div className="mt-6 grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-5">
          {radarData.map((d) => {
            const pct = d.score
            const barColor =
              pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-400' : 'bg-red-500'
            return (
              <div key={d.name}>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600">{d.name}</span>
                  <span className="font-semibold text-slate-800">{pct}</span>
                </div>
                <div className="mt-1 h-1.5 w-full rounded-full bg-slate-100">
                  <div
                    className={`h-1.5 rounded-full transition-all ${barColor}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── 五维评分 ── */}
      <SectionHeader title="五维评分" subtitle="点击卡片可展开优缺点与建议" className="mt-10" />

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <ScoreRadar data={radarData} totalScore={data.scores.total_score} />
        <div className="grid grid-cols-1 gap-4">
          <ScoreCard
            title="语义清晰度"
            score={data.scores.semantic_clarity}
            desc="标题层级/段落长度/小标题密度等结构信号"
            pros={insight.semantic?.pros}
            cons={insight.semantic?.cons}
            suggestions={insight.semantic?.suggestions}
          />
          <ScoreCard
            title="实体完整性"
            score={data.scores.entity_completeness}
            desc="关键术语是否给出上下文解释、缩写是否展开"
            pros={insight.entity?.pros}
            cons={insight.entity?.cons}
            suggestions={insight.entity?.suggestions}
          />
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
        <ScoreCard
          title="引用可信度"
          score={data.scores.citation_credibility}
          desc="作者/日期/外链等可追溯性信号"
          pros={insight.citation?.pros}
          cons={insight.citation?.cons}
          suggestions={insight.citation?.suggestions}
        />
        <ScoreCard
          title="问答友好度"
          score={data.scores.qa_friendly}
          desc="是否具备 FAQ/Q&A、结论前置、直接答案句式"
          pros={insight.qa?.pros}
          cons={insight.qa?.cons}
          suggestions={insight.qa?.suggestions}
        />
        <ScoreCard
          title="技术标记"
          score={data.scores.tech_markup}
          desc="Schema.org/OG/Canonical 等结构化标记"
          pros={insight.tech?.pros}
          cons={insight.tech?.cons}
          suggestions={insight.tech?.suggestions}
        />
      </div>

      {/* ── AI 洞察 ── */}
      <SectionHeader title="AI 洞察" subtitle="内容摘要 · 知识缺口 · 优化建议" className="mt-10" />

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <AIReport summary={data.ai_result.summary} gaps={data.ai_result.gaps} />
        <SuggestionList items={data.ai_result.suggestions} />
      </div>

      {/* ── 评分证据 ── */}
      <SectionHeader title="评分证据" subtitle="用于解释每个维度得分的原始信号" className="mt-10" />

      <div className="mt-4">
        <ScoreEvidence evidence={data.score_evidence || {}} />
      </div>

      {/* ── 操作按钮 ── */}
      <div className="mt-8 flex flex-wrap gap-2 border-t border-slate-100 pt-6">
        <Link
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          href="/"
        >
          ＋ 分析新页面
        </Link>
        <Link
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          href="/history"
        >
          历史记录
        </Link>
        {/* <ExportPDFButton analysisId={data.id} domain={data.domain} /> */}
      </div>
    </main>
  )
}

/** 统一区块标题组件 */
function SectionHeader({
  title,
  subtitle,
  className = '',
}: {
  title: string
  subtitle?: string
  className?: string
}) {
  return (
    <div className={`flex items-end justify-between border-b border-slate-100 pb-2 ${className}`}>
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
    </div>
  )
}
