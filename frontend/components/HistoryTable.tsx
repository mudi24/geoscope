import type { HistoryItem } from '@/lib/api'
import Link from 'next/link'

function scoreColor(score: number) {
  if (score >= 80) return 'text-emerald-700'
  if (score >= 60) return 'text-amber-700'
  return 'text-red-700'
}

export function HistoryTable({ items }: { items: HistoryItem[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-slate-700">
          <tr>
            <th className="px-4 py-3 font-medium">时间</th>
            <th className="px-4 py-3 font-medium">标题</th>
            <th className="px-4 py-3 font-medium">状态</th>
            <th className="px-4 py-3 font-medium">总分</th>
            <th className="px-4 py-3 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.id} className="border-t border-slate-100">
              <td className="px-4 py-3 text-slate-600">
                {new Date(it.created_at).toLocaleString()}
              </td>
              <td className="px-4 py-3 text-slate-900">{it.title || it.url}</td>
              <td className="px-4 py-3 text-slate-700">{it.status}</td>
              <td className={`px-4 py-3 font-semibold ${scoreColor(it.total_score)}`}>
                {it.total_score}
              </td>
              <td className="px-4 py-3">
                <Link
                  className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  href={`/analyze/${it.id}`}
                >
                  查看详情
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
