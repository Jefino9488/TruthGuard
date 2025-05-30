"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Info, MessageCircle, Users, TrendingUp } from "lucide-react"

const narrativeFrames = [
  {
    name: "Economic Impact",
    strength: 72,
    description: "Frames the issue primarily in terms of economic consequences",
    examples: [
      "focuses on financial implications",
      "emphasizes cost-benefit analysis",
      "highlights economic winners and losers",
    ],
  },
  {
    name: "Political Conflict",
    strength: 58,
    description: "Presents the issue as a partisan or ideological battle",
    examples: [
      "pits opposing political sides against each other",
      "emphasizes partisan divisions",
      "uses political labels",
    ],
  },
  {
    name: "Moral Judgment",
    strength: 45,
    description: "Frames the issue in terms of right vs. wrong or ethical considerations",
    examples: ["appeals to moral principles", "uses value-laden language", "invokes ethical standards"],
  },
  {
    name: "Scientific/Technical",
    strength: 32,
    description: "Presents the issue primarily through scientific or technical lens",
    examples: ["relies on expert opinions", "cites research findings", "uses technical terminology"],
  },
]

const keyActors = [
  {
    name: "Government Officials",
    portrayal: "negative",
    frequency: 8,
    examples: ["described as ineffective", "portrayed as self-interested", "actions questioned"],
  },
  {
    name: "Industry Representatives",
    portrayal: "neutral",
    frequency: 5,
    examples: ["presented factually", "mixed portrayal", "balanced representation"],
  },
  {
    name: "Experts/Academics",
    portrayal: "positive",
    frequency: 6,
    examples: ["cited as authoritative", "portrayed as objective", "given credibility"],
  },
  {
    name: "Affected Citizens",
    portrayal: "sympathetic",
    frequency: 4,
    examples: ["portrayed as victims", "personal stories highlighted", "emotional appeals"],
  },
]

const narrativePatterns = [
  {
    pattern: "Problem-Solution",
    description: "Presents an issue as a problem with a specific solution",
    strength: 65,
  },
  {
    pattern: "Conflict Narrative",
    description: "Structures content around opposing sides in conflict",
    strength: 78,
  },
  {
    pattern: "Status Quo Challenge",
    description: "Positions the issue as challenging established norms",
    strength: 52,
  },
  {
    pattern: "Appeal to Fear",
    description: "Uses potential negative consequences to drive narrative",
    strength: 48,
  },
]

export function NarrativeAnalysis() {
  const getPortrayalColor = (portrayal: string) => {
    switch (portrayal) {
      case "positive":
        return "bg-green-100 text-green-800"
      case "negative":
        return "bg-red-100 text-red-800"
      case "sympathetic":
        return "bg-blue-100 text-blue-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getStrengthColor = (strength: number) => {
    if (strength < 40) return "text-green-600"
    if (strength < 70) return "text-yellow-600"
    return "text-red-600"
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Narrative Analysis</CardTitle>
          <CardDescription>How the content frames issues and constructs narratives</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Dominant Narrative Frames */}
          <div>
            <h3 className="text-sm font-medium mb-4">Dominant Narrative Frames</h3>
            <div className="space-y-4">
              {narrativeFrames.map((frame) => (
                <div key={frame.name} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-medium">{frame.name}</h4>
                      <p className="text-sm text-gray-600">{frame.description}</p>
                    </div>
                    <span className={`font-bold ${getStrengthColor(frame.strength)}`}>{frame.strength}%</span>
                  </div>
                  <Progress value={frame.strength} className="h-2" />
                  <div className="pt-1">
                    <p className="text-xs text-gray-500">Examples: {frame.examples.join("; ")}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Narrative Patterns and Actors */}
          <Tabs defaultValue="patterns" className="mt-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="patterns">
                <TrendingUp className="h-4 w-4 mr-2" />
                Narrative Patterns
              </TabsTrigger>
              <TabsTrigger value="actors">
                <Users className="h-4 w-4 mr-2" />
                Key Actors
              </TabsTrigger>
            </TabsList>

            <TabsContent value="patterns" className="mt-4">
              <div className="space-y-4">
                {narrativePatterns.map((pattern) => (
                  <div key={pattern.pattern} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">{pattern.pattern}</h4>
                      <Badge
                        className={
                          pattern.strength > 70
                            ? "bg-red-100 text-red-800"
                            : pattern.strength > 50
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-green-100 text-green-800"
                        }
                      >
                        {pattern.strength}% Strength
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600">{pattern.description}</p>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="actors" className="mt-4">
              <div className="space-y-4">
                {keyActors.map((actor) => (
                  <div key={actor.name} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">{actor.name}</h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-500">Mentioned {actor.frequency} times</span>
                        <Badge className={getPortrayalColor(actor.portrayal)}>
                          {actor.portrayal.charAt(0).toUpperCase() + actor.portrayal.slice(1)} Portrayal
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">Examples: {actor.examples.join("; ")}</p>
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>

          {/* Narrative Impact */}
          <div className="p-4 border rounded-lg bg-amber-50 border-amber-200">
            <div className="flex items-start space-x-3">
              <MessageCircle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-amber-800">Narrative Impact</h3>
                <p className="mt-1 text-sm text-amber-800">
                  This content primarily uses an economic impact frame with elements of political conflict. The
                  narrative structure emphasizes problems and conflicts, potentially leading readers to view the issue
                  through a partisan lens rather than considering multiple perspectives.
                </p>
              </div>
            </div>
          </div>

          {/* Methodology Note */}
          <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
            <div className="flex items-start space-x-3">
              <Info className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-blue-800">Narrative Analysis Methodology</h3>
                <p className="mt-1 text-sm text-blue-800">
                  Our AI identifies narrative frames, actor portrayals, and storytelling patterns using advanced NLP
                  techniques. This analysis helps reveal how information is structured to influence reader perception
                  beyond simple bias detection.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
