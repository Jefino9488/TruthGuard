import { type NextRequest, NextResponse } from "next/server"
import { GoogleGenerativeAI } from "@google/generative-ai"

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_API_KEY || "")

export async function POST(request: NextRequest) {
  try {
    const { content, options = {} } = await request.json()

    if (!content) {
      return NextResponse.json({ error: "Content is required" }, { status: 400 })
    }

    // Initialize Gemini model for comprehensive analysis
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" })

    // Enhanced analysis prompt for hackathon requirements
    const prompt = `
    You are TruthGuard AI, an advanced media bias and misinformation detection system. 
    Analyze the following content comprehensively and provide a detailed JSON response.
    
    Your analysis should include:
    1. Bias detection across multiple dimensions
    2. Misinformation risk assessment with specific fact-checks
    3. Sentiment analysis with emotional tone mapping
    4. Narrative framing analysis
    5. Source credibility assessment
    6. Confidence scores for all assessments
    
    Provide response in this exact JSON structure:
    
    {
      "bias_analysis": {
        "overall_score": 0.0-1.0,
        "political_leaning": "far-left/left/center-left/center/center-right/right/far-right",
        "bias_indicators": ["specific bias indicators found"],
        "language_bias": 0.0-1.0,
        "source_bias": 0.0-1.0,
        "framing_bias": 0.0-1.0,
        "selection_bias": 0.0-1.0,
        "confirmation_bias": 0.0-1.0
      },
      "misinformation_analysis": {
        "risk_score": 0.0-1.0,
        "fact_checks": [
          {
            "claim": "specific factual claim",
            "verdict": "true/false/misleading/unverified/partially-true",
            "confidence": 0.0-1.0,
            "explanation": "detailed explanation",
            "sources": ["source1", "source2"]
          }
        ],
        "red_flags": ["specific misinformation indicators"],
        "logical_fallacies": ["fallacy1", "fallacy2"],
        "evidence_quality": 0.0-1.0
      },
      "sentiment_analysis": {
        "overall_sentiment": -1.0 to 1.0,
        "emotional_tone": "angry/fearful/hopeful/neutral/excited/concerned/optimistic",
        "sentiment_by_section": [{"section": 1, "sentiment": 0.0, "text_sample": "sample"}],
        "key_emotional_phrases": ["phrase1", "phrase2"],
        "emotional_manipulation": 0.0-1.0,
        "subjectivity_score": 0.0-1.0
      },
      "narrative_analysis": {
        "primary_frame": "economic/political/moral/scientific/social/cultural",
        "secondary_frames": ["frame1", "frame2"],
        "narrative_patterns": ["problem-solution", "conflict", "hero-villain", "crisis"],
        "actor_portrayal": {
          "government": "positive/negative/neutral/mixed",
          "experts": "positive/negative/neutral/mixed",
          "citizens": "positive/negative/neutral/mixed",
          "media": "positive/negative/neutral/mixed"
        },
        "perspective_diversity": 0.0-1.0,
        "narrative_coherence": 0.0-1.0
      },
      "credibility_assessment": {
        "overall_score": 0.0-1.0,
        "source_quality": 0.0-1.0,
        "evidence_quality": 0.0-1.0,
        "logical_consistency": 0.0-1.0,
        "transparency": 0.0-1.0,
        "expertise_indicators": ["indicator1", "indicator2"]
      },
      "technical_analysis": {
        "readability_score": 0.0-1.0,
        "complexity_level": "simple/moderate/complex/very-complex",
        "word_count": number,
        "key_topics": ["topic1", "topic2"],
        "named_entities": ["entity1", "entity2"],
        "language_register": "formal/informal/academic/colloquial"
      },
      "recommendations": {
        "verification_needed": ["claim1", "claim2"],
        "alternative_sources": ["suggestion1", "suggestion2"],
        "critical_questions": ["question1", "question2"],
        "bias_mitigation": ["strategy1", "strategy2"]
      },
      "confidence": 0.0-1.0,
      "processing_time": "timestamp",
      "model_version": "gemini-1.5-pro"
    }
    
    Content to analyze:
    "${content.substring(0, 8000)}"
    
    Provide only the JSON response, no additional text.
    `

    const result = await model.generateContent(prompt)
    const response = await result.response
    const text = response.text()

    try {
      // Parse the JSON response from Gemini
      const analysis = JSON.parse(text)

      // Store comprehensive analysis in MongoDB
      await storeComprehensiveAnalysis(content, analysis)

      // Generate additional insights
      const insights = generateAdditionalInsights(analysis)

      return NextResponse.json({
        success: true,
        analysis: {
          ...analysis,
          additional_insights: insights,
          processing_timestamp: new Date().toISOString(),
        },
        metadata: {
          content_length: content.length,
          processing_model: "gemini-1.5-pro",
          api_version: "2.0",
        },
      })
    } catch (parseError) {
      console.error("Failed to parse AI response:", parseError)

      // Enhanced fallback analysis
      const fallbackAnalysis = generateComprehensiveFallbackAnalysis(content)

      return NextResponse.json({
        success: true,
        analysis: fallbackAnalysis,
        metadata: {
          content_length: content.length,
          processing_model: "fallback-comprehensive",
          api_version: "2.0",
          note: "Fallback analysis used due to parsing error",
        },
      })
    }
  } catch (error) {
    console.error("AI Analysis Error:", error)
    return NextResponse.json(
      {
        success: false,
        error: "AI analysis failed",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}

async function storeComprehensiveAnalysis(content: string, analysis: any) {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/api/mongodb`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: content.substring(0, 100) + "...",
        content,
        source: "AI Analysis",
        url: null,
        topic: analysis.technical_analysis?.key_topics?.[0] || "general",
        bias_score: analysis.bias_analysis?.overall_score || 0,
        misinformation_risk: analysis.misinformation_analysis?.risk_score || 0,
        sentiment: analysis.sentiment_analysis?.overall_sentiment || 0,
        credibility_score: analysis.credibility_assessment?.overall_score || 0,
        fact_checks: analysis.misinformation_analysis?.fact_checks || [],
        narrative_analysis: analysis.narrative_analysis || {},
        comprehensive_analysis: analysis,
      }),
    })

    if (!response.ok) {
      console.error("Failed to store comprehensive analysis in MongoDB")
    }
  } catch (error) {
    console.error("Error storing comprehensive analysis:", error)
  }
}

function generateAdditionalInsights(analysis: any) {
  const insights = []

  // Bias insights
  if (analysis.bias_analysis?.overall_score > 0.7) {
    insights.push({
      type: "bias_warning",
      severity: "high",
      message: "High bias detected. Consider seeking alternative perspectives.",
      details: analysis.bias_analysis.bias_indicators,
    })
  }

  // Misinformation insights
  if (analysis.misinformation_analysis?.risk_score > 0.6) {
    insights.push({
      type: "misinformation_alert",
      severity: "high",
      message: "High misinformation risk. Fact-checking recommended.",
      details: analysis.misinformation_analysis.red_flags,
    })
  }

  // Credibility insights
  if (analysis.credibility_assessment?.overall_score < 0.4) {
    insights.push({
      type: "credibility_concern",
      severity: "medium",
      message: "Low credibility score. Verify claims independently.",
      details: ["Low source quality", "Insufficient evidence"],
    })
  }

  // Narrative insights
  if (analysis.narrative_analysis?.perspective_diversity < 0.3) {
    insights.push({
      type: "perspective_limitation",
      severity: "medium",
      message: "Limited perspective diversity. Seek additional viewpoints.",
      details: ["Single narrative frame", "Limited actor representation"],
    })
  }

  return insights
}

function generateComprehensiveFallbackAnalysis(content: string) {
  const words = content.toLowerCase().split(/\s+/)

  // Enhanced keyword analysis
  const analysisKeywords = {
    bias: {
      left: [
        "progressive",
        "liberal",
        "social justice",
        "inequality",
        "climate crisis",
        "systemic",
        "marginalized",
        "diversity",
        "inclusion",
      ],
      right: [
        "conservative",
        "traditional",
        "free market",
        "law and order",
        "family values",
        "patriotic",
        "constitutional",
        "freedom",
        "liberty",
      ],
    },
    sentiment: {
      positive: [
        "excellent",
        "amazing",
        "breakthrough",
        "success",
        "wonderful",
        "outstanding",
        "remarkable",
        "beneficial",
        "promising",
      ],
      negative: [
        "terrible",
        "awful",
        "crisis",
        "disaster",
        "shocking",
        "outrageous",
        "devastating",
        "alarming",
        "concerning",
      ],
    },
    misinformation: [
      "shocking truth",
      "they don't want you to know",
      "secret",
      "conspiracy",
      "cover-up",
      "mainstream media won't tell you",
      "hidden agenda",
    ],
    emotional: ["urgent", "critical", "devastating", "shocking", "incredible", "unbelievable", "must-see", "breaking"],
  }

  // Calculate scores
  const leftScore = analysisKeywords.bias.left.filter((word) => content.toLowerCase().includes(word)).length
  const rightScore = analysisKeywords.bias.right.filter((word) => content.toLowerCase().includes(word)).length
  const positiveScore = analysisKeywords.sentiment.positive.filter((word) =>
    content.toLowerCase().includes(word),
  ).length
  const negativeScore = analysisKeywords.sentiment.negative.filter((word) =>
    content.toLowerCase().includes(word),
  ).length
  const misinfoScore = analysisKeywords.misinformation.filter((phrase) => content.toLowerCase().includes(phrase)).length
  const emotionalScore = analysisKeywords.emotional.filter((word) => content.toLowerCase().includes(word)).length

  const biasScore = Math.min((leftScore + rightScore) / 15, 1)
  const sentiment = (positiveScore - negativeScore) / Math.max(words.length / 100, 1)
  const misinformationRisk = Math.min(misinfoScore / 3, 1)
  const emotionalManipulation = Math.min(emotionalScore / 10, 1)

  return {
    bias_analysis: {
      overall_score: biasScore,
      political_leaning: leftScore > rightScore ? "center-left" : rightScore > leftScore ? "center-right" : "center",
      bias_indicators: [],
      language_bias: biasScore,
      source_bias: 0.3,
      framing_bias: biasScore * 0.8,
      selection_bias: biasScore * 0.6,
      confirmation_bias: biasScore * 0.7,
    },
    misinformation_analysis: {
      risk_score: misinformationRisk,
      fact_checks: [],
      red_flags: [],
      logical_fallacies: [],
      evidence_quality: Math.max(0.3, 1 - misinformationRisk),
    },
    sentiment_analysis: {
      overall_sentiment: Math.max(-1, Math.min(1, sentiment)),
      emotional_tone: sentiment > 0.2 ? "positive" : sentiment < -0.2 ? "negative" : "neutral",
      sentiment_by_section: [],
      key_emotional_phrases: [],
      emotional_manipulation: emotionalManipulation,
      subjectivity_score: (biasScore + emotionalManipulation) / 2,
    },
    narrative_analysis: {
      primary_frame: "general",
      secondary_frames: [],
      narrative_patterns: [],
      actor_portrayal: {},
      perspective_diversity: Math.max(0.2, 1 - biasScore),
      narrative_coherence: 0.7,
    },
    credibility_assessment: {
      overall_score: Math.max(0.3, 1 - (biasScore + misinformationRisk) / 2),
      source_quality: 0.6,
      evidence_quality: 0.7,
      logical_consistency: 0.8,
      transparency: 0.6,
      expertise_indicators: [],
    },
    technical_analysis: {
      readability_score: 0.7,
      complexity_level: words.length > 500 ? "complex" : "moderate",
      word_count: words.length,
      key_topics: ["general"],
      named_entities: [],
      language_register: "informal",
    },
    recommendations: {
      verification_needed: [],
      alternative_sources: [],
      critical_questions: [],
      bias_mitigation: [],
    },
    confidence: 0.6,
    processing_time: new Date().toISOString(),
    model_version: "fallback-comprehensive",
  }
}
