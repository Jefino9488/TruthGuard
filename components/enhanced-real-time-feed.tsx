"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AlertTriangle, CheckCircle, TrendingUp, Pause, Play, Database, Cpu, Globe, Activity } from "lucide-react"

interface EnhancedRealTimeUpdate {
  type: string
  data?: {
    articles?: any[]
    system_stats?: any
    alerts?: any[]
    processing_pipeline?: any
  }
  message?: string
  timestamp: string
  stats?: {
    total_processed: number
    bias_detected: number
    misinformation_flagged: number
    high_credibility: number
    processing_rate: number
  }
}

export function EnhancedRealTimeFeed() {
  const [updates, setUpdates] = useState<EnhancedRealTimeUpdate[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [stats, setStats] = useState({
    total_processed: 0,
    bias_detected: 0,
    misinformation_flagged: 0,
    high_credibility: 0,
    processing_rate: 0,
  })
  const [systemStatus, setSystemStatus] = useState({
    mongodb_status: "connecting",
    google_ai_status: "connecting",
    gitlab_pipeline: "connecting",
    vector_search: "connecting",
  })

  useEffect(() => {
    if (isPaused) return

    const eventSource = new EventSource("/api/realtime")

    eventSource.onopen = () => {
      setIsConnected(true)
    }

    eventSource.onmessage = (event) => {
      try {
        const update: EnhancedRealTimeUpdate = JSON.parse(event.data)

        setUpdates((prev) => [update, ...prev.slice(0, 49)]) // Keep last 50 updates

        if (update.stats) {
          setStats(update.stats)
        }

        if (update.data?.processing_pipeline) {
          setSystemStatus(update.data.processing_pipeline)
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
      case "operational":
      case "running":
      case "active":
        return "bg-green-500"
      case "connecting":
      case "starting":
        return "bg-yellow-500 animate-pulse"
      default:
        return "bg-red-500"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "connected":
      case "operational":
      case "running":
      case "active":
        return "Online"
      case "connecting":
      case "starting":
        return "Starting"
      default:
        return "Offline"
    }
  }

  return (
    <div className="space-y-6">
      {/* Enhanced System Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-6 w-6 text-blue-600" />
                <span>TruthGuard Real-Time Processing</span>
              </CardTitle>
              <CardDescription>
                Live AI-powered analysis with MongoDB, Google Cloud AI, and GitLab CI/CD
              </CardDescription>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`}
                ></div>
                <span className="text-sm font-medium">{isConnected ? "Connected" : "Disconnected"}</span>
              </div>
              <Button variant="outline" size="sm" onClick={togglePause}>
                {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
                {isPaused ? "Resume" : "Pause"}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* System Components Status */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="flex items-center space-x-3 p-3 border rounded-lg">
              <Database className="h-8 w-8 text-blue-600" />
              <div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus.mongodb_status)}`}></div>
                  <span className="font-medium">MongoDB Atlas</span>
                </div>
                <span className="text-sm text-gray-600">{getStatusText(systemStatus.mongodb_status)}</span>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 border rounded-lg">
              <Cpu className="h-8 w-8 text-green-600" />
              <div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus.google_ai_status)}`}></div>
                  <span className="font-medium">Google Cloud AI</span>
                </div>
                <span className="text-sm text-gray-600">{getStatusText(systemStatus.google_ai_status)}</span>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 border rounded-lg">
              <Globe className="h-8 w-8 text-purple-600" />
              <div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus.gitlab_pipeline)}`}></div>
                  <span className="font-medium">GitLab CI/CD</span>
                </div>
                <span className="text-sm text-gray-600">{getStatusText(systemStatus.gitlab_pipeline)}</span>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 border rounded-lg">
              <TrendingUp className="h-8 w-8 text-orange-600" />
              <div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus.vector_search)}`}></div>
                  <span className="font-medium">Vector Search</span>
                </div>
                <span className="text-sm text-gray-600">{getStatusText(systemStatus.vector_search)}</span>
              </div>
            </div>
          </div>

          {/* Enhanced Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.total_processed.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Articles Processed</div>
              <Progress value={75} className="h-1 mt-2" />
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{stats.bias_detected.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Bias Detected</div>
              <Progress value={60} className="h-1 mt-2" />
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{stats.misinformation_flagged.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Misinformation Flagged</div>
              <Progress value={25} className="h-1 mt-2" />
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.high_credibility.toLocaleString()}</div>
              <div className="text-sm text-gray-600">High Credibility</div>
              <Progress value={85} className="h-1 mt-2" />
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.processing_rate}</div>
              <div className="text-sm text-gray-600">Articles/Hour</div>
              <Progress value={90} className="h-1 mt-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Enhanced Activity Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Live Activity Stream</CardTitle>
          <CardDescription>Real-time processing updates, alerts, and system events</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">All Updates</TabsTrigger>
              <TabsTrigger value="processing">Processing</TabsTrigger>
              <TabsTrigger value="alerts">Alerts</TabsTrigger>
              <TabsTrigger value="system">System</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-4">
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {updates.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    {isPaused ? "Feed paused - click Resume to continue" : "Waiting for updates..."}
                  </div>
                ) : (
                  updates.map((update, index) => (
                    <div
                      key={index}
                      className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="mt-1">
                        {update.type === "connection" ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : update.type === "comprehensive_update" ? (
                          <TrendingUp className="h-5 w-5 text-blue-600" />
                        ) : update.type === "alert" ? (
                          <AlertTriangle className="h-5 w-5 text-red-600" />
                        ) : (
                          <Activity className="h-5 w-5 text-purple-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">
                            {update.type === "connection" && "System Connected"}
                            {update.type === "comprehensive_update" && "Processing Update"}
                            {update.type === "alert" && "High Risk Alert"}
                            {update.type === "error" && "System Notice"}
                          </h4>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-gray-500">
                              {new Date(update.timestamp).toLocaleTimeString()}
                            </span>
                            {update.type === "comprehensive_update" && (
                              <Badge variant="outline" className="text-xs">
                                Live
                              </Badge>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {update.message ||
                            (update.type === "comprehensive_update"
                              ? `${update.data?.articles?.length || 0} articles processed`
                              : "System update")}
                        </p>

                        {/* Enhanced update details */}
                        {update.data?.articles && update.data.articles.length > 0 && (
                          <div className="mt-2">
                            <div className="flex flex-wrap gap-1 mb-2">
                              {update.data.articles.slice(0, 3).map((article: any, i: number) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {article.source}
                                </Badge>
                              ))}
                              {update.data.articles.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{update.data.articles.length - 3} more
                                </Badge>
                              )}
                            </div>
                            <div className="text-xs text-gray-500">
                              Latest: "{update.data.articles[0]?.title?.substring(0, 60)}..."
                            </div>
                          </div>
                        )}

                        {/* Alert details */}
                        {update.data?.alerts && update.data.alerts.length > 0 && (
                          <div className="mt-2 p-2 bg-red-50 rounded border-l-4 border-red-400">
                            <div className="text-sm font-medium text-red-800">
                              {update.data.alerts.length} high-risk article(s) detected
                            </div>
                            <div className="text-xs text-red-600 mt-1">
                              {update.data.alerts[0]?.title?.substring(0, 80)}...
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </TabsContent>

            <TabsContent value="processing" className="mt-4">
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {updates
                  .filter((u) => u.type === "comprehensive_update")
                  .map((update, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">Processing Batch</span>
                        <span className="text-xs text-gray-500">{new Date(update.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>Articles: {update.data?.articles?.length || 0}</div>
                        <div>Rate: {update.stats?.processing_rate || 0}/hr</div>
                      </div>
                    </div>
                  ))}
              </div>
            </TabsContent>

            <TabsContent value="alerts" className="mt-4">
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {updates
                  .filter((u) => u.type === "alert")
                  .map((update, index) => (
                    <div key={index} className="p-4 border rounded-lg border-red-200 bg-red-50">
                      <div className="flex items-center space-x-2 mb-2">
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                        <span className="font-medium text-red-800">High Risk Detection</span>
                        <span className="text-xs text-red-600">{new Date(update.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="text-sm text-red-700">
                        {update.data?.alerts?.length || 0} articles flagged for review
                      </div>
                    </div>
                  ))}
              </div>
            </TabsContent>

            <TabsContent value="system" className="mt-4">
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {updates
                  .filter((u) => u.type === "connection" || u.type === "error")
                  .map((update, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        {update.type === "connection" ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        )}
                        <span className="font-medium">System Event</span>
                        <span className="text-xs text-gray-500">{new Date(update.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="text-sm text-gray-700">{update.message}</div>
                    </div>
                  ))}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
