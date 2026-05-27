'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { AIReport } from '@/components/AIReport'
import { ScoreCard } from '@/components/ScoreCard'
import { ScoreEvidence } from '@/components/ScoreEvidence'
import { ScoreRadar } from '@/components/ScoreRadar'
import { SuggestionList } from '@/components/SuggestionList'
import { getAnalysis, type AnalysisResponse } from '@/lib/api'

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
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-lg font-semibold text-slate-900">分析失败</h1>
          <p className="mt-2 text-sm text-slate-600">{error}</p>
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
    return (
      <main className="mx-auto min-h-screen max-w-4xl px-6 py-12">
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-700 shadow-sm">
          <div className="font-medium text-slate-900">任务处理中</div>
          <div className="mt-2 text-slate-600">
            当前状态：{data?.status || 'loading'}（页面会自动刷新结果）
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto min-h-screen max-w-4xl px-6 py-12">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">
              {data.title || '（无标题）'}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              {data.domain || ''} · {new Date(data.created_at).toLocaleString()} · 抓取方式{' '}
              {data.fetch_method}
            </p>
          </div>
          <div className="text-4xl font-bold text-slate-900">{data.scores.total_score}</div>
        </div>
        <p className="mt-3 break-all text-sm text-slate-600">{data.url}</p>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <ScoreRadar data={radarData} />
        <div className="grid grid-cols-1 gap-4">
          <ScoreCard
            title="语义清晰度"
            score={data.scores.semantic_clarity}
            desc="标题层级/段落长度/小标题密度等结构信号"
            pros={insight.semantic?.pros}
            cons={insight.semantic?.cons}
          />
          <ScoreCard
            title="实体完整性"
            score={data.scores.entity_completeness}
            desc="关键术语是否给出上下文解释、缩写是否展开"
            pros={insight.entity?.pros}
            cons={insight.entity?.cons}
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
        />
        <ScoreCard
          title="问答友好度"
          score={data.scores.qa_friendly}
          desc="是否具备 FAQ/Q&A、结论前置、直接答案句式"
          pros={insight.qa?.pros}
          cons={insight.qa?.cons}
        />
        <ScoreCard
          title="技术标记"
          score={data.scores.tech_markup}
          desc="Schema.org/OG/Canonical 等结构化标记"
          pros={insight.tech?.pros}
          cons={insight.tech?.cons}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <AIReport summary={data.ai_result.summary} gaps={data.ai_result.gaps} />
        <SuggestionList items={data.ai_result.suggestions} />
      </div>

      <div className="mt-6">
        <ScoreEvidence evidence={data.score_evidence || {}} />
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <Link
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          href="/"
        >
          重新分析
        </Link>
        <Link
          className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          href="/history"
        >
          查看历史
        </Link>
      </div>
    </main>
  )
}
