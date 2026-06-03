'use client'

import { useState } from 'react'

function scoreColor(score: number) {
  if (score >= 80) return { text: 'text-emerald-700', bg: 'bg-emerald-500', ring: 'ring-emerald-200', badge: 'bg-emerald-50 text-emerald-700' }
  if (score >= 60) return { text: 'text-amber-700', bg: 'bg-amber-400', ring: 'ring-amber-200', badge: 'bg-amber-50 text-amber-700' }
  return { text: 'text-red-700', bg: 'bg-red-500', ring: 'ring-red-200', badge: 'bg-red-50 text-red-700' }
}

export function ScoreCard({
  title,
  score,
  desc,
  pros,
  cons,
  suggestions,
}: {
  title: string
  score: number
  desc: string
  pros?: string[]
  cons?: string[]
  suggestions?: string[]
}) {
  const [open, setOpen] = useState(false)
  const c = scoreColor(score)
  const hasDetails =
    (pros && pros.length > 0) || (cons && cons.length > 0) || (suggestions && suggestions.length > 0)

  return (
    <div className={`rounded-xl border border-slate-200 bg-white shadow-sm transition-shadow ${open ? 'shadow-md' : ''}`}>
      <div
        className={`flex cursor-pointer items-start gap-4 p-4 ${hasDetails ? 'hover:bg-slate-50/60' : ''}`}
        onClick={() => hasDetails && setOpen((v) => !v)}
        role={hasDetails ? 'button' : undefined}
        aria-expanded={hasDetails ? open : undefined}
      >
        {/* 分数圆环 */}
        <div className={`flex h-12 w-12 flex-shrink-0 flex-col items-center justify-center rounded-full ring-2 ${c.ring}`}>
          <span className={`text-lg font-extrabold leading-none ${c.text}`}>{score}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
            {hasDetails && (
              <span className="text-xs text-slate-400">{open ? '▲ 收起' : '▼ 展开'}</span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-slate-500">{desc}</p>
          {/* 进度条 */}
          <div className="mt-2 h-1.5 w-full rounded-full bg-slate-100">
            <div
              className={`h-1.5 rounded-full ${c.bg} transition-all duration-500`}
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
      </div>

      {/* 展开详情 */}
      {open && hasDetails && (
        <div className="border-t border-slate-100 px-4 pb-4 pt-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                <span>✅</span> 优点
              </div>
              <ul className="mt-1.5 space-y-1">
                {(pros || []).length > 0
                  ? (pros || []).slice(0, 4).map((p, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-slate-700">
                        <span className="mt-0.5 text-emerald-400">•</span> {p}
                      </li>
                    ))
                  : <li className="text-xs text-slate-400">暂无</li>}
              </ul>
            </div>
            <div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-red-600">
                <span>❌</span> 缺点
              </div>
              <ul className="mt-1.5 space-y-1">
                {(cons || []).length > 0
                  ? (cons || []).slice(0, 4).map((c, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-slate-700">
                        <span className="mt-0.5 text-red-400">•</span> {c}
                      </li>
                    ))
                  : <li className="text-xs text-slate-400">暂无</li>}
              </ul>
            </div>
          </div>

          {suggestions && suggestions.length > 0 && (
            <div className="mt-3 rounded-lg bg-indigo-50 p-3">
              <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-indigo-700">
                <span>💡</span> 改进建议
              </div>
              <ul className="space-y-1">
                {suggestions.slice(0, 4).map((s, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-indigo-800">
                    <span className="mt-0.5 font-bold">{i + 1}.</span> {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
