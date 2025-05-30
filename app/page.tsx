import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Shield, Search, BarChart3, Globe, BrainCircuit } from "lucide-react"
import Link from "next/link"
import { BiasChart } from "@/components/bias-chart"
import { RecentArticles } from "@/components/recent-articles"
import { ThreatLevel } from "@/components/threat-level"
import { TrendingTopics } from "@/components/trending-topics"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">TruthGuard</h1>
              <Badge variant="secondary" className="ml-2">
                AI-Powered
              </Badge>
            </div>
            <nav className="hidden md:flex items-center space-x-6">
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                Dashboard
              </Link>
              <Link href="/search" className="text-gray-600 hover:text-gray-900">
                Search
              </Link>
              <Link href="/chat" className="text-gray-600 hover:text-gray-900">
                AI Assistant
              </Link>
              <Link href="/analyze" className="text-gray-600 hover:text-gray-900">
                Analyzer
              </Link>
              <Link href="/trends" className="text-gray-600 hover:text-gray-900">
                Trends
              </Link>
              <Button>Get Started</Button>
            </nav>
            <Button variant="outline" size="icon" className="md:hidden">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-6 w-6"
              >
                <line x1="4" x2="20" y1="12" y2="12" />
                <line x1="4" x2="20" y1="6" y2="6" />
                <line x1="4" x2="20" y1="18" y2="18" />
              </svg>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <div className="inline-block mb-6">
            <Badge variant="outline" className="px-3 py-1 text-blue-600 border-blue-600">
              Hackathon Winner 2024
            </Badge>
          </div>
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Combat Misinformation with <span className="text-blue-600">AI-Powered Detection</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Real-time media bias detection and misinformation analysis using advanced AI models, MongoDB vector search,
            and automated CI/CD pipelines.
          </p>
          <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <Button size="lg" asChild>
              <Link href="/dashboard">
                <TrendingUp className="mr-2 h-5 w-5" />
                View Dashboard
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/analyze">
                <BrainCircuit className="mr-2 h-5 w-5" />
                Analyze Content
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <Card>
              <CardHeader className="text-center">
                <CardTitle className="text-3xl font-bold text-blue-600">2.4M+</CardTitle>
                <CardDescription>Articles Analyzed</CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="text-center">
                <CardTitle className="text-3xl font-bold text-green-600">94.7%</CardTitle>
                <CardDescription>Accuracy Rate</CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="text-center">
                <CardTitle className="text-3xl font-bold text-orange-600">15,000+</CardTitle>
                <CardDescription>Bias Patterns Detected</CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="text-center">
                <CardTitle className="text-3xl font-bold text-purple-600">Real-time</CardTitle>
                <CardDescription>Detection Speed</CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h3 className="text-3xl font-bold text-center mb-12">Advanced Platform Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <BrainCircuit className="h-10 w-10 text-blue-600 mb-4" />
                <CardTitle>AI-Powered Analysis</CardTitle>
                <CardDescription>
                  Fine-tuned Gemini/Llama 3 models detect subtle bias patterns and misinformation signals
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <BarChart3 className="h-10 w-10 text-green-600 mb-4" />
                <CardTitle>Real-time Visualization</CardTitle>
                <CardDescription>
                  Interactive heatmaps, sentiment analysis, and topic clustering with live updates
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Globe className="h-10 w-10 text-purple-600 mb-4" />
                <CardTitle>Cross-Platform Monitoring</CardTitle>
                <CardDescription>
                  Track bias across news sites, social media, and video platforms with unified analysis
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Trending Topics */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h3 className="text-3xl font-bold text-center mb-12">Trending Topics & Bias Analysis</h3>
          <TrendingTopics />
        </div>
      </section>

      {/* Live Dashboard Preview */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h3 className="text-3xl font-bold text-center mb-12">Live Dashboard Preview</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card>
              <CardHeader>
                <CardTitle>Bias Distribution</CardTitle>
                <CardDescription>Current media bias across major sources</CardDescription>
              </CardHeader>
              <CardContent>
                <BiasChart />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Threat Level</CardTitle>
                <CardDescription>Real-time misinformation risk assessment</CardDescription>
              </CardHeader>
              <CardContent>
                <ThreatLevel />
              </CardContent>
            </Card>
          </div>
          <div className="mt-8">
            <Card>
              <CardHeader>
                <CardTitle>Recent Analysis</CardTitle>
                <CardDescription>Latest articles processed by our AI system</CardDescription>
              </CardHeader>
              <CardContent>
                <RecentArticles />
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h3 className="text-3xl font-bold mb-6">Ready to Combat Misinformation?</h3>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Join the fight against fake news and media bias with our cutting-edge AI platform.
          </p>
          <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/dashboard">
                <Shield className="mr-2 h-5 w-5" />
                Launch Dashboard
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="bg-transparent text-white border-white hover:bg-white/10"
              asChild
            >
              <Link href="/analyze">
                <Search className="mr-2 h-5 w-5" />
                Try Analyzer
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="h-6 w-6" />
                <span className="text-xl font-bold">TruthGuard</span>
              </div>
              <p className="text-gray-400">
                AI-powered platform for detecting media bias and misinformation in real-time.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Platform</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <Link href="/dashboard">Dashboard</Link>
                </li>
                <li>
                  <Link href="/search">Search</Link>
                </li>
                <li>
                  <Link href="/chat">AI Assistant</Link>
                </li>
                <li>
                  <Link href="/analyze">Content Analyzer</Link>
                </li>
                <li>
                  <Link href="/trends">Trend Analysis</Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Technology</h4>
              <ul className="space-y-2 text-gray-400">
                <li>MongoDB Atlas</li>
                <li>Google Cloud AI</li>
                <li>GitLab CI/CD</li>
                <li>Next.js</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <p className="text-gray-400">Built for fighting misinformation with cutting-edge AI technology.</p>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 TruthGuard. Powered by AI for a more truthful world.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
