export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type AISuggestion = {
  priority: number
  issue: string
  fix: string
}

export type AIResult = {
  summary: string
  gaps: string[]
  suggestions: AISuggestion[]
}

export type GeoScores = {
  semantic_clarity: number
  entity_completeness: number
  citation_credibility: number
  qa_friendly: number
  tech_markup: number
  total_score: number
}

export type AnalysisResponse = {
  id: number
  url: string
  title?: string | null
  domain?: string | null
  scores: GeoScores
  ai_result: AIResult
  fetch_method: string
  created_at: string
}

export type HistoryItem = {
  id: number
  url: string
  title?: string | null
  total_score: number
  created_at: string
}

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `${res.status} ${res.statusText}`)
  }
  return (await res.json()) as T
}

export async function analyzeUrl(url: string): Promise<{ id: number }> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  return asJson<{ id: number }>(res)
}

export async function getAnalysis(id: string): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/analysis/${id}`, {
    cache: 'no-store',
  })
  return asJson<AnalysisResponse>(res)
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/api/history`, { cache: 'no-store' })
  return asJson<HistoryItem[]>(res)
}

