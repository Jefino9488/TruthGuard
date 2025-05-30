import { type NextRequest, NextResponse } from "next/server"
import { JSDOM } from "jsdom"

// Enhanced news sources for comprehensive coverage
const DEFAULT_NEWS_SOURCES = [
  "https://www.reuters.com/world/",
  "https://apnews.com/",
  "https://www.bbc.com/news",
  "https://www.cnn.com/",
  "https://www.foxnews.com/",
  "https://www.npr.org/",
  "https://www.washingtonpost.com/",
  "https://www.nytimes.com/",
  "https://www.wsj.com/",
  "https://www.theguardian.com/us",
]

export async function POST(request: NextRequest) {
  try {
    const { urls, auto_scrape = false } = await request.json()

    const urlsToScrape = urls && urls.length > 0 ? urls : auto_scrape ? DEFAULT_NEWS_SOURCES : []

    if (urlsToScrape.length === 0) {
      return NextResponse.json({ error: "URLs array is required" }, { status: 400 })
    }

    const results = []
    const batchSize = 5 // Process in batches to avoid overwhelming servers

    for (let i = 0; i < urlsToScrape.length; i += batchSize) {
      const batch = urlsToScrape.slice(i, i + batchSize)

      const batchPromises = batch.map(async (url) => {
        try {
          const articles = await scrapeNewsSource(url)
          const processedArticles = []

          for (const article of articles) {
            try {
              // Store in MongoDB with comprehensive AI analysis
              const storeResponse = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/api/mongodb`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(article),
              })

              const storeResult = await storeResponse.json()
              processedArticles.push({
                url: article.url,
                title: article.title,
                success: storeResult.success,
                id: storeResult.id,
                analysis: storeResult.analysis,
              })
            } catch (error) {
              console.error(`Failed to process article ${article.url}:`, error)
              processedArticles.push({
                url: article.url,
                title: article.title,
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
              })
            }
          }

          return {
            source_url: url,
            articles_found: articles.length,
            articles_processed: processedArticles,
            success: true,
          }
        } catch (error) {
          console.error(`Failed to scrape ${url}:`, error)
          return {
            source_url: url,
            articles_found: 0,
            articles_processed: [],
            success: false,
            error: error instanceof Error ? error.message : "Unknown error",
          }
        }
      })

      const batchResults = await Promise.all(batchPromises)
      results.push(...batchResults)

      // Add delay between batches to be respectful
      if (i + batchSize < urlsToScrape.length) {
        await new Promise((resolve) => setTimeout(resolve, 2000))
      }
    }

    const totalArticles = results.reduce((sum, result) => sum + result.articles_found, 0)
    const successfulSources = results.filter((r) => r.success).length

    return NextResponse.json({
      success: true,
      results,
      summary: {
        sources_processed: results.length,
        successful_sources: successfulSources,
        total_articles_found: totalArticles,
        processing_time: new Date().toISOString(),
      },
    })
  } catch (error) {
    console.error("Scraper Error:", error)
    return NextResponse.json(
      {
        success: false,
        error: "Scraping failed",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}

async function scrapeNewsSource(sourceUrl: string) {
  try {
    const response = await fetch(sourceUrl, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        Connection: "keep-alive",
      },
      timeout: 30000,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const html = await response.text()
    const dom = new JSDOM(html)
    const document = dom.window.document

    // Extract articles using multiple strategies
    const articles = []
    const articleLinks = extractArticleLinks(document, sourceUrl)

    // Limit to first 5 articles per source to avoid overwhelming
    for (const link of articleLinks.slice(0, 5)) {
      try {
        const article = await scrapeArticle(link.url)
        if (article) {
          articles.push({
            ...article,
            source: extractSourceName(sourceUrl),
            source_url: sourceUrl,
            headline_from_listing: link.title,
          })
        }
      } catch (error) {
        console.error(`Failed to scrape article ${link.url}:`, error)
      }
    }

    return articles
  } catch (error) {
    console.error(`Error scraping source ${sourceUrl}:`, error)
    return []
  }
}

function extractArticleLinks(document: Document, baseUrl: string) {
  const links = []

  // Common selectors for article links
  const selectors = [
    'a[href*="/article/"]',
    'a[href*="/story/"]',
    'a[href*="/news/"]',
    'a[href*="/politics/"]',
    'a[href*="/world/"]',
    "h1 a",
    "h2 a",
    "h3 a",
    ".headline a",
    ".story-headline a",
    '[data-testid="card-headline"] a',
  ]

  for (const selector of selectors) {
    const elements = document.querySelectorAll(selector)

    for (const element of elements) {
      const href = element.getAttribute("href")
      const title = element.textContent?.trim()

      if (href && title && title.length > 10) {
        let fullUrl = href

        if (!href.startsWith("http")) {
          try {
            fullUrl = new URL(href, baseUrl).toString()
          } catch {
            continue
          }
        }

        // Avoid duplicates and non-article URLs
        if (
          !links.some((l) => l.url === fullUrl) &&
          !href.includes("#") &&
          !href.includes("mailto:") &&
          !href.includes("javascript:")
        ) {
          links.push({ url: fullUrl, title })
        }
      }
    }
  }

  return links
}

async function scrapeArticle(url: string) {
  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
      },
      timeout: 20000,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const html = await response.text()
    const dom = new JSDOM(html)
    const document = dom.window.document

    const title = extractTitle(document)
    const content = extractContent(document)
    const author = extractAuthor(document)
    const publishDate = extractPublishDate(document)

    if (!title || !content || content.length < 100) {
      throw new Error("Insufficient content extracted")
    }

    return {
      title,
      content,
      author,
      publish_date: publishDate,
      url,
      scraped_at: new Date().toISOString(),
      content_length: content.length,
      word_count: content.split(/\s+/).length,
    }
  } catch (error) {
    console.error(`Error scraping article ${url}:`, error)
    return null
  }
}

function extractTitle(document: Document): string {
  const selectors = [
    "h1",
    '[data-testid="headline"]',
    ".headline",
    ".article-title",
    ".entry-title",
    "title",
    '[property="og:title"]',
  ]

  for (const selector of selectors) {
    const element = document.querySelector(selector)
    if (element?.textContent?.trim()) {
      return element.textContent.trim()
    }
  }

  return "Untitled Article"
}

function extractContent(document: Document): string {
  const selectors = [
    "article",
    ".article-body",
    ".story-body",
    ".post-content",
    ".entry-content",
    '[data-testid="article-body"]',
    ".content",
    ".article-content",
  ]

  for (const selector of selectors) {
    const element = document.querySelector(selector)
    if (element?.textContent?.trim()) {
      // Clean up the content
      const content = element.textContent
        .trim()
        .replace(/\s+/g, " ")
        .replace(/\n\s*\n/g, "\n\n")

      if (content.length > 200) {
        return content
      }
    }
  }

  // Fallback: get all paragraph text
  const paragraphs = Array.from(document.querySelectorAll("p"))
  const content = paragraphs
    .map((p) => p.textContent?.trim())
    .filter((text) => text && text.length > 30)
    .join("\n\n")

  return content || "Content could not be extracted"
}

function extractAuthor(document: Document): string {
  const selectors = ['[rel="author"]', ".author", ".byline", '[data-testid="author"]', ".article-author"]

  for (const selector of selectors) {
    const element = document.querySelector(selector)
    if (element?.textContent?.trim()) {
      return element.textContent.trim()
    }
  }

  return "Unknown Author"
}

function extractPublishDate(document: Document): string {
  const selectors = [
    '[property="article:published_time"]',
    '[name="publish_date"]',
    ".publish-date",
    ".article-date",
    "time[datetime]",
  ]

  for (const selector of selectors) {
    const element = document.querySelector(selector)
    const dateValue =
      element?.getAttribute("content") || element?.getAttribute("datetime") || element?.textContent?.trim()

    if (dateValue) {
      try {
        return new Date(dateValue).toISOString()
      } catch {
        continue
      }
    }
  }

  return new Date().toISOString()
}

function extractSourceName(url: string): string {
  try {
    const domain = new URL(url).hostname.replace("www.", "")

    // Map domains to readable names
    const sourceMap: { [key: string]: string } = {
      "reuters.com": "Reuters",
      "apnews.com": "Associated Press",
      "bbc.com": "BBC",
      "cnn.com": "CNN",
      "foxnews.com": "Fox News",
      "npr.org": "NPR",
      "washingtonpost.com": "Washington Post",
      "nytimes.com": "New York Times",
      "wsj.com": "Wall Street Journal",
      "theguardian.com": "The Guardian",
    }

    return sourceMap[domain] || domain
  } catch {
    return "Unknown Source"
  }
}
