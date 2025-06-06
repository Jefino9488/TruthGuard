"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, AlertTriangle, CheckCircle } from "lucide-react"

// Interface for the article structure from the API
interface ApiArticle {
  _id: string
  title: string
  source_name?: string // Or whatever the field is named in your API
  published_at: string // Assuming ISO date string
  bias_score?: number
  misinformation_risk?: number
  article_url?: string // For the external link
}

// Interface for the article structure used in the component's rendering
interface RecentArticleDisplay {
  id: string
  title: string
  source: string
  time: string
  biasScore: number // Renamed from bias_score for consistency
  misinfoRisk: number // Renamed from misinformation_risk for consistency
  articleUrl?: string
}

// Helper function to format time difference
const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.round((now.getTime() - date.getTime()) / 1000)
  const minutes = Math.round(seconds / 60)
  const hours = Math.round(minutes / 60)
  const days = Math.round(hours / 24)

  if (seconds < 60) return `${seconds} seconds ago`
  if (minutes < 60) return `${minutes} minutes ago`
  if (hours < 24) return `${hours} hours ago`
  return `${days} days ago`
}

export function RecentArticles() {
  const [articles, setArticles] = useState<RecentArticleDisplay[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchArticles = async () => {
      setIsLoading(true)
      try {
        const response = await fetch("/api/mongodb")
        if (!response.ok) {
          throw new Error(`Failed to fetch articles: ${response.statusText}`)
        }
        const data = await response.json()
        const apiArticles: ApiArticle[] = data.articles || []

        const transformedArticles: RecentArticleDisplay[] = apiArticles.map(article => ({
          id: article._id,
          title: article.title || "No title available",
          source: article.source_name || "Unknown source",
          time: formatTimeAgo(article.published_at),
          biasScore: article.bias_score || 0,
          misinfoRisk: article.misinformation_risk || 0,
          articleUrl: article.article_url,
        }));
        setArticles(transformedArticles)
      } catch (err) {
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchArticles()
  }, [])

  const getBiasColor = (score: number) => {
    if (score < 0.3) return "bg-green-100 text-green-800"
    if (score < 0.6) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  const getRiskColor = (score: number) => {
    if (score < 0.2) return "bg-green-100 text-green-800"
    if (score < 0.5) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  const getBiasLabel = (score: number) => {
    if (score < 0.3) return "Low"
    if (score < 0.6) return "Moderate"
    return "High"
  }

  const getRiskLabel = (score: number) => {
    if (score < 0.2) return "Low"
    if (score < 0.5) return "Medium"
    return "High"
  }

  if (isLoading) return <p>Loading recent articles...</p>
  if (error) return <p className="text-red-500">Error: {error}</p>
  if (articles.length === 0) return <p>No recent articles found.</p>

  return (
    <div className="space-y-4">
      {articles.map((article) => (
        <div key={article.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
          <div className="flex-1 min-w-0"> {/* Added min-w-0 for better truncation if needed */}
            <h4 className="font-medium mb-1 truncate" title={article.title}>{article.title}</h4>
            <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
              <span className="truncate" title={article.source}>{article.source}</span>
              <span>{article.time}</span>
              <div className="flex items-center space-x-2">
                <Badge className={getBiasColor(article.biasScore)}>Bias: {getBiasLabel(article.biasScore)}</Badge>
                <Badge className={getRiskColor(article.misinfoRisk)}>
                  Risk: {getRiskLabel(article.misinfoRisk)}
                </Badge>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2 ml-4"> {/* Added ml-4 for spacing */}
            {article.misinfoRisk > 0.5 ? (
              <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
            )}
            <Button
              variant="ghost"
              size="sm"
              asChild={!!article.articleUrl} // Use asChild if articleUrl exists
              disabled={!article.articleUrl}
            >
              {article.articleUrl ? (
                <a href={article.articleUrl} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4" />
                </a>
              ) : (
                <ExternalLink className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}
