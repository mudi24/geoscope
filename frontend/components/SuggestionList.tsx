import type { AISuggestion } from '@/lib/api'

const PRIORITY_CONFIG: Record<number, { label: string; bg: string; border: string; dot: string; icon: string }> = {
  1: { label: '高优先级', bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500', icon: '🔴' },
  2: { label: '中优先级', bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-400', icon: '🟡' },
  3: { label: '低优先级', bg: 'bg-emerald-50', border: 'border-emerald-200', dot: 'bg-emerald-500', icon: '🟢' },
}

function getPriorityCfg(p: number) {
  return PRIORITY_CONFIG[p] ?? PRIORITY_CONFIG[3]
}

export function SuggestionList({ items }: { items: AISuggestion[] }) {
  const list = [...(items || [])].sort((a, b) => a.priority - b.priority)

  const counts = list.reduce<Record<number, number>>((acc, s) => {
    acc[s.priority] = (acc[s.priority] || 0) + 1
    return acc
  }, {})

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-violet-100 text-xs">💡</span>
          <h3 className="text-sm font-semibold text-slate-900">优化建议</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
          共 {list.length} 条
        </span>
      </div>

      {/* 优先级统计 */}
      {list.length > 0 && (
        <div className="mt-3 flex gap-2">
          {([1, 2, 3] as const).map((p) =>
            counts[p] ? (
              <span
                key={p}
                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${getPriorityCfg(p).bg} ${getPriorityCfg(p).border}`}
              >
                {getPriorityCfg(p).icon} {counts[p]} 条
              </span>
            ) : null,
          )}
        </div>
      )}

      <div className="mt-4 space-y-3">
        {list.length === 0 ? (
          <p className="text-sm text-slate-400">暂无建议</p>
        ) : (
          list.map((s, idx) => {
            const cfg = getPriorityCfg(s.priority)
            return (
              <div key={idx} className={`rounded-lg border p-3 ${cfg.bg} ${cfg.border}`}>
                <div className="flex items-start gap-2">
                  <span className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${cfg.dot}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-semibold text-slate-500">{cfg.label}</span>
                      <span className="text-sm font-semibold text-slate-900">{s.issue}</span>
                    </div>
                    <p className="mt-1.5 text-sm leading-relaxed text-slate-700">{s.fix}</p>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
