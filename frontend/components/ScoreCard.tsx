export function ScoreCard({
  title,
  score,
  desc,
}: {
  title: string
  score: number
  desc: string
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
    </div>
  )
}

