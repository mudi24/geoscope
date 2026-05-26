import type { AISuggestion } from '@/lib/api'

function badge(priority: number) {
  if (priority === 1) return 'bg-red-100 text-red-700 border-red-200'
  if (priority === 2) return 'bg-amber-100 text-amber-800 border-amber-200'
  return 'bg-emerald-100 text-emerald-800 border-emerald-200'
}

export function SuggestionList({ items }: { items: AISuggestion[] }) {
  const list = [...(items || [])].sort((a, b) => a.priority - b.priority)
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">优化建议</h3>
      <div className="mt-3 space-y-3">
        {list.map((s, idx) => (
          <div key={idx} className="rounded-lg border border-slate-200 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${badge(
                  s.priority,
                )}`}
              >
                P{s.priority}
              </span>
              <span className="text-sm font-medium text-slate-900">{s.issue}</span>
            </div>
            <p className="mt-2 text-sm text-slate-700">{s.fix}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

