"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, XCircle, AlertTriangle, ExternalLink, Info } from "lucide-react"

const factChecks = [
  {
    claim: "Global temperatures have risen by 2°C in the last decade.",
    verdict: "False",
    confidence: 92,
    explanation:
      "According to NASA and NOAA data, global temperatures have risen by approximately 0.18°C per decade since 1981, not 2°C in the last decade.",
    sources: ["NASA Global Climate Change", "NOAA Climate.gov"],
  },
  {
    claim: "The policy resulted in a 15% decrease in unemployment.",
    verdict: "Misleading",
    confidence: 87,
    explanation:
      "While unemployment did decrease by 15% in certain regions, the national average decrease was only 3%. The claim cherry-picks data from specific areas.",
    sources: ["Bureau of Labor Statistics", "Economic Policy Institute"],
  },
  {
    claim: "The study involved 5,000 participants across 12 countries.",
    verdict: "True",
    confidence: 95,
    explanation:
      "The referenced study did indeed include 5,000 participants from 12 different countries, as verified from the published research paper.",
    sources: ["Journal of Medical Research", "Study Authors' Data"],
  },
  {
    claim: "This technology has been approved by regulatory agencies worldwide.",
    verdict: "Partially True",
    confidence: 78,
    explanation:
      "The technology has been approved in some countries (US, EU, Japan) but is still pending approval in many others. The claim overstates the extent of regulatory approval.",
    sources: ["FDA Database", "European Medicines Agency", "International Regulatory Index"],
  },
]

export function FactCheckResults() {
  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case "True":
        return "bg-green-100 text-green-800"
      case "Partially True":
        return "bg-yellow-100 text-yellow-800"
      case "Misleading":
        return "bg-orange-100 text-orange-800"
      case "False":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getVerdictIcon = (verdict: string) => {
    switch (verdict) {
      case "True":
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case "Partially True":
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />
      case "Misleading":
        return <AlertTriangle className="h-5 w-5 text-orange-600" />
      case "False":
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <Info className="h-5 w-5 text-gray-600" />
    }
  }

  // Calculate overall accuracy
  const totalClaims = factChecks.length
  const trueClaims = factChecks.filter((check) => check.verdict === "True").length
  const partiallyTrueClaims = factChecks.filter((check) => check.verdict === "Partially True").length
  const accuracyScore = Math.round(((trueClaims + partiallyTrueClaims * 0.5) / totalClaims) * 100)

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Fact Check Results</CardTitle>
          <CardDescription>Verification of key claims against reliable sources</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Accuracy */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Overall Factual Accuracy</h3>
              <div className="text-3xl font-bold text-blue-600">{accuracyScore}%</div>
              <div className="text-sm text-gray-500">
                {totalClaims} claims analyzed • {trueClaims} verified true
              </div>
            </div>
            <div className="mt-4 md:mt-0 md:w-64">
              <Progress value={accuracyScore} className="h-2" />
              <div className="flex justify-between text-xs mt-1">
                <span>Low Accuracy</span>
                <span>High Accuracy</span>
              </div>
            </div>
          </div>

          {/* Individual Claims */}
          <div className="space-y-4">
            {factChecks.map((check, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-start space-x-4">
                    <div className="mt-1">{getVerdictIcon(check.verdict)}</div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">Claim:</h4>
                        <Badge className={getVerdictColor(check.verdict)}>{check.verdict}</Badge>
                      </div>
                      <p className="text-gray-800 mb-3">"{check.claim}"</p>
                      <div className="mb-3">
                        <h4 className="text-sm font-medium mb-1">Fact Check:</h4>
                        <p className="text-sm text-gray-600">{check.explanation}</p>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1 text-xs text-gray-500">
                          <span>Confidence:</span>
                          <span className="font-medium">{check.confidence}%</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {check.sources.map((source, i) => (
                            <Button key={i} variant="ghost" size="sm" className="h-7 text-xs">
                              <ExternalLink className="h-3 w-3 mr-1" />
                              {source}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Methodology Note */}
          <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
            <div className="flex items-start space-x-3">
              <Info className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-blue-800">Fact-Checking Methodology</h3>
                <p className="mt-1 text-sm text-blue-800">
                  Claims are verified against multiple authoritative sources using our AI-powered cross-referencing
                  system. Each claim is evaluated for context, accuracy, and potential omissions.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
