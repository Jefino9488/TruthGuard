"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DateRangePicker } from "@/components/date-range-picker"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Filter, Download, Share2 } from "lucide-react"
import { BiasTimeline } from "@/components/bias-timeline"
import { TopicCluster } from "@/components/topic-cluster"
import { SourceComparisonMatrix } from "@/components/source-comparison-matrix"
import { NarrativeFlow } from "@/components/narrative-flow"
import { MediaBubbleChart } from "@/components/media-bubble-chart"

export default function TrendsPage() {
  const [dateRange, setDateRange] = useState({
    from: new Date(2024, 0, 1),
    to: new Date(),
  })
  const [selectedTopic, setSelectedTopic] = useState("politics")

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold">Trend Analysis</h1>
              <p className="text-sm text-gray-600">Track bias patterns and misinformation trends over time</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Filters */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle>Media Bias Trends</CardTitle>
                <CardDescription>Analyze how bias and misinformation evolve over time</CardDescription>
              </div>
              <div className="flex items-center space-x-2 mt-4 md:mt-0">
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
                <Button variant="outline" size="sm">
                  <Share2 className="h-4 w-4 mr-2" />
                  Share
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Date Range</label>
                <DateRangePicker dateRange={dateRange} setDateRange={setDateRange} />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Topic</label>
                <Select value={selectedTopic} onValueChange={setSelectedTopic}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select topic" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="politics">Politics</SelectItem>
                    <SelectItem value="climate">Climate Change</SelectItem>
                    <SelectItem value="economy">Economy</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="technology">Technology</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Sources</label>
                <Button variant="outline" className="w-full justify-start">
                  <Filter className="h-4 w-4 mr-2" />
                  All Sources
                  <Badge className="ml-2" variant="secondary">
                    12
                  </Badge>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Key Insights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Bias Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold text-blue-600">+12%</div>
                  <p className="text-sm text-gray-600">Increase in left-leaning bias</p>
                </div>
                <TrendingUp className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Emerging Narrative</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-lg font-bold text-purple-600">Economic Policy Impact</div>
                  <p className="text-sm text-gray-600">Gaining traction across sources</p>
                </div>
                <Badge className="bg-purple-100 text-purple-800">New</Badge>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Misinformation Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold text-red-600">High</div>
                  <p className="text-sm text-gray-600">3 active misinformation campaigns</p>
                </div>
                <Badge className="bg-red-100 text-red-800">Alert</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="timeline" className="space-y-8">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="topics">Topic Clusters</TabsTrigger>
            <TabsTrigger value="sources">Source Matrix</TabsTrigger>
            <TabsTrigger value="narratives">Narrative Flow</TabsTrigger>
            <TabsTrigger value="landscape">Media Landscape</TabsTrigger>
          </TabsList>

          <TabsContent value="timeline">
            <Card>
              <CardHeader>
                <CardTitle>Bias Timeline</CardTitle>
                <CardDescription>
                  Track how bias levels have changed over time across different media sources
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <BiasTimeline />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="topics">
            <Card>
              <CardHeader>
                <CardTitle>Topic Clusters</CardTitle>
                <CardDescription>
                  Visualization of related topics and how they connect across the media landscape
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <TopicCluster />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sources">
            <Card>
              <CardHeader>
                <CardTitle>Source Comparison Matrix</CardTitle>
                <CardDescription>
                  Compare how different sources cover the same topics with varying perspectives
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <SourceComparisonMatrix />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="narratives">
            <Card>
              <CardHeader>
                <CardTitle>Narrative Flow Analysis</CardTitle>
                <CardDescription>
                  Track how narratives evolve and spread across different media sources over time
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <NarrativeFlow />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="landscape">
            <Card>
              <CardHeader>
                <CardTitle>Media Landscape Visualization</CardTitle>
                <CardDescription>
                  Interactive visualization of the media ecosystem showing bias and influence
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <MediaBubbleChart />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Insights and Predictions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Key Insights</CardTitle>
              <CardDescription>AI-generated analysis of current trends</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2 flex items-center">
                    <Badge className="mr-2 bg-blue-100 text-blue-800">Insight</Badge>
                    Polarization Increasing
                  </h3>
                  <p className="text-sm text-gray-600">
                    Analysis shows a 23% increase in polarized coverage of political topics over the last 30 days, with
                    fewer neutral perspectives being represented in mainstream media.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2 flex items-center">
                    <Badge className="mr-2 bg-blue-100 text-blue-800">Insight</Badge>
                    Narrative Shift
                  </h3>
                  <p className="text-sm text-gray-600">
                    Economic policy coverage has shifted from focusing on inflation to employment statistics, with a
                    notable change in framing across multiple sources beginning on March 15th.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2 flex items-center">
                    <Badge className="mr-2 bg-blue-100 text-blue-800">Insight</Badge>
                    Source Behavior Change
                  </h3>
                  <p className="text-sm text-gray-600">
                    Three previously moderate sources have shown significant shifts toward more biased coverage,
                    particularly on healthcare and immigration topics.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Predictions</CardTitle>
              <CardDescription>AI-generated forecasts based on current trends</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2 flex items-center">
                    <Badge className="mr-2 bg-purple-100 text-purple-800">Prediction</Badge>
                    Emerging Narrative
                  </h3>
                  <p className="text-sm text-gray-600">
                    Our models predict that coverage of climate policy will increase by approximately 40% in the next
                    two weeks, with a strong polarization pattern emerging.
                  </p>
                  <div className="mt-2 flex items-center">
                    <span className="text-xs text-gray-500 mr-2">Confidence:</span>
                    <div className="h-2 w-24 bg-gray-200 rounded-full">
                      <div className="h-2 w-[75%] bg-purple-600 rounded-full"></div>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">75%</span>
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2 flex items-center">
                    <Badge className="mr-2 bg-purple-100 text-purple-800">Prediction</Badge>
                    Misinformation Risk
                  </h3>
                  <p className="text-sm text-gray-600">
                    Based on current patterns, we predict a high risk of misinformation campaigns related to upcoming
                    economic data releases, particularly focusing on employment statistics.
                  </p>
                  <div className="mt-2 flex items-center">
                    <span className="text-xs text-gray-500 mr-2">Confidence:</span>
                    <div className="h-2 w-24 bg-gray-200 rounded-full">
                      <div className="h-2 w-[82%] bg-purple-600 rounded-full"></div>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">82%</span>
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2 flex items-center">
                    <Badge className="mr-2 bg-purple-100 text-purple-800">Prediction</Badge>
                    Source Convergence
                  </h3>
                  <p className="text-sm text-gray-600">
                    Our trend analysis suggests that previously divergent sources will begin converging on similar
                    narratives about technology regulation within the next 30 days.
                  </p>
                  <div className="mt-2 flex items-center">
                    <span className="text-xs text-gray-500 mr-2">Confidence:</span>
                    <div className="h-2 w-24 bg-gray-200 rounded-full">
                      <div className="h-2 w-[68%] bg-purple-600 rounded-full"></div>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">68%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
