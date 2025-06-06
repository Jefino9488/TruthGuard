import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, Database, Cpu, Globe } from "lucide-react"
import { EnhancedRealTimeFeed } from "@/components/enhanced-real-time-feed"
import { useEffect, useState } from "react"

export default function RealTimePage() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchArticles() {
      setLoading(true)
      const res = await fetch("/api/mongodb")
      const data = await res.json()
      setArticles(data.articles || [])
      setLoading(false)
    }
    fetchArticles()
    // Optionally, poll every 30s for real-time updates
    const interval = setInterval(fetchArticles, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <Activity className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold">Real-Time Processing</h1>
              <p className="text-sm text-gray-600">Live AI-powered bias and misinformation detection</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* System Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">MongoDB Atlas</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm">Connected</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">Vector search active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Google Cloud AI</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm">Operational</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">Gemini 1.5 Pro active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">GitLab CI/CD</CardTitle>
              <Globe className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm">Running</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">Auto-deployment active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Processing Rate</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">847</div>
              <p className="text-xs text-muted-foreground">articles/hour</p>
            </CardContent>
          </Card>
        </div>

        {/* Real-Time Feed */}
        <EnhancedRealTimeFeed articles={articles} loading={loading} />

        {/* Technical Architecture */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Technical Architecture</CardTitle>
            <CardDescription>How TruthGuard processes information in real-time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-6 border rounded-lg">
                <Database className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                <h3 className="font-bold mb-2">MongoDB Atlas</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Vector search for semantic similarity, real-time article storage, and change streams for live updates.
                </p>
                <div className="flex flex-wrap justify-center gap-1">
                  <Badge variant="outline">Vector Search</Badge>
                  <Badge variant="outline">Change Streams</Badge>
                  <Badge variant="outline">Atlas Search</Badge>
                </div>
              </div>

              <div className="text-center p-6 border rounded-lg">
                <Cpu className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-bold mb-2">Google Cloud AI</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Gemini 1.5 Pro for bias detection, sentiment analysis, and fact-checking with real-time processing.
                </p>
                <div className="flex flex-wrap justify-center gap-1">
                  <Badge variant="outline">Gemini 1.5 Pro</Badge>
                  <Badge variant="outline">Vertex AI</Badge>
                  <Badge variant="outline">Cloud Run</Badge>
                </div>
              </div>

              <div className="text-center p-6 border rounded-lg">
                <Globe className="h-12 w-12 text-purple-600 mx-auto mb-4" />
                <h3 className="font-bold mb-2">GitLab CI/CD</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Automated scraping, model training, and deployment pipeline with continuous integration.
                </p>
                <div className="flex flex-wrap justify-center gap-1">
                  <Badge variant="outline">Auto Deploy</Badge>
                  <Badge variant="outline">CI/CD Pipeline</Badge>
                  <Badge variant="outline">GitLab Runner</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
