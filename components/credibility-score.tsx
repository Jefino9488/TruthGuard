"use client"

import { CircularProgressbar, buildStyles } from "react-circular-progressbar"
import "react-circular-progressbar/dist/styles.css"

interface CredibilityScoreProps {
  score: number
}

export function CredibilityScore({ score }: CredibilityScoreProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "#10b981" // green
    if (score >= 60) return "#f59e0b" // yellow
    return "#ef4444" // red
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return "High"
    if (score >= 60) return "Moderate"
    return "Low"
  }

  return (
    <div className="flex items-center space-x-2">
      <div className="w-16 h-16">
        <CircularProgressbar
          value={score}
          text={`${score}`}
          styles={buildStyles({
            textSize: "32px",
            pathColor: getScoreColor(score),
            textColor: getScoreColor(score),
            trailColor: "#e5e7eb",
          })}
        />
      </div>
      <div className="text-sm">
        <div className="font-medium">Credibility</div>
        <div className="text-gray-500">{getScoreLabel(score)}</div>
      </div>
    </div>
  )
}
