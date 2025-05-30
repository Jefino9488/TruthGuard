"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

const data = [
  { date: "Jan 1", leftBias: 45, rightBias: 38, neutralContent: 17 },
  { date: "Jan 15", leftBias: 48, rightBias: 40, neutralContent: 12 },
  { date: "Feb 1", leftBias: 52, rightBias: 42, neutralContent: 6 },
  { date: "Feb 15", leftBias: 50, rightBias: 45, neutralContent: 5 },
  { date: "Mar 1", leftBias: 55, rightBias: 40, neutralContent: 5 },
  { date: "Mar 15", leftBias: 58, rightBias: 38, neutralContent: 4 },
  { date: "Apr 1", leftBias: 60, rightBias: 36, neutralContent: 4 },
  { date: "Apr 15", leftBias: 57, rightBias: 39, neutralContent: 4 },
  { date: "May 1", leftBias: 62, rightBias: 35, neutralContent: 3 },
]

export function BiasTimeline() {
  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="leftBias" stroke="#3b82f6" name="Left-Leaning Content %" />
          <Line type="monotone" dataKey="rightBias" stroke="#ef4444" name="Right-Leaning Content %" />
          <Line type="monotone" dataKey="neutralContent" stroke="#10b981" name="Neutral Content %" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
