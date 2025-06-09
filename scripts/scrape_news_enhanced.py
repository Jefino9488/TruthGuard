#!/usr/bin/env python3
"""
TruthGuard News API Fetcher
Fetches news articles from News API using newsapi-python and stores them in MongoDB Atlas with vector search
"""

import os
from datetime import datetime
import pymongo
import time
import logging
import hashlib
from newspaper import Article
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from newsapi import NewsApiClient  # Import newsapi-python client

# Load environment variables
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping_logs/scraper.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create necessary directories
os.makedirs('scraping_logs', exist_ok=True)
os.makedirs('scraped_data', exist_ok=True)

# News API categories and topics
CATEGORIES = ["business", "technology", "science", "health", "general"]
TOPICS = ["misinformation", "fact checking", "media bias", "artificial intelligence", "politics", "climate"]

class NewsAPIFetcher:
    def __init__(self, news_api_key: str, mongo_uri: str, app_logger=None):
        if app_logger:
            self.logger = app_logger
        else:
            # Configure a default logger for standalone use
            self.logger = logging.getLogger(__name__ + ".NewsAPIFetcher")
            if not self.logger.handlers: # Avoid adding multiple handlers if already configured
                # Basic configuration if run standalone
                log_file_handler = logging.FileHandler('scraping_logs/scraper_fetcher.log', mode='a')
                log_stream_handler = logging.StreamHandler()
                log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                log_file_handler.setFormatter(log_formatter)
                log_stream_handler.setFormatter(log_formatter)
                self.logger.addHandler(log_file_handler)
                self.logger.addHandler(log_stream_handler)
                self.logger.setLevel(logging.INFO)

        self.api_key = news_api_key
        if not self.api_key:
            self.logger.error("News API key not provided.") # Changed from raise to log
            raise ValueError("News API key is required")

        self.mongo_uri = mongo_uri
        if not self.mongo_uri:
            self.logger.error("MongoDB URI not provided.") # Changed from raise to log
            raise ValueError("MongoDB URI is required")

        # Initialize NewsApiClient
        self.logger.info("Initializing News API client...")
        self.newsapi = NewsApiClient(api_key=self.api_key)

        # MongoDB connection
        self.logger.info(f"Connecting to MongoDB at {self.mongo_uri.split('@')[-1].split('/')[0]}...") # Mask credentials
        self.mongo_client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.mongo_client.truthguard # Consider making db name configurable too
        self.collection = self.db.articles

        # Initialize sentence transformer model for embeddings
        self.logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

        # Ensure indexes for full-text search
        self.logger.info("Creating MongoDB indexes for 'articles' collection...")
        self.collection.create_index([("title", "text"), ("content", "text")], name="idx_title_content_text")
        self.collection.create_index([("article_id", pymongo.ASCENDING)], unique=True, name="idx_article_id_unique")


        # Statistics
        self.stats = {
            'categories_processed': 0,
            'topics_processed': 0,
            'articles_found': 0,
            'articles_stored': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }

    def fetch_top_headlines(self, country="us", category=None, page_size=20):
        """Fetch top headlines from News API using newsapi-python"""
        try:
            params = {
                "country": country,
                "page_size": page_size
            }
            if category:
                params["category"] = category

            response = self.newsapi.get_top_headlines(**params)

            if response["status"] != "ok":
                self.logger.error(f"API Error: {response.get('message', 'Unknown error')}")
                return []

            self.logger.info(f"Fetched {len(response['articles'])} top headlines for category: {category or 'all'}")
            return response["articles"]

        except Exception as e:
            self.logger.error(f"Error fetching top headlines: {e}")
            self.stats['errors'] += 1
            return []

    def fetch_everything(self, query, language="en", sort_by="publishedAt", page_size=20):
        """Fetch articles matching query from News API using newsapi-python"""
        try:
            response = self.newsapi.get_everything(
                q=query,
                language=language,
                sort_by=sort_by,
                page_size=page_size
            )

            if response["status"] != "ok":
                self.logger.error(f"API Error: {response.get('message', 'Unknown error')}")
                return []

            self.logger.info(f"Fetched {len(response['articles'])} articles for query: {query}")
            return response["articles"]

        except Exception as e:
            self.logger.error(f"Error fetching articles: {e}")
            self.stats['errors'] += 1
            return []

    def extract_full_content(self, url):
        """Extract full article content using newspaper3k"""
        try:
            article = Article(url)
            article.download()
            article.parse()

            # Return full text if available, otherwise return empty string
            return article.text if article.text else ""

        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {e}")
            return ""

    def generate_embedding(self, text):
        """Generate vector embedding for text using sentence-transformers"""
        try:
            # Truncate text if it's too long (model has input limits)
            max_length = 10000
            if len(text) > max_length:
                text = text[:max_length]

            # Generate embedding
            embedding = self.model.encode(text)
            return embedding.tolist()  # Convert numpy array to list for MongoDB storage

        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return None

    def process_article(self, article):
        """Process a single article from News API"""
        try:
            # Extract basic info from API response
            title = article.get("title", "")
            url = article.get("url", "")
            source_name = article.get("source", {}).get("name", "Unknown")
            published_at = article.get("publishedAt", "")
            description = article.get("description", "")

            # Skip articles without title or URL
            if not title or not url:
                self.logger.warning(f"Skipping article with missing title or URL")
                return None

            # Generate a unique ID for the article based on URL
            article_id = hashlib.md5(url.encode()).hexdigest()

            # Check if article already exists in database
            existing = self.collection.find_one({"article_id": article_id})
            if existing:
                self.logger.info(f"Article already exists: {title[:50]}...")
                self.stats['duplicates_skipped'] += 1
                return None

            # Extract full content using newspaper3k
            content = self.extract_full_content(url)

            # If content extraction failed, use description as fallback
            if not content and description:
                content = description

            # Skip articles with insufficient content
            if len(content) < 200:
                self.logger.warning(f"Skipping article with insufficient content: {title[:50]}...")
                return None

            # Generate vector embedding for content
            content_embedding = self.generate_embedding(content)
            title_embedding = self.generate_embedding(title)

            # Create article document
            article_doc = {
                "article_id": article_id,
                "title": title,
                "url": url,
                "source": source_name,
                "published_at": published_at,
                "content": content,
                "description": description,
                "scraped_at": datetime.utcnow(),
                "processed": False,
                "processing_status": "pending",
                "content_hash": hashlib.md5(content.encode()).hexdigest(),
                "word_count": len(content.split()),
                "content_embedding": content_embedding,
                "title_embedding": title_embedding,
                "data_source": "news_api"
            }

            return article_doc

        except Exception as e:
            self.logger.error(f"Error processing article: {e}")
            self.stats['errors'] += 1
            return None

    def store_articles(self, articles):
        """Store articles in MongoDB"""
        if not articles:
            return 0

        try:
            # Insert articles
            inserted_count = 0
            for article in articles:
                if article:
                    self.collection.insert_one(article)
                    inserted_count += 1
                    self.logger.info(f"Stored: {article['title'][:50]}...")

            self.stats['articles_stored'] += inserted_count
            self.logger.info(f"Stored {inserted_count} articles in MongoDB")
            return inserted_count

        except Exception as e:
            self.logger.error(f"Error storing articles: {e}")
            self.stats['errors'] += 1
            return 0

    def run(self):
        """Run the complete fetching process"""
        self.logger.info("Starting TruthGuard News API fetching...")

        all_articles = []

        # Fetch top headlines for each category
        for category in CATEGORIES:
            self.logger.info(f"Fetching top headlines for category: {category}")
            articles = self.fetch_top_headlines(category=category)

            # Process each article
            processed_articles = []
            for article in articles:
                processed = self.process_article(article)
                if processed:
                    processed_articles.append(processed)
                    self.stats['articles_found'] += 1

            self.logger.info(f"Fetched {len(processed_articles)} articles for category {category}")
            all_articles.extend(processed_articles)
            self.stats['categories_processed'] += 1
            time.sleep(1)  # Rate limiting

        # Fetch articles for specific topics
        for topic in TOPICS:
            self.logger.info(f"Fetching articles for topic: {topic}")
            articles = self.fetch_everything(query=topic)

            # Process each article
            processed_articles = []
            for article in articles:
                processed = self.process_article(article)
                if processed:
                    processed_articles.append(processed)
                    self.stats['articles_found'] += 1

            self.logger.info(f"Fetched {len(processed_articles)} articles for topic {topic}")
            all_articles.extend(processed_articles)
            self.stats['topics_processed'] += 1
            time.sleep(1)  # Rate limiting

        # Store articles in MongoDB
        stored_count = self.store_articles(all_articles)

        # Save to file for GitLab artifacts
        self.save_scraping_summary(all_articles)

        self.logger.info(f"Fetching complete. Total articles found (before filtering for storage): {self.stats['articles_found']}, Stored: {self.stats['articles_stored']}")

        return self.stats # Return the statistics dictionary

    def save_scraping_summary(self, articles):
        """Save scraping summary and sample data"""
        summary = {
            'scraping_timestamp': datetime.utcnow().isoformat(),
            'statistics': self.stats,
            'sample_articles': [
                {
                    'title': article['title'],
                    'source': article['source'],
                    'url': article['url'],
                    'word_count': article.get('word_count', 0),
                    'published_at': article.get('published_at', '')
                }
                for article in articles[:10]  # Sample of first 10
            ],
            'categories_processed': CATEGORIES,
            'topics_processed': TOPICS
        }

        # Save summary
        with open('scraped_data/scraping_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        # Save full article data (limited for artifact size)
        limited_articles = [
            {
                'title': article['title'],
                'source': article['source'],
                'url': article['url'],
                'content_preview': article['content'][:500] + '...' if len(article['content']) > 500 else article['content'],
                'scraped_at': article['scraped_at'],
                'has_embedding': article['content_embedding'] is not None
            }
            for article in articles[:50]  # Limit for artifact size
        ]

        with open('scraped_data/articles_sample.json', 'w') as f:
            json.dump(limited_articles, f, indent=2, default=str)

        self.logger.info("Scraping summary saved to artifacts")

if __name__ == "__main__":
    import json # Keep this import local if only used here
    load_dotenv('.env.local') # Load .env for standalone run

    news_key = os.getenv('NEWS_API_KEY_SCRAPER') # Use a distinct name or ensure .env has NEWS_API_KEY
    mongo_connection_string = os.getenv('MONGODB_URI')

    if not news_key:
        print("Error: NEWS_API_KEY_SCRAPER environment variable not set for standalone run.")
        sys.exit(1)
    if not mongo_connection_string:
        print("Error: MONGODB_URI environment variable not set for standalone run.")
        sys.exit(1)

    # Standalone logger configuration (basic, could be more elaborate)
    # The global logger configuration at the top of the file will apply if not overridden by specific class loggers.
    # Ensure the global logger is configured before instantiating.
    standalone_logger = logging.getLogger(__name__) # This will use the global config at the top

    fetcher = NewsAPIFetcher(news_api_key=news_key, mongo_uri=mongo_connection_string, app_logger=standalone_logger)
    sys.exit(fetcher.run())