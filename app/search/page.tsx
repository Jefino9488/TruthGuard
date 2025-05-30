"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, ExternalLink } from "lucide-react"

const mockArticles = [
  {
    id: 1,
    title: "Climate Change Policies Show Mixed Results in Latest Study",
    source: "Reuters",
    bias_score: 0.2,
    misinformation_risk: 0.1,
    topic: "Environment",
    date: "2024-01-15",
    summary:
      "A comprehensive analysis of global climate policies reveals varying effectiveness across different regions and implementation strategies.",
  },
  {
    id: 2,
    title: "Economic Recovery Accelerates Despite Global Challenges",
    source: "Wall Street Journal",
    bias_score: 0.4,
    misinformation_risk: 0.2,
    topic: "Economy",
    date: "2024-01-14",
    summary:
      "Latest economic indicators suggest robust recovery momentum, though experts warn of potential headwinds from international trade tensions.",
  },
  {
    id: 3,
    title: "Healthcare Innovation Breakthrough in AI Diagnostics",
    source: "Nature Medicine",
    bias_score: 0.1,
    misinformation_risk: 0.05,
    topic: "Healthcare",
    date: "2024-01-13",
    summary:
      "Researchers demonstrate significant improvements in diagnostic accuracy using advanced machine learning algorithms for medical imaging.",
  },
  {
    id: 4,
    title: "Political Tensions Rise Over Immigration Reform Proposals",
    source: "Fox News",
    bias_score: 0.8,
    misinformation_risk: 0.6,
    topic: "Politics",
    date: "2024-01-12",
    summary:
      "Congressional debates intensify as lawmakers struggle to find common ground on comprehensive immigration policy changes.",
  },
  {
    id: 5,
    title: "Technology Sector Leads Market Rally Amid AI Optimism",
    source: "Bloomberg",
    bias_score: 0.3,
    misinformation_risk: 0.15,
    topic: "Technology",
    date: "2024-01-11",
    summary:
      "Major tech stocks surge as investors show renewed confidence in artificial intelligence applications across various industries.",
  },
]

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedTopic, setSelectedTopic] = useState("all")
  const [selectedSource, setSelectedSource] = useState("all")
  const [filteredArticles, setFilteredArticles] = useState(mockArticles)

  const handleSearch = () => {
    let filtered = mockArticles

    if (searchQuery) {
      filtered = filtered.filter(
        (article) =>
          article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          article.summary.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    }

    if (selectedTopic !== "all") {
      filtered = filtered.filter((article) => article.topic === selectedTopic)
    }

    if (selectedSource !== "all") {
      filtered = filtered.filter((article) => article.source === selectedSource)
    }

    setFilteredArticles(filtered)
  }

  const getBiasLabel = (score: number) => {
    if (score < 0.3) return { label: "Low Bias", color: "bg-green-100 text-green-800" }
    if (score < 0.6) return { label: "Moderate Bias", color: "bg-yellow-100 text-yellow-800" }
    return { label: "High Bias", color: "bg-red-100 text-red-800" }
  }

  const getRiskLabel = (score: number) => {
    if (score < 0.2) return { label: "Low Risk", color: "bg-green-100 text-green-800" }
    if (score < 0.5) return { label: "Medium Risk", color: "bg-yellow-100 text-yellow-800" }
    return { label: "High Risk", color: "bg-red-100 text-red-800" }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <Search className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold">Article Search</h1>
              <p className="text-sm text-gray-600">Search and analyze articles with AI-powered bias detection</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Search Interface */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Semantic Search</CardTitle>
            <CardDescription>
              Search through millions of articles using MongoDB vector search and AI-powered analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex space-x-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search articles, topics, or bias patterns..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                  />
                </div>
                <Button onClick={handleSearch}>
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </Button>
              </div>
              <div className="flex space-x-4">
                <Select value={selectedTopic} onValueChange={setSelectedTopic}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Select topic" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Topics</SelectItem>
                    <SelectItem value="Politics">Politics</SelectItem>
                    <SelectItem value="Economy">Economy</SelectItem>
                    <SelectItem value="Healthcare">Healthcare</SelectItem>
                    <SelectItem value="Technology">Technology</SelectItem>
                    <SelectItem value="Environment">Environment</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={selectedSource} onValueChange={setSelectedSource}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Select source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sources</SelectItem>
                    <SelectItem value="Reuters">Reuters</SelectItem>
                    <SelectItem value="Wall Street Journal">Wall Street Journal</SelectItem>
                    <SelectItem value="Fox News">Fox News</SelectItem>
                    <SelectItem value="CNN">CNN</SelectItem>
                    <SelectItem value="Bloomberg">Bloomberg</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Search Results */}
        <Tabs defaultValue="articles" className="space-y-6">
          <TabsList>
            <TabsTrigger value="articles">Articles ({filteredArticles.length})</TabsTrigger>
            <TabsTrigger value="patterns">Bias Patterns</TabsTrigger>
            <TabsTrigger value="similar">Similar Content</TabsTrigger>
          </TabsList>

          <TabsContent value="articles" className="space-y-4">
            {filteredArticles.map((article) => {
              const biasInfo = getBiasLabel(article.bias_score)
              const riskInfo = getRiskLabel(article.misinformation_risk)

              return (
                <Card key={article.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-2">{article.title}</CardTitle>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>{article.source}</span>
                          <span>{article.date}</span>
                          <Badge variant="outline">{article.topic}</Badge>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700 mb-4">{article.summary}</p>
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">Bias Score:</span>
                        <Badge className={biasInfo.color}>{biasInfo.label}</Badge>
                        <span className="text-sm text-gray-500">({(article.bias_score * 100).toFixed(1)}%)</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">Risk Level:</span>
                        <Badge className={riskInfo.color}>{riskInfo.label}</Badge>
                        <span className="text-sm text-gray-500">
                          ({(article.misinformation_risk * 100).toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </TabsContent>

          <TabsContent value="patterns" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Detected Bias Patterns</CardTitle>
                <CardDescription>Common bias patterns found in search results</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-medium">Emotional Language</h4>
                      <p className="text-sm text-gray-600">Use of charged emotional terms</p>
                    </div>
                    <Badge className="bg-orange-100 text-orange-800">Found in 3 articles</Badge>
                  </div>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-medium">Source Selection Bias</h4>
                      <p className="text-sm text-gray-600">Limited or one-sided source selection</p>
                    </div>
                    <Badge className="bg-red-100 text-red-800">Found in 2 articles</Badge>
                  </div>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-medium">Statistical Manipulation</h4>
                      <p className="text-sm text-gray-600">Misleading use of statistics</p>
                    </div>
                    <Badge className="bg-yellow-100 text-yellow-800">Found in 1 article</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="similar" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Similar Content Analysis</CardTitle>
                <CardDescription>Articles with similar topics using vector similarity search</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredArticles.slice(0, 3).map((article) => (
                    <div key={article.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h4 className="font-medium">{article.title}</h4>
                        <p className="text-sm text-gray-600">{article.source} • Similarity: 87%</p>
                      </div>
                      <Button variant="outline" size="sm">
                        View
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
