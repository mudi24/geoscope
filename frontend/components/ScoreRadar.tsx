'use client'

import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

export type RadarDatum = { name: string; score: number }

export function ScoreRadar({
  data,
  totalScore,
}: {
  data: RadarDatum[]
  totalScore?: number
}) {
  return (
    <div className="w-full rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-900">五维雷达图</div>
        {typeof totalScore === 'number' ? (
          <div className="text-sm font-semibold text-slate-700">
            总分 <span className="text-slate-900">{totalScore}</span>
          </div>
        ) : null}
      </div>
      <div className="mt-3 h-60">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid />
            <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
            <Tooltip />
            <Radar
              dataKey="score"
              stroke="#4f46e5"
              fill="#4f46e5"
              fillOpacity={0.25}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
