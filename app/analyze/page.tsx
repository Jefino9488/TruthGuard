"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { BrainCircuit, AlertTriangle, CheckCircle, Loader2, LinkIcon, FileText, Globe } from "lucide-react"
import { SentimentAnalysis } from "@/components/sentiment-analysis"
import { FactCheckResults } from "@/components/fact-check-results"
import { BiasBreakdown } from "@/components/bias-breakdown"
import { CredibilityScore } from "@/components/credibility-score"
import { NarrativeAnalysis } from "@/components/narrative-analysis"

export default function AnalyzePage() {
  const [content, setContent] = useState("")
  const [url, setUrl] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [activeTab, setActiveTab] = useState("text")
  const [advancedOptions, setAdvancedOptions] = useState({
    factCheck: true,
    sentimentAnalysis: true,
    narrativeDetection: true,
    sourceCredibility: true,
    biasDetection: true,
  })

  const handleAnalyze = () => {
    if ((activeTab === "text" && !content) || (activeTab === "url" && !url)) return

    setIsAnalyzing(true)
    setAnalysisComplete(false)
    setAnalysisProgress(0)

    // Simulate analysis progress
    const interval = setInterval(() => {
      setAnalysisProgress((prev) => {
        const newProgress = prev + Math.random() * 15
        if (newProgress >= 100) {
          clearInterval(interval)
          setTimeout(() => {
            setIsAnalyzing(false)
            setAnalysisComplete(true)
          }, 500)
          return 100
        }
        return newProgress
      })
    }, 600)
  }

  const handleReset = () => {
    setContent("")
    setUrl("")
    setAnalysisComplete(false)
    setAnalysisProgress(0)
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <BrainCircuit className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold">Content Analyzer</h1>
              <p className="text-sm text-gray-600">Deep analysis of bias, sentiment, and misinformation</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle>Analyze Content</CardTitle>
                <CardDescription>
                  Enter text, paste an article, or provide a URL to analyze for bias and misinformation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="text">Text Input</TabsTrigger>
                    <TabsTrigger value="url">URL</TabsTrigger>
                  </TabsList>
                  <TabsContent value="text" className="space-y-4 mt-4">
                    <Textarea
                      placeholder="Paste article text or enter content to analyze..."
                      className="min-h-[200px]"
                      value={content}
                      onChange={(e) => setContent(e.target.value)}
                      disabled={isAnalyzing}
                    />
                  </TabsContent>
                  <TabsContent value="url" className="space-y-4 mt-4">
                    <div className="flex space-x-2">
                      <Input
                        placeholder="https://example.com/article"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        disabled={isAnalyzing}
                      />
                      <Button variant="outline" size="icon" disabled={isAnalyzing}>
                        <Globe className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="flex items-center space-x-2 text-sm">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-500">Article will be fetched and analyzed</span>
                    </div>
                  </TabsContent>
                </Tabs>

                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-medium">Advanced Options</h3>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="fact-check" className="flex items-center space-x-2 cursor-pointer">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span>Fact Checking</span>
                      </Label>
                      <Switch
                        id="fact-check"
                        checked={advancedOptions.factCheck}
                        onCheckedChange={(checked) => setAdvancedOptions({ ...advancedOptions, factCheck: checked })}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="sentiment" className="flex items-center space-x-2 cursor-pointer">
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        <span>Sentiment Analysis</span>
                      </Label>
                      <Switch
                        id="sentiment"
                        checked={advancedOptions.sentimentAnalysis}
                        onCheckedChange={(checked) =>
                          setAdvancedOptions({ ...advancedOptions, sentimentAnalysis: checked })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="narrative" className="flex items-center space-x-2 cursor-pointer">
                        <BrainCircuit className="h-4 w-4 text-purple-600" />
                        <span>Narrative Detection</span>
                      </Label>
                      <Switch
                        id="narrative"
                        checked={advancedOptions.narrativeDetection}
                        onCheckedChange={(checked) =>
                          setAdvancedOptions({ ...advancedOptions, narrativeDetection: checked })
                        }
                      />
                    </div>
                  </div>
                </div>

                {isAnalyzing && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Analyzing content...</span>
                      <span>{Math.round(analysisProgress)}%</span>
                    </div>
                    <Progress value={analysisProgress} className="h-2" />
                  </div>
                )}

                <div className="flex space-x-3">
                  <Button
                    className="flex-1"
                    onClick={handleAnalyze}
                    disabled={
                      isAnalyzing || (activeTab === "text" && !content.trim()) || (activeTab === "url" && !url.trim())
                    }
                  >
                    {isAnalyzing ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing
                      </>
                    ) : (
                      "Analyze Content"
                    )}
                  </Button>
                  <Button variant="outline" onClick={handleReset} disabled={isAnalyzing}>
                    Reset
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            {!analysisComplete && !isAnalyzing && (
              <div className="h-full flex items-center justify-center text-center p-12">
                <div className="max-w-md">
                  <BrainCircuit className="h-16 w-16 text-blue-600 mx-auto mb-6 opacity-50" />
                  <h2 className="text-2xl font-bold mb-2">Advanced Content Analysis</h2>
                  <p className="text-gray-600 mb-6">
                    Our AI will analyze your content for bias patterns, sentiment, factual accuracy, and narrative
                    framing using state-of-the-art language models.
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    <Badge variant="outline" className="text-blue-600 border-blue-600">
                      Bias Detection
                    </Badge>
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      Fact Checking
                    </Badge>
                    <Badge variant="outline" className="text-purple-600 border-purple-600">
                      Sentiment Analysis
                    </Badge>
                    <Badge variant="outline" className="text-orange-600 border-orange-600">
                      Source Credibility
                    </Badge>
                    <Badge variant="outline" className="text-red-600 border-red-600">
                      Narrative Framing
                    </Badge>
                  </div>
                </div>
              </div>
            )}

            {isAnalyzing && (
              <div className="h-full flex items-center justify-center text-center p-12">
                <div className="max-w-md">
                  <div className="relative mx-auto mb-6">
                    <BrainCircuit className="h-16 w-16 text-blue-600 mx-auto opacity-50" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-24 h-24 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                  </div>
                  <h2 className="text-2xl font-bold mb-2">Analyzing Content</h2>
                  <p className="text-gray-600 mb-6">
                    Our AI models are processing your content. This typically takes 15-30 seconds depending on length
                    and complexity.
                  </p>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                      <span>Extracting key entities</span>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Analyzing sentiment patterns</span>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Detecting bias indicators</span>
                      {analysisProgress > 50 ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                      )}
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Cross-referencing facts</span>
                      {analysisProgress > 75 ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                      )}
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Generating comprehensive report</span>
                      {analysisProgress > 90 ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {analysisComplete && (
              <div className="space-y-8">
                {/* Summary Card */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Analysis Summary</CardTitle>
                        <CardDescription>
                          {activeTab === "text"
                            ? `Analysis of ${content.length} characters of text`
                            : `Analysis of content from ${url}`}
                        </CardDescription>
                      </div>
                      <CredibilityScore score={72} />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                          <h3 className="text-sm font-medium text-gray-500 mb-1">Bias Score</h3>
                          <div className="text-3xl font-bold text-yellow-600">64%</div>
                          <Badge className="mt-2 bg-yellow-100 text-yellow-800">Moderate Bias</Badge>
                        </div>
                        <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                          <h3 className="text-sm font-medium text-gray-500 mb-1">Factual Accuracy</h3>
                          <div className="text-3xl font-bold text-green-600">83%</div>
                          <Badge className="mt-2 bg-green-100 text-green-800">Mostly Accurate</Badge>
                        </div>
                        <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                          <h3 className="text-sm font-medium text-gray-500 mb-1">Sentiment</h3>
                          <div className="text-3xl font-bold text-blue-600">-27%</div>
                          <Badge className="mt-2 bg-blue-100 text-blue-800">Slightly Negative</Badge>
                        </div>
                      </div>

                      <div className="p-4 border rounded-lg bg-amber-50 border-amber-200">
                        <div className="flex items-start space-x-3">
                          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                          <div>
                            <h3 className="font-medium text-amber-800">Analysis Highlights</h3>
                            <ul className="mt-2 space-y-1 text-sm text-amber-800">
                              <li>• Detected emotional language that may influence reader perception</li>
                              <li>• Found 3 claims that require additional verification</li>
                              <li>• Source selection appears to favor one perspective</li>
                              <li>• Narrative framing suggests political leaning</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Detailed Analysis Tabs */}
                <Tabs defaultValue="bias" className="w-full">
                  <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="bias">Bias Analysis</TabsTrigger>
                    <TabsTrigger value="facts">Fact Check</TabsTrigger>
                    <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
                    <TabsTrigger value="narrative">Narrative</TabsTrigger>
                    <TabsTrigger value="sources">Sources</TabsTrigger>
                  </TabsList>

                  <TabsContent value="bias" className="mt-6">
                    <BiasBreakdown />
                  </TabsContent>

                  <TabsContent value="facts" className="mt-6">
                    <FactCheckResults />
                  </TabsContent>

                  <TabsContent value="sentiment" className="mt-6">
                    <SentimentAnalysis />
                  </TabsContent>

                  <TabsContent value="narrative" className="mt-6">
                    <NarrativeAnalysis />
                  </TabsContent>

                  <TabsContent value="sources" className="mt-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Source Analysis</CardTitle>
                        <CardDescription>Evaluation of sources cited and their credibility</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-6">
                          <div className="space-y-4">
                            {[
                              {
                                name: "Example Research Institute",
                                url: "https://example-research.org",
                                credibility: 92,
                                bias: "Minimal",
                              },
                              {
                                name: "News Organization",
                                url: "https://news-example.com",
                                credibility: 78,
                                bias: "Slight Left",
                              },
                              {
                                name: "Political Think Tank",
                                url: "https://policy-institute.org",
                                credibility: 65,
                                bias: "Moderate Right",
                              },
                            ].map((source, index) => (
                              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                                <div>
                                  <div className="flex items-center space-x-2">
                                    <Globe className="h-4 w-4 text-gray-500" />
                                    <h4 className="font-medium">{source.name}</h4>
                                  </div>
                                  <div className="flex items-center space-x-2 mt-1">
                                    <LinkIcon className="h-3 w-3 text-gray-400" />
                                    <span className="text-sm text-gray-600">{source.url}</span>
                                  </div>
                                </div>
                                <div className="flex items-center space-x-4">
                                  <div className="text-right">
                                    <div className="text-sm font-medium">Credibility</div>
                                    <div
                                      className={`text-lg font-bold ${source.credibility > 80 ? "text-green-600" : source.credibility > 60 ? "text-yellow-600" : "text-red-600"}`}
                                    >
                                      {source.credibility}%
                                    </div>
                                  </div>
                                  <Badge
                                    variant="outline"
                                    className={
                                      source.bias === "Minimal"
                                        ? "border-green-600 text-green-600"
                                        : source.bias.includes("Slight")
                                          ? "border-yellow-600 text-yellow-600"
                                          : "border-red-600 text-red-600"
                                    }
                                  >
                                    {source.bias}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>

                          <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
                            <div className="flex items-start space-x-3">
                              <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                              <div>
                                <h3 className="font-medium text-blue-800">Source Diversity</h3>
                                <p className="mt-1 text-sm text-blue-800">
                                  This content cites sources with varying perspectives and credibility levels. Consider
                                  evaluating primary sources directly when possible.
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>

                {/* Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle>Recommended Actions</CardTitle>
                    <CardDescription>Based on our analysis, here are some suggested next steps</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Button className="w-full">
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Verify Key Claims
                      </Button>
                      <Button variant="outline" className="w-full">
                        <Globe className="mr-2 h-4 w-4" />
                        Find Alternative Sources
                      </Button>
                      <Button variant="outline" className="w-full">
                        <FileText className="mr-2 h-4 w-4" />
                        Generate Balanced Summary
                      </Button>
                      <Button variant="outline" className="w-full">
                        <LinkIcon className="mr-2 h-4 w-4" />
                        Share Analysis Report
                      </Button>
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between border-t pt-6">
                    <div className="text-sm text-gray-500">
                      Analysis powered by TruthGuard AI using Gemini and Llama 3 models
                    </div>
                    <Button variant="ghost" size="sm">
                      Export Report
                    </Button>
                  </CardFooter>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
