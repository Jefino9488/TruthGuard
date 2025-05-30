"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendingUp, ArrowRight, AlertTriangle } from "lucide-react"

interface Topic {
  id: number
  name: string
  biasScore: number
  misinfoRisk: number
  trendDirection: "up" | "down" | "stable"
  trendPercentage: number
  sources: number
  category: string
}

const topics: Topic[] = [
  {
    id: 1,
    name: "Economic Policy",
    biasScore: 0.68,
    misinfoRisk: 0.45,
    trendDirection: "up",
    trendPercentage: 24,
    sources: 87,
    category: "Economy",
  },
  {
    id: 2,
    name: "Climate Change",
    biasScore: 0.72,
    misinfoRisk: 0.62,
    trendDirection: "up",
    trendPercentage: 18,
    sources: 65,
    category: "Environment",
  },
  {
    id: 3,
    name: "Healthcare Reform",
    biasScore: 0.58,
    misinfoRisk: 0.32,
    trendDirection: "stable",
    trendPercentage: 3,
    sources: 42,
    category: "Healthcare",
  },
  {
    id: 4,
    name: "Immigration Policy",
    biasScore: 0.85,
    misinfoRisk: 0.76,
    trendDirection: "up",
    trendPercentage: 31,
    sources: 93,
    category: "Politics",
  },
  {
    id: 5,
    name: "Tech Regulation",
    biasScore: 0.42,
    misinfoRisk: 0.28,
    trendDirection: "down",
    trendPercentage: 12,
    sources: 38,
    category: "Technology",
  },
  {
    id: 6,
    name: "Education Funding",
    biasScore: 0.51,
    misinfoRisk: 0.22,
    trendDirection: "stable",
    trendPercentage: 5,
    sources: 29,
    category: "Education",
  },
]

export function TrendingTopics() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const filteredTopics = selectedCategory ? topics.filter((topic) => topic.category === selectedCategory) : topics

  const categories = Array.from(new Set(topics.map((topic) => topic.category)))

  const getBiasColor = (score: number) => {
    if (score < 0.3) return "bg-green-100 text-green-800"
    if (score < 0.6) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  const getRiskColor = (score: number) => {
    if (score < 0.3) return "bg-green-100 text-green-800"
    if (score < 0.5) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  const getTrendColor = (direction: string) => {
    if (direction === "up") return "text-red-600"
    if (direction === "down") return "text-green-600"
    return "text-gray-600"
  }

  const getTrendIcon = (direction: string) => {
    if (direction === "up") return <TrendingUp className="h-4 w-4 rotate-45" />
    if (direction === "down") return <TrendingUp className="h-4 w-4 -rotate-45" />
    return <TrendingUp className="h-4 w-4 rotate-0" />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedCategory === null ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedCategory(null)}
        >
          All Topics
        </Button>
        {categories.map((category) => (
          <Button
            key={category}
            variant={selectedCategory === category ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(category)}
          >
            {category}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTopics.map((topic) => (
          <Card key={topic.id} className="overflow-hidden">
            <CardContent className="p-0">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-lg mb-1">{topic.name}</h3>
                    <Badge variant="outline">{topic.category}</Badge>
                  </div>
                  <div className={`flex items-center space-x-1 ${getTrendColor(topic.trendDirection)}`}>
                    {getTrendIcon(topic.trendDirection)}
                    <span className="font-bold">{topic.trendPercentage}%</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Bias Score:</span>
                    <Badge className={getBiasColor(topic.biasScore)}>{(topic.biasScore * 100).toFixed(0)}%</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Misinfo Risk:</span>
                    <Badge className={getRiskColor(topic.misinfoRisk)}>{(topic.misinfoRisk * 100).toFixed(0)}%</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Sources:</span>
                    <span className="text-sm font-medium">{topic.sources} outlets</span>
                  </div>
                </div>

                {topic.misinfoRisk > 0.6 && (
                  <div className="mt-4 p-3 bg-red-50 rounded-md flex items-start space-x-2">
                    <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                    <span className="text-xs text-red-800">High misinformation activity detected in this topic</span>
                  </div>
                )}
              </div>

              <div className="border-t p-4 bg-gray-50">
                <Button variant="ghost" size="sm" className="w-full justify-between">
                  View Topic Analysis
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
