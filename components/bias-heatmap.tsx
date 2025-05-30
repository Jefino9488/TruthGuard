"use client"

const topics = ["Politics", "Economy", "Healthcare", "Technology", "Environment", "Sports"]
const sources = ["CNN", "Fox News", "Reuters", "BBC", "MSNBC", "AP News"]

// Generate mock bias data (0-1 scale)
const generateBiasData = () => {
  const data = []
  for (let i = 0; i < topics.length; i++) {
    for (let j = 0; j < sources.length; j++) {
      data.push({
        topic: topics[i],
        source: sources[j],
        bias: Math.random(),
        x: j,
        y: i,
      })
    }
  }
  return data
}

const biasData = generateBiasData()

export function BiasHeatmap() {
  const getBiasColor = (bias: number) => {
    if (bias < 0.2) return "#10b981" // Green
    if (bias < 0.4) return "#84cc16" // Light green
    if (bias < 0.6) return "#eab308" // Yellow
    if (bias < 0.8) return "#f97316" // Orange
    return "#ef4444" // Red
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-7 gap-2 text-sm">
        <div></div>
        {sources.map((source) => (
          <div key={source} className="text-center font-medium p-2">
            {source}
          </div>
        ))}

        {topics.map((topic, topicIndex) => (
          <div key={topic} className="contents">
            <div className="font-medium p-2 text-right">{topic}</div>
            {sources.map((source, sourceIndex) => {
              const dataPoint = biasData.find((d) => d.topic === topic && d.source === source)
              return (
                <div
                  key={`${topic}-${source}`}
                  className="h-12 rounded flex items-center justify-center text-white text-xs font-medium"
                  style={{ backgroundColor: getBiasColor(dataPoint?.bias || 0) }}
                  title={`${topic} - ${source}: ${((dataPoint?.bias || 0) * 100).toFixed(1)}% bias`}
                >
                  {((dataPoint?.bias || 0) * 100).toFixed(0)}%
                </div>
              )
            })}
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center space-x-4 text-sm">
        <span>Low Bias</span>
        <div className="flex space-x-1">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: "#10b981" }}></div>
          <div className="w-4 h-4 rounded" style={{ backgroundColor: "#84cc16" }}></div>
          <div className="w-4 h-4 rounded" style={{ backgroundColor: "#eab308" }}></div>
          <div className="w-4 h-4 rounded" style={{ backgroundColor: "#f97316" }}></div>
          <div className="w-4 h-4 rounded" style={{ backgroundColor: "#ef4444" }}></div>
        </div>
        <span>High Bias</span>
      </div>
    </div>
  )
}
