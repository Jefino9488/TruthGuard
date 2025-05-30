"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface SourceData {
  name: string
  bias: "left" | "center-left" | "center" | "center-right" | "right"
  topics: {
    [key: string]: {
      coverage: number
      sentiment: number
      framing: string
    }
  }
}

const sources: SourceData[] = [
  {
    name: "CNN",
    bias: "center-left",
    topics: {
      Economy: { coverage: 7, sentiment: -0.3, framing: "Critical" },
      Healthcare: { coverage: 8, sentiment: 0.2, framing: "Supportive" },
      Immigration: { coverage: 6, sentiment: 0.1, framing: "Humanitarian" },
      Climate: { coverage: 9, sentiment: 0.4, framing: "Urgent" },
    },
  },
  {
    name: "Fox News",
    bias: "right",
    topics: {
      Economy: { coverage: 8, sentiment: 0.5, framing: "Positive" },
      Healthcare: { coverage: 5, sentiment: -0.4, framing: "Critical" },
      Immigration: { coverage: 9, sentiment: -0.6, framing: "Security" },
      Climate: { coverage: 4, sentiment: -0.2, framing: "Skeptical" },
    },
  },
  {
    name: "Reuters",
    bias: "center",
    topics: {
      Economy: { coverage: 8, sentiment: 0.1, framing: "Factual" },
      Healthcare: { coverage: 6, sentiment: 0.0, framing: "Balanced" },
      Immigration: { coverage: 5, sentiment: 0.0, framing: "Factual" },
      Climate: { coverage: 7, sentiment: 0.1, framing: "Scientific" },
    },
  },
  {
    name: "MSNBC",
    bias: "left",
    topics: {
      Economy: { coverage: 6, sentiment: -0.4, framing: "Critical" },
      Healthcare: { coverage: 9, sentiment: 0.5, framing: "Supportive" },
      Immigration: { coverage: 7, sentiment: 0.6, framing: "Humanitarian" },
      Climate: { coverage: 8, sentiment: 0.7, framing: "Urgent" },
    },
  },
  {
    name: "WSJ",
    bias: "center-right",
    topics: {
      Economy: { coverage: 10, sentiment: 0.3, framing: "Business" },
      Healthcare: { coverage: 5, sentiment: -0.1, framing: "Market" },
      Immigration: { coverage: 4, sentiment: -0.2, framing: "Economic" },
      Climate: { coverage: 5, sentiment: 0.0, framing: "Balanced" },
    },
  },
]

const topics = ["Economy", "Healthcare", "Immigration", "Climate"]

export function SourceComparisonMatrix() {
  const getBiasColor = (bias: string) => {
    switch (bias) {
      case "left":
        return "bg-blue-600 text-white"
      case "center-left":
        return "bg-blue-300 text-blue-900"
      case "center":
        return "bg-gray-200 text-gray-900"
      case "center-right":
        return "bg-red-300 text-red-900"
      case "right":
        return "bg-red-600 text-white"
      default:
        return "bg-gray-200 text-gray-900"
    }
  }

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.3) return "text-green-600"
    if (sentiment < -0.3) return "text-red-600"
    return "text-gray-600"
  }

  const getCoverageSize = (coverage: number) => {
    return `${Math.max(coverage * 8, 16)}px`
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-left">Source</th>
            {topics.map((topic) => (
              <th key={topic} className="p-2 text-center">
                {topic}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sources.map((source) => (
            <tr key={source.name} className="border-t">
              <td className="p-3">
                <div className="flex items-center space-x-2">
                  <span className="font-medium">{source.name}</span>
                  <Badge className={getBiasColor(source.bias)}>
                    {source.bias.charAt(0).toUpperCase() + source.bias.slice(1)}
                  </Badge>
                </div>
              </td>
              {topics.map((topic) => {
                const topicData = source.topics[topic]
                return (
                  <td key={topic} className="p-2">
                    <Card className="border-0 shadow-none">
                      <CardContent className="p-3 text-center">
                        <div
                          className="mx-auto rounded-full bg-blue-100 flex items-center justify-center mb-1"
                          style={{
                            width: getCoverageSize(topicData.coverage),
                            height: getCoverageSize(topicData.coverage),
                          }}
                        >
                          <span className="text-xs font-medium">{topicData.coverage}</span>
                        </div>
                        <div className={`text-sm font-medium ${getSentimentColor(topicData.sentiment)}`}>
                          {topicData.sentiment > 0 ? "+" : ""}
                          {topicData.sentiment.toFixed(1)}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">{topicData.framing}</div>
                      </CardContent>
                    </Card>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-4 text-sm text-gray-500 flex items-center justify-center space-x-6">
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full bg-blue-100 mr-2"></div>
          <span>Circle size = Coverage intensity</span>
        </div>
        <div className="flex items-center">
          <span className="text-green-600 font-medium mr-1">+0.5</span>
          <span>= Positive sentiment</span>
        </div>
        <div className="flex items-center">
          <span className="text-red-600 font-medium mr-1">-0.5</span>
          <span>= Negative sentiment</span>
        </div>
      </div>
    </div>
  )
}
