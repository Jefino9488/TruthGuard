import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Shield, TrendingUp, AlertTriangle, CheckCircle, RefreshCw } from "lucide-react"
import { BiasChart } from "@/components/bias-chart"
import { SourceComparison } from "@/components/source-comparison"
import { ThreatLevel } from "@/components/threat-level"
import { RecentArticles } from "@/components/recent-articles"
import { BiasHeatmap } from "@/components/bias-heatmap"

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Shield className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold">TruthGuard Dashboard</h1>
                <p className="text-sm text-gray-600">Real-time bias and misinformation detection</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="text-green-600 border-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                System Online
              </Badge>
              <Button size="sm" variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Articles Processed</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">2,847</div>
              <p className="text-xs text-muted-foreground">+12% from yesterday</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Bias Detected</CardTitle>
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">342</div>
              <p className="text-xs text-muted-foreground">-8% from yesterday</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Misinformation Risk</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">23</div>
              <p className="text-xs text-muted-foreground">+3% from yesterday</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Accuracy Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">94.7%</div>
              <p className="text-xs text-muted-foreground">+0.2% from yesterday</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Dashboard Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="bias-analysis">Bias Analysis</TabsTrigger>
            <TabsTrigger value="sources">Sources</TabsTrigger>
            <TabsTrigger value="real-time">Real-time</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Bias Distribution</CardTitle>
                  <CardDescription>Current bias patterns across all sources</CardDescription>
                </CardHeader>
                <CardContent>
                  <BiasChart />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Threat Assessment</CardTitle>
                  <CardDescription>Real-time misinformation risk levels</CardDescription>
                </CardHeader>
                <CardContent>
                  <ThreatLevel />
                </CardContent>
              </Card>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Recent Analysis</CardTitle>
                <CardDescription>Latest articles processed by the AI system</CardDescription>
              </CardHeader>
              <CardContent>
                <RecentArticles />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="bias-analysis" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Bias Heatmap</CardTitle>
                <CardDescription>Visual representation of bias patterns across topics and sources</CardDescription>
              </CardHeader>
              <CardContent>
                <BiasHeatmap />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sources" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Source Comparison</CardTitle>
                <CardDescription>Bias analysis across different news sources</CardDescription>
              </CardHeader>
              <CardContent>
                <SourceComparison />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="real-time" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Live Feed</CardTitle>
                  <CardDescription>Real-time article processing</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          <div>
                            <p className="font-medium">Processing article #{2847 + i}</p>
                            <p className="text-sm text-gray-600">Source: CNN Politics</p>
                          </div>
                        </div>
                        <Badge variant="outline">Processing</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>System Status</CardTitle>
                  <CardDescription>AI model and pipeline health</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Gemini AI Model</span>
                      <Badge className="bg-green-100 text-green-800">Healthy</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>MongoDB Atlas</span>
                      <Badge className="bg-green-100 text-green-800">Connected</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Vector Search</span>
                      <Badge className="bg-green-100 text-green-800">Operational</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>GitLab CI/CD</span>
                      <Badge className="bg-green-100 text-green-800">Running</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Google Cloud Run</span>
                      <Badge className="bg-green-100 text-green-800">Deployed</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
