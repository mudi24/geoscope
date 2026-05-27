export function ScoreCard({
  title,
  score,
  desc,
  pros,
  cons,
}: {
  title: string
  score: number
  desc: string
  pros?: string[]
  cons?: string[]
}) {
  const color =
    score >= 80 ? 'text-emerald-700' : score >= 60 ? 'text-amber-700' : 'text-red-700'

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        <div className={`text-xl font-bold ${color}`}>{score}</div>
      </div>
      <p className="mt-2 text-sm text-slate-600">{desc}</p>
      {(pros && pros.length > 0) || (cons && cons.length > 0) ? (
        <div className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <div className="text-xs font-semibold text-slate-900">优点</div>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-700">
              {(pros || []).slice(0, 3).map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-900">缺点</div>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-700">
              {(cons || []).slice(0, 3).map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  )
}
