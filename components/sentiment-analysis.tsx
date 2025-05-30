"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const sentimentData = [
  { segment: 1, sentiment: -0.4 },
  { segment: 2, sentiment: -0.6 },
  { segment: 3, sentiment: -0.3 },
  { segment: 4, sentiment: -0.1 },
  { segment: 5, sentiment: 0.2 },
  { segment: 6, sentiment: 0.1 },
  { segment: 7, sentiment: -0.2 },
  { segment: 8, sentiment: -0.5 },
  { segment: 9, sentiment: -0.3 },
  { segment: 10, sentiment: -0.2 },
]

const emotionData = [
  { emotion: "Anger", score: 32 },
  { emotion: "Fear", score: 18 },
  { emotion: "Sadness", score: 24 },
  { emotion: "Joy", score: 8 },
  { emotion: "Surprise", score: 12 },
  { emotion: "Disgust", score: 6 },
]

const keyPhrases = [
  { text: "economic downturn", sentiment: "negative", frequency: 3 },
  { text: "policy failure", sentiment: "negative", frequency: 2 },
  { text: "concerning trend", sentiment: "negative", frequency: 2 },
  { text: "potential benefits", sentiment: "positive", frequency: 1 },
  { text: "expert analysis", sentiment: "neutral", frequency: 2 },
]

export function SentimentAnalysis() {
  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.2) return "text-green-600"
    if (sentiment > -0.2) return "text-yellow-600"
    return "text-red-600"
  }

  const getSentimentLabel = (sentiment: number) => {
    if (sentiment > 0.2) return "Positive"
    if (sentiment > -0.2) return "Neutral"
    return "Negative"
  }

  const getEmotionColor = (emotion: string) => {
    switch (emotion) {
      case "Anger":
        return "bg-red-600"
      case "Fear":
        return "bg-purple-600"
      case "Sadness":
        return "bg-blue-600"
      case "Joy":
        return "bg-green-600"
      case "Surprise":
        return "bg-yellow-600"
      case "Disgust":
        return "bg-orange-600"
      default:
        return "bg-gray-600"
    }
  }

  const getPhraseColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-100 text-green-800"
      case "negative":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const overallSentiment = -0.27

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Sentiment Analysis</CardTitle>
          <CardDescription>Emotional tone and sentiment patterns throughout the content</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Sentiment */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Overall Sentiment</h3>
              <div className={`text-3xl font-bold ${getSentimentColor(overallSentiment)}`}>
                {getSentimentLabel(overallSentiment)}
              </div>
              <div className="text-sm text-gray-500">Score: {(overallSentiment * 100).toFixed(0)}%</div>
            </div>
            <div className="mt-4 md:mt-0">
              <div className="w-full md:w-64 h-4 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full relative">
                <div
                  className="absolute w-3 h-6 bg-black rounded-full top-1/2 transform -translate-y-1/2"
                  style={{ left: `${((overallSentiment + 1) / 2) * 100}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span>Negative</span>
                <span>Neutral</span>
                <span>Positive</span>
              </div>
            </div>
          </div>

          {/* Sentiment Flow */}
          <div>
            <h3 className="text-sm font-medium mb-4">Sentiment Flow Throughout Content</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={sentimentData}
                  margin={{
                    top: 10,
                    right: 30,
                    left: 0,
                    bottom: 0,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="segment"
                    label={{ value: "Content Segments", position: "insideBottom", offset: -5 }}
                  />
                  <YAxis
                    domain={[-1, 1]}
                    label={{ value: "Sentiment", angle: -90, position: "insideLeft" }}
                    ticks={[-1, -0.5, 0, 0.5, 1]}
                  />
                  <Tooltip
                    formatter={(value: number) => [`Sentiment: ${value.toFixed(2)}`, "Score"]}
                    labelFormatter={(label) => `Segment ${label}`}
                  />
                  <defs>
                    <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.2} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="sentiment"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#sentimentGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Emotion Analysis */}
          <div>
            <h3 className="text-sm font-medium mb-4">Emotion Distribution</h3>
            <div className="space-y-3">
              {emotionData.map((item) => (
                <div key={item.emotion} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{item.emotion}</span>
                    <span>{item.score}%</span>
                  </div>
                  <Progress value={item.score} className={`h-2 ${getEmotionColor(item.emotion)}`} />
                </div>
              ))}
            </div>
          </div>

          {/* Key Phrases */}
          <div>
            <h3 className="text-sm font-medium mb-4">Key Sentiment Phrases</h3>
            <div className="flex flex-wrap gap-2">
              {keyPhrases.map((phrase, index) => (
                <div key={index} className="flex items-center">
                  <Badge className={getPhraseColor(phrase.sentiment)}>
                    {phrase.text} {phrase.frequency > 1 && `(${phrase.frequency})`}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
