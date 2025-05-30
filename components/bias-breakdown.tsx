"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { AlertTriangle, Info } from "lucide-react"

const biasCategories = [
  { name: "Political", score: 72, description: "Favors specific political viewpoints or policies" },
  { name: "Source", score: 58, description: "Relies on sources with known biases" },
  { name: "Language", score: 64, description: "Uses emotionally charged or persuasive language" },
  { name: "Framing", score: 68, description: "Presents information within a specific narrative frame" },
  { name: "Selection", score: 59, description: "Selectively includes or excludes relevant information" },
]

const biasIndicators = [
  {
    category: "Language",
    indicators: [
      { text: "Emotional language", frequency: 8, severity: "high" },
      { text: "Loaded terms", frequency: 6, severity: "medium" },
      { text: "Exaggeration", frequency: 4, severity: "medium" },
      { text: "Subjective descriptors", frequency: 7, severity: "high" },
    ],
  },
  {
    category: "Framing",
    indicators: [
      { text: "One-sided presentation", frequency: 3, severity: "high" },
      { text: "Misleading context", frequency: 2, severity: "medium" },
      { text: "Implied causation", frequency: 4, severity: "medium" },
    ],
  },
  {
    category: "Selection",
    indicators: [
      { text: "Cherry-picked data", frequency: 2, severity: "high" },
      { text: "Missing context", frequency: 3, severity: "medium" },
      { text: "Omitted perspectives", frequency: 5, severity: "high" },
    ],
  },
]

const politicalLeaningData = [
  { viewpoint: "Far Left", score: 15 },
  { viewpoint: "Left", score: 42 },
  { viewpoint: "Center Left", score: 28 },
  { viewpoint: "Center", score: 10 },
  { viewpoint: "Center Right", score: 3 },
  { viewpoint: "Right", score: 2 },
  { viewpoint: "Far Right", score: 0 },
]

export function BiasBreakdown() {
  const getBiasColor = (score: number) => {
    if (score < 30) return "text-green-600"
    if (score < 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getBiasLevel = (score: number) => {
    if (score < 30) return "Low"
    if (score < 60) return "Moderate"
    return "High"
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "low":
        return "bg-green-100 text-green-800"
      case "medium":
        return "bg-yellow-100 text-yellow-800"
      case "high":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  // Calculate overall bias score (average of all categories)
  const overallBiasScore = Math.round(
    biasCategories.reduce((sum, category) => sum + category.score, 0) / biasCategories.length,
  )

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Bias Analysis</CardTitle>
          <CardDescription>Detailed breakdown of bias patterns and indicators</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Bias Score */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Overall Bias Score</h3>
              <div className={`text-3xl font-bold ${getBiasColor(overallBiasScore)}`}>
                {getBiasLevel(overallBiasScore)}
              </div>
              <div className="text-sm text-gray-500">{overallBiasScore}/100</div>
            </div>
            <div className="mt-4 md:mt-0 md:w-64">
              <Progress value={overallBiasScore} className="h-2" />
              <div className="flex justify-between text-xs mt-1">
                <span>Minimal Bias</span>
                <span>Extreme Bias</span>
              </div>
            </div>
          </div>

          {/* Bias Categories */}
          <div>
            <h3 className="text-sm font-medium mb-4">Bias Categories</h3>
            <div className="space-y-3">
              {biasCategories.map((category) => (
                <div key={category.name} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <div className="flex items-center">
                      <span className="font-medium">{category.name}</span>
                      <span className="text-xs text-gray-500 ml-2">({category.description})</span>
                    </div>
                    <span className={getBiasColor(category.score)}>{category.score}%</span>
                  </div>
                  <Progress value={category.score} className="h-2" />
                </div>
              ))}
            </div>
          </div>

          {/* Political Leaning */}
          <div>
            <h3 className="text-sm font-medium mb-4">Political Leaning Analysis</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={politicalLeaningData}
                  layout="vertical"
                  margin={{
                    top: 5,
                    right: 30,
                    left: 80,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis dataKey="viewpoint" type="category" width={80} />
                  <Tooltip formatter={(value) => [`${value}%`, "Score"]} />
                  <Bar dataKey="score" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bias Indicators */}
          <div>
            <h3 className="text-sm font-medium mb-4">Detected Bias Indicators</h3>
            <Tabs defaultValue="Language">
              <TabsList className="grid grid-cols-3">
                <TabsTrigger value="Language">Language</TabsTrigger>
                <TabsTrigger value="Framing">Framing</TabsTrigger>
                <TabsTrigger value="Selection">Selection</TabsTrigger>
              </TabsList>
              {biasIndicators.map((category) => (
                <TabsContent key={category.category} value={category.category} className="mt-4">
                  <div className="space-y-3">
                    {category.indicators.map((indicator, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-2">
                          <AlertTriangle
                            className={`h-4 w-4 ${indicator.severity === "high" ? "text-red-500" : indicator.severity === "medium" ? "text-yellow-500" : "text-green-500"}`}
                          />
                          <span>{indicator.text}</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-gray-500">
                            Found {indicator.frequency} {indicator.frequency === 1 ? "time" : "times"}
                          </span>
                          <Badge className={getSeverityColor(indicator.severity)}>
                            {indicator.severity.charAt(0).toUpperCase() + indicator.severity.slice(1)}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </div>

          {/* Methodology Note */}
          <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
            <div className="flex items-start space-x-3">
              <Info className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-blue-800">Bias Detection Methodology</h3>
                <p className="mt-1 text-sm text-blue-800">
                  Our AI analyzes multiple dimensions of bias including language patterns, framing techniques, source
                  selection, and narrative structure. The analysis is based on a comprehensive model trained on diverse
                  media content.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
