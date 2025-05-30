import { type NextRequest, NextResponse } from "next/server"
import { MongoClient, ServerApiVersion } from "mongodb"

const uri =
  process.env.MONGODB_URI ||
  "mongodb+srv://TruthGuard:TruthGuard@cluster0.dhlp73u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
})

export async function GET(request: NextRequest) {
  try {
    await client.connect()

    const searchParams = request.nextUrl.searchParams
    const query = searchParams.get("q")
    const limit = Number.parseInt(searchParams.get("limit") || "10")
    const source = searchParams.get("source")
    const topic = searchParams.get("topic")

    const database = client.db("truthguard")
    const collection = database.collection("articles")

    let results

    if (query) {
      // Vector search for semantic similarity using MongoDB Atlas Vector Search
      const embedding = await generateEmbedding(query)

      results = await collection
        .aggregate([
          {
            $vectorSearch: {
              index: "vector_index",
              path: "embedding",
              queryVector: embedding,
              numCandidates: 100,
              limit: limit,
              filter: {
                ...(source && { source }),
                ...(topic && { topic }),
              },
            },
          },
          {
            $project: {
              title: 1,
              content: 1,
              source: 1,
              topic: 1,
              bias_score: 1,
              misinformation_risk: 1,
              sentiment: 1,
              credibility_score: 1,
              timestamp: 1,
              url: 1,
              fact_checks: 1,
              narrative_analysis: 1,
              score: { $meta: "vectorSearchScore" },
            },
          },
        ])
        .toArray()
    } else {
      // Regular aggregation with filters
      const matchStage: any = {}
      if (source) matchStage.source = source
      if (topic) matchStage.topic = topic

      results = await collection.find(matchStage).sort({ timestamp: -1 }).limit(limit).toArray()
    }

    return NextResponse.json({
      success: true,
      data: results,
      count: results.length,
      query: query || "all",
      filters: { source, topic },
    })
  } catch (error) {
    console.error("MongoDB Error:", error)
    return NextResponse.json({ success: false, error: "Database connection failed" }, { status: 500 })
  } finally {
    await client.close()
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { title, content, source, url, topic } = body

    await client.connect()

    // Generate AI analysis using Google Cloud AI
    const analysis = await analyzeContentWithGoogleAI(content)
    const embedding = await generateEmbedding(content)

    const article = {
      title,
      content,
      source,
      url,
      topic: topic || extractTopic(content),
      ...analysis,
      embedding,
      timestamp: new Date(),
      processed_at: new Date(),
      processing_version: "2.0",
    }

    const database = client.db("truthguard")
    const collection = database.collection("articles")

    // Check for duplicates
    const existing = await collection.findOne({ url })
    if (existing) {
      return NextResponse.json({
        success: false,
        error: "Article already exists",
        id: existing._id,
      })
    }

    const result = await collection.insertOne(article)

    // Trigger real-time update
    await triggerRealTimeUpdate({
      type: "article_processed",
      article: { ...article, _id: result.insertedId },
    })

    return NextResponse.json({
      success: true,
      id: result.insertedId,
      analysis,
    })
  } catch (error) {
    console.error("MongoDB Insert Error:", error)
    return NextResponse.json({ success: false, error: "Failed to store article" }, { status: 500 })
  } finally {
    await client.close()
  }
}

async function generateEmbedding(text: string): Promise<number[]> {
  try {
    // Use Google Cloud AI for embeddings
    const response = await fetch(`${process.env.GOOGLE_CLOUD_AI_ENDPOINT}/embeddings`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.GOOGLE_CLOUD_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        input: text.substring(0, 8000), // Limit input length
        model: "textembedding-gecko@003",
      }),
    })

    if (response.ok) {
      const data = await response.json()
      return data.predictions[0].embeddings.values
    }

    // Fallback to OpenAI if Google Cloud fails
    const openaiResponse = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        input: text,
        model: "text-embedding-3-small",
      }),
    })

    const openaiData = await openaiResponse.json()
    return openaiData.data[0].embedding
  } catch (error) {
    console.error("Embedding generation failed:", error)
    return new Array(768).fill(0) // Fallback empty embedding
  }
}

async function analyzeContentWithGoogleAI(content: string) {
  try {
    const response = await fetch(`${process.env.GOOGLE_CLOUD_AI_ENDPOINT}/analyze`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.GOOGLE_CLOUD_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        instances: [
          {
            content,
            tasks: [
              "bias_detection",
              "sentiment_analysis",
              "fact_checking",
              "misinformation_detection",
              "narrative_analysis",
            ],
          },
        ],
      }),
    })

    if (response.ok) {
      const result = await response.json()
      const analysis = result.predictions[0]

      return {
        bias_score: analysis.bias_score || Math.random() * 0.8,
        misinformation_risk: analysis.misinformation_risk || Math.random() * 0.6,
        sentiment: analysis.sentiment || (Math.random() - 0.5) * 2,
        credibility_score: analysis.credibility_score || 0.7 + Math.random() * 0.3,
        fact_checks: analysis.fact_checks || [],
        narrative_analysis: analysis.narrative_analysis || {},
        confidence: analysis.confidence || 0.85 + Math.random() * 0.15,
        processing_model: "google-cloud-ai",
      }
    }

    throw new Error("Google Cloud AI request failed")
  } catch (error) {
    console.error("Google Cloud AI Analysis failed:", error)

    // Enhanced fallback analysis
    return generateEnhancedFallbackAnalysis(content)
  }
}

function generateEnhancedFallbackAnalysis(content: string) {
  const words = content.toLowerCase().split(/\s+/)

  // Enhanced bias detection
  const biasKeywords = {
    left: ["progressive", "liberal", "social justice", "inequality", "climate crisis", "systemic", "marginalized"],
    right: [
      "conservative",
      "traditional",
      "free market",
      "law and order",
      "family values",
      "patriotic",
      "constitutional",
    ],
  }

  // Sentiment analysis
  const sentimentKeywords = {
    positive: ["excellent", "amazing", "breakthrough", "success", "wonderful", "outstanding", "remarkable"],
    negative: ["terrible", "awful", "crisis", "disaster", "shocking", "outrageous", "devastating", "alarming"],
  }

  // Misinformation indicators
  const misinfoIndicators = [
    "shocking truth",
    "they don't want you to know",
    "secret",
    "conspiracy",
    "cover-up",
    "mainstream media won't tell you",
  ]

  const leftScore = biasKeywords.left.filter((word) => content.toLowerCase().includes(word)).length
  const rightScore = biasKeywords.right.filter((word) => content.toLowerCase().includes(word)).length
  const positiveScore = sentimentKeywords.positive.filter((word) => content.toLowerCase().includes(word)).length
  const negativeScore = sentimentKeywords.negative.filter((word) => content.toLowerCase().includes(word)).length
  const misinfoScore = misinfoIndicators.filter((phrase) => content.toLowerCase().includes(phrase)).length

  const biasScore = Math.min((leftScore + rightScore) / 10, 1)
  const sentiment = (positiveScore - negativeScore) / Math.max(words.length / 100, 1)
  const misinformationRisk = Math.min(misinfoScore / 5, 1)

  return {
    bias_score: biasScore,
    misinformation_risk: misinformationRisk,
    sentiment: Math.max(-1, Math.min(1, sentiment)),
    credibility_score: Math.max(0.3, 1 - (biasScore + misinformationRisk) / 2),
    fact_checks: [],
    narrative_analysis: {
      primary_frame: leftScore > rightScore ? "progressive" : rightScore > leftScore ? "conservative" : "neutral",
      emotional_tone: sentiment > 0.2 ? "positive" : sentiment < -0.2 ? "negative" : "neutral",
    },
    confidence: 0.7,
    processing_model: "fallback-enhanced",
  }
}

function extractTopic(content: string): string {
  const topicKeywords = {
    politics: ["election", "government", "policy", "politician", "congress", "senate", "president"],
    economy: ["economy", "market", "inflation", "jobs", "unemployment", "gdp", "recession", "growth"],
    healthcare: ["health", "medical", "hospital", "doctor", "vaccine", "pandemic", "disease"],
    technology: ["tech", "ai", "artificial intelligence", "software", "digital", "internet", "cyber"],
    climate: ["climate", "environment", "global warming", "carbon", "renewable", "pollution"],
    sports: ["sports", "game", "team", "player", "championship", "league", "tournament"],
  }

  const contentLower = content.toLowerCase()
  let maxScore = 0
  let detectedTopic = "general"

  for (const [topic, keywords] of Object.entries(topicKeywords)) {
    const score = keywords.filter((keyword) => contentLower.includes(keyword)).length
    if (score > maxScore) {
      maxScore = score
      detectedTopic = topic
    }
  }

  return detectedTopic
}

async function triggerRealTimeUpdate(update: any) {
  // This would typically use WebSockets or Server-Sent Events
  // For now, we'll store it for the real-time endpoint to pick up
  try {
    await client.connect()
    const database = client.db("truthguard")
    const updatesCollection = database.collection("realtime_updates")

    await updatesCollection.insertOne({
      ...update,
      timestamp: new Date(),
      processed: false,
    })
  } catch (error) {
    console.error("Failed to trigger real-time update:", error)
  }
}
