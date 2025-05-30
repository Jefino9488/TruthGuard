import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, AlertTriangle, CheckCircle } from "lucide-react"

const recentArticles = [
  {
    id: 1,
    title: "Economic Recovery Shows Strong Momentum in Q4",
    source: "Reuters",
    bias_score: 0.2,
    misinformation_risk: 0.1,
    time: "2 minutes ago",
  },
  {
    id: 2,
    title: "SHOCKING: Climate Scientists Hide Truth About Global Warming",
    source: "NewsMax",
    bias_score: 0.9,
    misinformation_risk: 0.8,
    time: "5 minutes ago",
  },
  {
    id: 3,
    title: "Healthcare Innovation Breakthrough in AI Diagnostics",
    source: "Nature Medicine",
    bias_score: 0.1,
    misinformation_risk: 0.05,
    time: "8 minutes ago",
  },
  {
    id: 4,
    title: "Political Tensions Rise Over Immigration Proposals",
    source: "Associated Press",
    bias_score: 0.3,
    misinformation_risk: 0.2,
    time: "12 minutes ago",
  },
]

export function RecentArticles() {
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

  return (
    <div className="space-y-4">
      {recentArticles.map((article) => (
        <div key={article.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
          <div className="flex-1">
            <h4 className="font-medium mb-1">{article.title}</h4>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>{article.source}</span>
              <span>{article.time}</span>
              <div className="flex items-center space-x-2">
                <Badge className={getBiasColor(article.bias_score)}>Bias: {getBiasLabel(article.bias_score)}</Badge>
                <Badge className={getRiskColor(article.misinformation_risk)}>
                  Risk: {getRiskLabel(article.misinformation_risk)}
                </Badge>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {article.misinformation_risk > 0.5 ? (
              <AlertTriangle className="h-5 w-5 text-red-500" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-500" />
            )}
            <Button variant="ghost" size="sm">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}
