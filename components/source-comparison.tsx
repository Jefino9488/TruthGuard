"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

const data = [
  { source: "Reuters", bias: 0.2, misinformation: 0.1 },
  { source: "AP News", bias: 0.15, misinformation: 0.08 },
  { source: "CNN", bias: 0.6, misinformation: 0.3 },
  { source: "Fox News", bias: 0.8, misinformation: 0.5 },
  { source: "MSNBC", bias: 0.7, misinformation: 0.4 },
  { source: "BBC", bias: 0.25, misinformation: 0.12 },
]

export function SourceComparison() {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="source" />
          <YAxis />
          <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
          <Legend />
          <Bar dataKey="bias" fill="#3b82f6" name="Bias Score" />
          <Bar dataKey="misinformation" fill="#ef4444" name="Misinformation Risk" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
