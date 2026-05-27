import type { AnalysisResponse } from '@/lib/api'

type Evidence = NonNullable<AnalysisResponse['score_evidence']>

const KEY_LABELS: Record<string, string> = {
  has_h1: '是否包含 H1 主标题',
  has_h2_6: '是否包含 H2-H6 小标题',
  avg_line_len: '平均行长度（字符）',
  avg_para_len: '平均段落长度（字符）',
  short_heading_like_lines: '疑似小标题的短行数量',

  has_definition_pattern: '是否检测到“X 是 …”定义句',
  has_parentheses_explain: '是否检测到括号解释（…）',
  has_acronym_expand: '是否检测到缩写展开（ABC(…)/ABC（…））',

  has_author: '是否包含作者/署名信息',
  has_date: '是否包含发布日期/更新时间',
  unique_links: '检测到的外链数量（去重）',

  has_faq: '是否包含 FAQ/常见问题结构',
  question_patterns_hit: '问题式表达命中数量（什么是/如何/为什么…）',
  has_conclusion: '是否包含“结论/总结/TL;DR/答案”信号',

  has_jsonld_or_schemaorg: '是否包含 JSON-LD 或 Schema.org',
  has_open_graph_or_twitter: '是否包含 OpenGraph/Twitter Card 元信息',
  has_canonical: '是否包含 canonical 链接',
}

const DIM_LABELS: Record<string, string> = {
  semantic_clarity: '语义清晰度',
  entity_completeness: '实体完整性',
  citation_credibility: '引用可信度',
  qa_friendly: '问答友好度',
  tech_markup: '技术标记',
}

function formatValue(v: unknown) {
  if (typeof v === 'boolean') return v ? '是' : '否'
  if (typeof v === 'number') return String(v)
  if (typeof v === 'string') return v
  if (v == null) return '—'
  return JSON.stringify(v)
}

function rowsFromObject(obj: Record<string, unknown>) {
  const entries = Object.entries(obj)
  // 已知 key 优先，未知 key 放后面
  entries.sort(([a], [b]) => {
    const ak = a in KEY_LABELS ? 0 : 1
    const bk = b in KEY_LABELS ? 0 : 1
    if (ak !== bk) return ak - bk
    return a.localeCompare(b)
  })
  return entries.map(([k, v]) => ({
    key: k,
    meaning: KEY_LABELS[k] || '（未定义含义）',
    value: formatValue(v),
  }))
}

export function ScoreEvidence({ evidence }: { evidence: Evidence }) {
  const dims = Object.entries(evidence || {})

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700 shadow-sm">
      <details>
        <summary className="cursor-pointer select-none font-medium text-slate-900">
          查看评分证据（字段含义说明）
        </summary>

        <div className="mt-4 space-y-5">
          {dims.length === 0 ? (
            <div className="text-slate-600">暂无评分证据。</div>
          ) : (
            dims.map(([dim, obj]) => (
              <div key={dim}>
                <div className="text-sm font-semibold text-slate-900">
                  {DIM_LABELS[dim] || dim}
                </div>
                <div className="mt-2 overflow-hidden rounded-lg border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-700">
                      <tr>
                        <th className="px-3 py-2 font-medium">字段</th>
                        <th className="px-3 py-2 font-medium">含义</th>
                        <th className="px-3 py-2 font-medium">值</th>
                      </tr>
                    </thead>
                    <tbody>
                      {typeof obj === 'object' && obj && !Array.isArray(obj)
                        ? rowsFromObject(obj as Record<string, unknown>).map((r) => (
                            <tr key={r.key} className="border-t border-slate-100">
                              <td className="px-3 py-2 font-mono text-slate-800">{r.key}</td>
                              <td className="px-3 py-2 text-slate-700">{r.meaning}</td>
                              <td className="px-3 py-2 text-slate-900">{r.value}</td>
                            </tr>
                          ))
                        : null}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}

          <div>
            <div className="text-sm font-semibold text-slate-900">原始 JSON</div>
            <pre className="mt-2 overflow-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-800">
              {JSON.stringify(evidence || {}, null, 2)}
            </pre>
          </div>
        </div>
      </details>
    </div>
  )
}

