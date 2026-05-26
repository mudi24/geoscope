export function AIReport({ summary, gaps }: { summary: string; gaps: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">AI 摘要</h3>
      <p className="mt-2 rounded-lg bg-slate-50 p-3 text-sm text-slate-800">
        {summary || '（暂无摘要）'}
      </p>

      <h3 className="mt-4 text-sm font-semibold text-slate-900">知识缺口</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-red-700">
        {(gaps || []).map((g, i) => (
          <li key={i}>{g}</li>
        ))}
      </ul>
    </div>
  )
}

