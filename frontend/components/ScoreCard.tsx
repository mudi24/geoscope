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
  const color =
    score >= 80 ? 'text-emerald-700' : score >= 60 ? 'text-amber-700' : 'text-red-700'
  const hasDetails =
    (pros && pros.length > 0) || (cons && cons.length > 0) || (suggestions && suggestions.length > 0)

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        <div className={`text-xl font-bold ${color}`}>{score}</div>
      </div>
      <p className="mt-2 text-sm text-slate-600">{desc}</p>
      {hasDetails ? (
        <details className="mt-3">
          <summary className="cursor-pointer select-none text-xs font-medium text-slate-700 hover:text-slate-900">
            查看优缺点与建议
          </summary>
          <div className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
            <div>
              <div className="text-xs font-semibold text-slate-900">优点</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-700">
                {(pros || []).slice(0, 4).map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
                {(pros || []).length === 0 ? <li className="text-slate-400">—</li> : null}
              </ul>
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-900">缺点</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-700">
                {(cons || []).slice(0, 4).map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
                {(cons || []).length === 0 ? <li className="text-slate-400">—</li> : null}
              </ul>
            </div>
          </div>
          {suggestions && suggestions.length > 0 ? (
            <div className="mt-3">
              <div className="text-xs font-semibold text-slate-900">建议</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-700">
                {suggestions.slice(0, 4).map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </details>
      ) : null}
    </div>
  )
}
