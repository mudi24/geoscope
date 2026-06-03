'use client'

import { useState } from 'react'
import type { AnalysisResponse } from '@/lib/api'

type Evidence = NonNullable<AnalysisResponse['score_evidence']>

const KEY_LABELS: Record<string, string> = {
  has_h1: '是否包含 H1 主标题',
  has_h2_6: '是否包含 H2-H6 小标题',
  avg_line_len: '平均行长度（字符）',
  avg_para_len: '平均段落长度（字符）',
  short_heading_like_lines: '疑似小标题的短行数量',

  has_definition_pattern: '是否检测到"X 是 …"定义句',
  has_parentheses_explain: '是否检测到括号解释（…）',
  has_acronym_expand: '是否检测到缩写展开',

  has_author: '是否包含作者/署名信息',
  has_date: '是否包含发布日期/更新时间',
  unique_links: '检测到的外链数量（去重）',

  has_faq: '是否包含 FAQ/常见问题结构',
  question_patterns_hit: '问题式表达命中数量',
  has_conclusion: '是否包含"结论/总结/TL;DR"信号',

  has_jsonld_or_schemaorg: '是否包含 JSON-LD 或 Schema.org',
  has_open_graph_or_twitter: '是否包含 OpenGraph/Twitter Card',
  has_canonical: '是否包含 canonical 链接',
}

const DIM_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  semantic_clarity:      { label: '语义清晰度', icon: '📐', color: 'text-indigo-600' },
  entity_completeness:   { label: '实体完整性', icon: '🔍', color: 'text-violet-600' },
  citation_credibility:  { label: '引用可信度', icon: '🔗', color: 'text-sky-600' },
  qa_friendly:           { label: '问答友好度', icon: '💬', color: 'text-amber-600' },
  tech_markup:           { label: '技术标记',   icon: '🏷', color: 'text-emerald-600' },
}

function formatValue(v: unknown): { text: string; type: 'bool-true' | 'bool-false' | 'number' | 'other' } {
  if (typeof v === 'boolean') return { text: v ? '是' : '否', type: v ? 'bool-true' : 'bool-false' }
  if (typeof v === 'number') return { text: String(v), type: 'number' }
  if (typeof v === 'string') return { text: v, type: 'other' }
  if (v == null) return { text: '—', type: 'other' }
  return { text: JSON.stringify(v), type: 'other' }
}

function ValueBadge({ v }: { v: unknown }) {
  const { text, type } = formatValue(v)
  if (type === 'bool-true')
    return <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">✓ {text}</span>
  if (type === 'bool-false')
    return <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">✗ {text}</span>
  if (type === 'number')
    return <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-mono font-medium text-slate-700">{text}</span>
  return <span className="text-xs text-slate-600">{text}</span>
}

function rowsFromObject(obj: Record<string, unknown>) {
  const entries = Object.entries(obj)
  entries.sort(([a], [b]) => {
    const ak = a in KEY_LABELS ? 0 : 1
    const bk = b in KEY_LABELS ? 0 : 1
    if (ak !== bk) return ak - bk
    return a.localeCompare(b)
  })
  return entries.map(([k, v]) => ({ key: k, meaning: KEY_LABELS[k] || k, rawValue: v }))
}

function DimSection({ dim, obj }: { dim: string; obj: unknown }) {
  const [open, setOpen] = useState(true)
  const cfg = DIM_CONFIG[dim] || { label: dim, icon: '📊', color: 'text-slate-600' }
  if (typeof obj !== 'object' || !obj || Array.isArray(obj)) return null
  const rows = rowsFromObject(obj as Record<string, unknown>)

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
      <button
        className="flex w-full items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <span className="text-base">{cfg.icon}</span>
          <span className={`text-sm font-semibold ${cfg.color}`}>{cfg.label}</span>
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
            {rows.length} 项
          </span>
        </div>
        <span className="text-xs text-slate-400">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="border-t border-slate-100">
          <div className="divide-y divide-slate-50">
            {rows.map((r) => (
              <div key={r.key} className="flex items-center justify-between gap-4 px-4 py-2.5">
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-mono text-slate-500">{r.key}</div>
                  <div className="text-xs text-slate-700">{r.meaning}</div>
                </div>
                <ValueBadge v={r.rawValue} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function ScoreEvidence({ evidence }: { evidence: Evidence }) {
  const [showRaw, setShowRaw] = useState(false)
  const dims = Object.entries(evidence || {})

  return (
    <div className="space-y-3">
      {dims.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm">
          暂无评分证据。
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {dims.map(([dim, obj]) => (
              <DimSection key={dim} dim={dim} obj={obj} />
            ))}
          </div>

          {/* 原始 JSON 折叠 */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <button
              className="flex w-full items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
              onClick={() => setShowRaw((v) => !v)}
              aria-expanded={showRaw}
            >
              <span className="flex items-center gap-2 text-sm font-medium text-slate-600">
                <span>{'{ }'}</span> 原始 JSON
              </span>
              <span className="text-xs text-slate-400">{showRaw ? '▲ 收起' : '▼ 展开'}</span>
            </button>
            {showRaw && (
              <pre className="border-t border-slate-100 overflow-auto bg-slate-50 p-4 text-xs text-slate-700">
                {JSON.stringify(evidence || {}, null, 2)}
              </pre>
            )}
          </div>
        </>
      )}
    </div>
  )
}
