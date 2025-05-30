"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, CheckCircle, TrendingUp, Pause, Play } from "lucide-react"

interface RealTimeUpdate {
  type: string
  data?: any[]
  message?: string
  timestamp: string
  stats?: {
    total_processed: number
    bias_detected: number
    misinformation_flagged: number
  }
}

export function RealTimeFeed() {
  const [updates, setUpdates] = useState<RealTimeUpdate[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [stats, setStats] = useState({
    total_processed: 0,
    bias_detected: 0,
    misinformation_flagged: 0,
  })

  useEffect(() => {
    if (isPaused) return

    const eventSource = new EventSource("/api/realtime")

    eventSource.onopen = () => {
      setIsConnected(true)
    }

    eventSource.onmessage = (event) => {
      try {
        const update: RealTimeUpdate = JSON.parse(event.data)

        setUpdates((prev) => [update, ...prev.slice(0, 19)]) // Keep last 20 updates

        if (update.stats) {
          setStats(update.stats)
        }
      } catch (error) {
        console.error("Failed to parse real-time update:", error)
      }
    }

    eventSource.onerror = () => {
      setIsConnected(false)
    }

    return () => {
      eventSource.close()
      setIsConnected(false)
    }
  }, [isPaused])

  const togglePause = () => {
    setIsPaused(!isPaused)
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Real-Time Processing Feed</CardTitle>
              <CardDescription>Live updates from the TruthGuard AI pipeline</CardDescription>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`}
                ></div>
                <span className="text-sm">{isConnected ? "Connected" : "Disconnected"}</span>
              </div>
              <Button variant="outline" size="sm" onClick={togglePause}>
                {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
                {isPaused ? "Resume" : "Pause"}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.total_processed.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Articles Processed</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{stats.bias_detected.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Bias Detected</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{stats.misinformation_flagged.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Misinformation Flagged</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Updates */}
      <Card>
        <CardHeader>
          <CardTitle>Live Activity Stream</CardTitle>
          <CardDescription>Real-time processing updates and alerts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {updates.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {isPaused ? "Feed paused" : "Waiting for updates..."}
              </div>
            ) : (
              updates.map((update, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                  <div className="mt-1">
                    {update.type === "connection" ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : update.type === "article_processed" ? (
                      <TrendingUp className="h-5 w-5 text-blue-600" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">
                        {update.type === "connection" && "System Connected"}
                        {update.type === "article_processed" && "Articles Processed"}
                        {update.type === "bias_alert" && "High Bias Detected"}
                        {update.type === "misinformation_alert" && "Misinformation Alert"}
                      </h4>
                      <span className="text-xs text-gray-500">{new Date(update.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {update.message || `${update.data?.length || 0} new articles analyzed`}
                    </p>
                    {update.data && update.data.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {update.data.slice(0, 3).map((article: any, i: number) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {article.source}
                          </Badge>
                        ))}
                        {update.data.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{update.data.length - 3} more
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
