"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Bot, User, Send, AlertTriangle, CheckCircle, TrendingUp } from "lucide-react"

interface Message {
  id: number
  type: "user" | "bot"
  content: string
  timestamp: Date
  analysis?: {
    bias_score: number
    misinformation_risk: number
    confidence: number
  }
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: "bot",
      content:
        "Hello! I'm TruthGuard AI, your bias and misinformation detection assistant. You can ask me to analyze headlines, articles, or discuss media bias patterns. How can I help you today?",
      timestamp: new Date(),
    },
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const analyzeText = (text: string) => {
    // Simulate AI analysis
    const biasKeywords = ["shocking", "devastating", "outrageous", "incredible", "unbelievable"]
    const misinfoKeywords = ["scientists say", "studies show", "experts claim", "breaking"]

    let biasScore = 0
    let misinfoRisk = 0

    biasKeywords.forEach((keyword) => {
      if (text.toLowerCase().includes(keyword)) biasScore += 0.2
    })

    misinfoKeywords.forEach((keyword) => {
      if (text.toLowerCase().includes(keyword)) misinfoRisk += 0.15
    })

    return {
      bias_score: Math.min(biasScore, 1),
      misinformation_risk: Math.min(misinfoRisk, 1),
      confidence: 0.85 + Math.random() * 0.1,
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      id: messages.length + 1,
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage("")
    setIsLoading(true)

    // Simulate AI processing
    setTimeout(() => {
      const analysis = analyzeText(inputMessage)

      let botResponse = ""

      if (inputMessage.toLowerCase().includes("analyze") || inputMessage.toLowerCase().includes("headline")) {
        botResponse = `I've analyzed your text for bias and misinformation indicators. Here's what I found:

**Bias Analysis:**
- Bias Score: ${(analysis.bias_score * 100).toFixed(1)}% ${analysis.bias_score > 0.5 ? "(High bias detected)" : "(Low bias)"}
- The text ${analysis.bias_score > 0.3 ? "contains emotional language that may indicate bias" : "appears relatively neutral"}

**Misinformation Risk:**
- Risk Level: ${(analysis.misinformation_risk * 100).toFixed(1)}% ${analysis.misinformation_risk > 0.4 ? "(Requires fact-checking)" : "(Low risk)"}
- ${analysis.misinformation_risk > 0.3 ? "Contains claims that should be verified" : "No obvious misinformation indicators"}

**Confidence:** ${(analysis.confidence * 100).toFixed(1)}%

Would you like me to explain any specific aspects of this analysis?`
      } else if (inputMessage.toLowerCase().includes("bias")) {
        botResponse =
          "Media bias can manifest in several ways: selection bias (what stories are covered), framing bias (how stories are presented), and confirmation bias (favoring information that confirms existing beliefs). I can help you identify these patterns in news articles. Would you like me to analyze a specific headline or article?"
      } else if (inputMessage.toLowerCase().includes("misinformation")) {
        botResponse =
          "Misinformation detection involves analyzing several factors: source credibility, fact-checking against reliable databases, identifying logical fallacies, and detecting emotional manipulation. Our AI model uses advanced NLP techniques to identify these patterns. Do you have a specific claim you'd like me to fact-check?"
      } else {
        botResponse =
          "I can help you analyze text for bias and misinformation. Try asking me to 'analyze this headline' followed by the text you want me to examine, or ask me about bias detection techniques and misinformation patterns."
      }

      const botMessage: Message = {
        id: messages.length + 2,
        type: "bot",
        content: botResponse,
        timestamp: new Date(),
        analysis: inputMessage.toLowerCase().includes("analyze") ? analysis : undefined,
      }

      setMessages((prev) => [...prev, botMessage])
      setIsLoading(false)
    }, 1500)
  }

  const getBiasColor = (score: number) => {
    if (score < 0.3) return "text-green-600"
    if (score < 0.6) return "text-yellow-600"
    return "text-red-600"
  }

  const getRiskColor = (score: number) => {
    if (score < 0.2) return "text-green-600"
    if (score < 0.5) return "text-yellow-600"
    return "text-red-600"
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <Bot className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold">TruthGuard AI Assistant</h1>
              <p className="text-sm text-gray-600">Chat with AI for real-time bias and misinformation analysis</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <Card className="h-[600px] flex flex-col">
              <CardHeader>
                <CardTitle>AI Chat Assistant</CardTitle>
                <CardDescription>
                  Ask me to analyze headlines, articles, or discuss bias detection techniques
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <ScrollArea className="flex-1 pr-4">
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[80%] ${message.type === "user" ? "bg-blue-600 text-white" : "bg-gray-100"} rounded-lg p-4`}
                        >
                          <div className="flex items-center space-x-2 mb-2">
                            {message.type === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                            <span className="text-sm font-medium">
                              {message.type === "user" ? "You" : "TruthGuard AI"}
                            </span>
                            <span className="text-xs opacity-70">{message.timestamp.toLocaleTimeString()}</span>
                          </div>
                          <div className="whitespace-pre-wrap">{message.content}</div>

                          {message.analysis && (
                            <div className="mt-4 p-3 bg-white/10 rounded border">
                              <h4 className="font-medium mb-2">Analysis Results:</h4>
                              <div className="space-y-1 text-sm">
                                <div className={`flex justify-between ${getBiasColor(message.analysis.bias_score)}`}>
                                  <span>Bias Score:</span>
                                  <span>{(message.analysis.bias_score * 100).toFixed(1)}%</span>
                                </div>
                                <div
                                  className={`flex justify-between ${getRiskColor(message.analysis.misinformation_risk)}`}
                                >
                                  <span>Misinfo Risk:</span>
                                  <span>{(message.analysis.misinformation_risk * 100).toFixed(1)}%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Confidence:</span>
                                  <span>{(message.analysis.confidence * 100).toFixed(1)}%</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg p-4">
                          <div className="flex items-center space-x-2">
                            <Bot className="h-4 w-4" />
                            <span className="text-sm font-medium">TruthGuard AI</span>
                          </div>
                          <div className="mt-2 flex space-x-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div
                              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.1s" }}
                            ></div>
                            <div
                              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.2s" }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </ScrollArea>

                <div className="flex space-x-2 mt-4">
                  <Input
                    placeholder="Ask me to analyze a headline or discuss bias patterns..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && !isLoading && handleSendMessage()}
                    disabled={isLoading}
                  />
                  <Button onClick={handleSendMessage} disabled={isLoading || !inputMessage.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setInputMessage("Analyze this headline: ")}
                >
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Analyze Headline
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setInputMessage("What are common bias patterns?")}
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Bias Patterns
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setInputMessage("How do you detect misinformation?")}
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Detection Methods
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">AI Capabilities</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Bias detection</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Misinformation analysis</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Source credibility</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Fact-checking</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Pattern recognition</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Example Queries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <p className="text-gray-600">"Analyze this headline: Breaking news shocks the world"</p>
                  <p className="text-gray-600">"What bias patterns do you detect?"</p>
                  <p className="text-gray-600">"How reliable is this source?"</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
