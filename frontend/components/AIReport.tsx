export function AIReport({ summary, gaps }: { summary: string; gaps: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      {/* 摘要 */}
      <div className="flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-xs">🤖</span>
        <h3 className="text-sm font-semibold text-slate-900">AI 摘要</h3>
      </div>
      <p className="mt-3 rounded-lg bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-700 border border-slate-100">
        {summary || '（暂无摘要）'}
      </p>

      {/* 知识缺口 */}
      <div className="mt-5 flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-xs">🕳</span>
        <h3 className="text-sm font-semibold text-slate-900">知识缺口</h3>
        {gaps && gaps.length > 0 && (
          <span className="ml-auto rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
            {gaps.length} 项
          </span>
        )}
      </div>
      {(gaps || []).length === 0 ? (
        <p className="mt-2 text-sm text-slate-400">未发现明显知识缺口 🎉</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {gaps.map((g, i) => (
            <li
              key={i}
              className="flex items-start gap-2.5 rounded-lg border border-red-100 bg-red-50 px-3 py-2.5 text-sm text-red-800"
            >
              <span className="mt-0.5 flex-shrink-0 font-bold text-red-400">{i + 1}.</span>
              {g}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
