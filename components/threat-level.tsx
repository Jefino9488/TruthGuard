import { AlertTriangle, CheckCircle, Shield } from "lucide-react"
import { Progress } from "@/components/ui/progress"

export function ThreatLevel() {
  const currentThreat = 35 // Current threat level percentage

  const getThreatColor = (level: number) => {
    if (level < 30) return "text-green-600"
    if (level < 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getThreatIcon = (level: number) => {
    if (level < 30) return <CheckCircle className="h-8 w-8 text-green-600" />
    if (level < 60) return <Shield className="h-8 w-8 text-yellow-600" />
    return <AlertTriangle className="h-8 w-8 text-red-600" />
  }

  const getThreatLabel = (level: number) => {
    if (level < 30) return "Low Risk"
    if (level < 60) return "Moderate Risk"
    return "High Risk"
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        {getThreatIcon(currentThreat)}
        <h3 className={`text-2xl font-bold mt-2 ${getThreatColor(currentThreat)}`}>{getThreatLabel(currentThreat)}</h3>
        <p className="text-gray-600">Current misinformation threat level</p>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Threat Level</span>
          <span className={getThreatColor(currentThreat)}>{currentThreat}%</span>
        </div>
        <Progress value={currentThreat} className="h-2" />
      </div>

      <div className="space-y-3 text-sm">
        <div className="flex items-center justify-between">
          <span>Active Monitoring</span>
          <CheckCircle className="h-4 w-4 text-green-600" />
        </div>
        <div className="flex items-center justify-between">
          <span>AI Models Online</span>
          <CheckCircle className="h-4 w-4 text-green-600" />
        </div>
        <div className="flex items-center justify-between">
          <span>Vector Search Active</span>
          <CheckCircle className="h-4 w-4 text-green-600" />
        </div>
      </div>
    </div>
  )
}
