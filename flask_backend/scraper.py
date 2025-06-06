#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Scraper Module for TruthGuard Backend.

This module is responsible for fetching news articles from various sources
(currently NewsAPI) using the newsapi-python client. It processes these
articles, extracts content using the newspaper3k library, generates
vector embeddings using sentence-transformers, and stores them in a
MongoDB database. It also handles duplicate detection and saves
scraping summaries.

The main entry point for scraping tasks is `run_scraping_task()`.
"""

import os
from datetime import datetime
import pymongo
import time
import logging
import hashlib
from newspaper import Article
from dotenv import load_dotenv # Keep for now, might be redundant if Flask handles it
from sentence_transformers import SentenceTransformer
import sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from newsapi import NewsApiClient
import json # Added import
from .analyzer import run_analysis_task # Import the analysis task runner

# Configure logging - paths will be relative to flask_backend
# Note: Flask app might reconfigure logging, this is a fallback or for direct script use
LOG_DIR = 'scraping_logs'
DATA_DIR = 'scraped_data'

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Basic configuration for this module's logger.
# Note: If the Flask app's logger is configured with basicConfig,
# this might inherit that config if this module's logger is a child.
# However, this script defines its own handlers for a separate log file.
scraper_logger = logging.getLogger(__name__) # Logger named after the module: 'flask_backend.scraper'
scraper_logger.setLevel(logging.INFO) # Default level for this logger

# File Handler for scraper-specific logs
scraper_file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'scraper.log'), mode='a')
scraper_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')) # Simpler format for module log
scraper_logger.addHandler(scraper_file_handler)

# Optional: Console Handler for scraper logs (can be noisy if app also logs to console)
# scraper_stream_handler = logging.StreamHandler()
# scraper_stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# scraper_logger.addHandler(scraper_stream_handler)

scraper_logger.propagate = False # Avoid passing to parent/root logger if it has handlers, to prevent duplicates.

# News API categories and topics for fetching
CATEGORIES = ["business", "technology", "science", "health", "general", "entertainment", "sports"]
TOPICS = ["misinformation", "fact checking", "media bias", "artificial intelligence", "global politics", "climate change", "election integrity"]

class NewsAPIFetcher:
    """
    A class to fetch, process, and store news articles from NewsAPI.

    Attributes:
        api_key (str): NewsAPI API key.
        mongodb_uri (str): MongoDB connection URI.
        newsapi (NewsApiClient): Instance of the NewsAPI client.
        mongo_client (pymongo.MongoClient): MongoDB client instance.
        db (pymongo.database.Database): MongoDB database instance ('truthguard').
        collection (pymongo.collection.Collection): MongoDB collection instance ('articles').
        model (SentenceTransformer): Sentence embedding model.
        stats (dict): Dictionary to store scraping statistics.
    """
    def __init__(self, news_api_key: str, mongodb_uri: str):
        """
        Initializes the NewsAPIFetcher with API keys and database URI.

        Args:
            news_api_key (str): The API key for NewsAPI.
            mongodb_uri (str): The connection URI for MongoDB.

        Raises:
            ValueError: If `news_api_key` or `mongodb_uri` is not provided.
        """
        if not news_api_key:
            scraper_logger.error("NEWS_API_KEY not provided to NewsAPIFetcher constructor.")
            raise ValueError("NEWS_API_KEY is required for NewsAPIFetcher.")
        self.api_key = news_api_key

        if not mongodb_uri:
            scraper_logger.error("MONGODB_URI not provided to NewsAPIFetcher constructor.")
            raise ValueError("MONGODB_URI is required for NewsAPIFetcher.")
        self.mongo_uri = mongodb_uri

        scraper_logger.info("Initializing News API client...")
        self.newsapi = NewsApiClient(api_key=self.api_key)

        scraper_logger.info(f"Connecting to MongoDB at URI: {'mongodb+srv://... (credentials hidden)' if 'mongodb+srv://' in self.mongo_uri else self.mongo_uri}")
        self.mongo_client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.mongo_client.truthguard # Database name is 'truthguard'
        self.collection = self.db.articles     # Collection name is 'articles'

        scraper_logger.info("Loading sentence transformer model 'all-MiniLM-L6-v2' for embeddings...")
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2') # Model for generating 384-dimensional embeddings
        except Exception as e:
            scraper_logger.error(f"Failed to load SentenceTransformer model: {e}. Ensure it's installed and accessible.", exc_info=True)
            raise

        scraper_logger.info("Ensuring MongoDB indexes for 'articles' collection...")
        try:
            # Text index for searching within title and content fields
            self.collection.create_index([("title", "text"), ("content", "text")],
                                         name="text_index_title_content", background=True)
            # Unique index on 'article_id' (MD5 hash of URL) to prevent duplicates
            self.collection.create_index([("article_id", pymongo.ASCENDING)],
                                         name="unique_article_id", unique=True, background=True)
            scraper_logger.info("Core scraper indexes ensured.")
        except Exception as e:
            scraper_logger.error(f"Error creating core scraper indexes: {e}", exc_info=True)
            # Depending on policy, could raise this or just log.
            # For now, logging, as app-level index creation might also run.

        # Statistics for the current scraping run
        self.stats = {
            'start_time': datetime.utcnow().isoformat(), # Timestamp for when the task started
            'end_time': None,                             # Timestamp for when the task finished
            'categories_processed': 0,                    # Count of NewsAPI categories processed
            'topics_processed': 0,                        # Count of NewsAPI topics/queries processed
            'articles_found_from_api': 0,                 # Total articles received from NewsAPI
            'articles_processed_successfully': 0,         # Articles that passed local processing (content extraction, etc.)
            'articles_stored_in_db': 0,                   # New articles actually inserted into MongoDB
            'duplicates_skipped': 0,                      # Articles skipped due to already existing in DB
            'fetch_errors': 0,                            # Errors during API calls to NewsAPI
            'processing_errors': 0,                       # Errors during local article processing (content, embedding)
            'storage_errors': 0,                          # Errors during MongoDB insertion
            'status': 'pending'                           # Overall status of the scraping task
        }

    def fetch_top_headlines(self, country: str = "us", category: str = None, page_size: int = 20) -> list:
        """
        Fetches top headlines from NewsAPI for a given country and category.

        Args:
            country (str): The 2-letter ISO 3166-1 code of the country. Default is "us".
            category (str, optional): The category to fetch (e.g., "business", "technology").
                                      Default is None (all categories).
            page_size (int): The number of results to return per page. Default is 20.

        Returns:
            list: A list of article dictionaries from NewsAPI, or an empty list if an error occurs.
        """
        try:
            params = {"country": country, "page_size": page_size}
            if category:
                params["category"] = category

            scraper_logger.debug(f"Fetching top headlines with params: {params}")
            response = self.newsapi.get_top_headlines(**params)

            if response.get("status") != "ok":
                scraper_logger.error(f"NewsAPI Error (top-headlines, category: {category}): {response.get('message', 'Unknown error')}")
                self.stats['fetch_errors'] += 1
                return []

            num_articles = len(response.get('articles', []))
            scraper_logger.info(f"Fetched {num_articles} top headlines for category: {category or 'all'}")
            self.stats['articles_found_from_api'] += num_articles
            return response.get("articles", [])
        except Exception as e:
            scraper_logger.error(f"Exception fetching top headlines for category {category}: {e}", exc_info=True)
            self.stats['fetch_errors'] += 1
            return []

    def fetch_everything(self, query: str, language: str = "en", sort_by: str = "publishedAt", page_size: int = 20) -> list:
        """
        Fetches articles matching a query from NewsAPI.

        Args:
            query (str): The search query.
            language (str): The 2-letter ISO 639-1 code of the language. Default is "en".
            sort_by (str): The order to sort articles (e.g., "publishedAt", "relevancy"). Default is "publishedAt".
            page_size (int): The number of results to return per page. Default is 20.

        Returns:
            list: A list of article dictionaries from NewsAPI, or an empty list if an error occurs.
        """
        try:
            scraper_logger.debug(f"Fetching 'everything' for query: '{query}' with params: lang={language}, sort_by={sort_by}, page_size={page_size}")
            response = self.newsapi.get_everything(
                q=query,
                language=language,
                sort_by=sort_by,
                page_size=page_size
            )
            if response.get("status") != "ok":
                scraper_logger.error(f"NewsAPI Error (everything, query: {query}): {response.get('message', 'Unknown error')}")
                self.stats['fetch_errors'] += 1
                return []

            num_articles = len(response.get('articles', []))
            scraper_logger.info(f"Fetched {num_articles} articles for query: '{query}'")
            self.stats['articles_found_from_api'] += num_articles
            return response.get("articles", [])
        except Exception as e:
            scraper_logger.error(f"Exception fetching 'everything' for query '{query}': {e}", exc_info=True)
            self.stats['fetch_errors'] += 1
            return []

    def extract_full_content(self, url: str) -> str:
        """
        Extracts the full text content from an article URL using newspaper3k.

        Args:
            url (str): The URL of the article.

        Returns:
            str: The extracted full text content, or an empty string if extraction fails.
        """
        try:
            scraper_logger.debug(f"Extracting content from URL: {url}")
            article_parser = Article(url)
            article_parser.download()
            article_parser.parse()
            scraper_logger.debug(f"Successfully parsed content from URL: {url}")
            return article_parser.text if article_parser.text else ""
        except Exception as e:
            # Log as warning because some articles might be intentionally difficult to parse or are not standard articles.
            scraper_logger.warning(f"Could not extract full content from URL '{url}': {e}", exc_info=False) # Set exc_info=False for less verbose logs for common errors
            return "" # Return empty string on failure

    def generate_embedding(self, text: str) -> list[float] | None:
        """
        Generates a vector embedding for the given text using the SentenceTransformer model.

        Args:
            text (str): The text to embed.

        Returns:
            list[float] | None: A list of floats representing the embedding, or None if generation fails.
        """
        if not text:
            scraper_logger.warning("Attempted to generate embedding for empty text.")
            return None
        try:
            # Truncate text if it's too long for the model (e.g., some models have input limits like 512 tokens)
            # This is a basic truncation; more sophisticated chunking might be needed for very long texts.
            max_model_input_length = 10000  # Approximate characters, actual limit is token-based
            truncated_text = text[:max_model_input_length] if len(text) > max_model_input_length else text

            scraper_logger.debug(f"Generating embedding for text (length: {len(truncated_text)} chars).")
            embedding = self.model.encode(truncated_text, show_progress_bar=False) # show_progress_bar=False for non-interactive use
            return embedding.tolist()  # Convert numpy array to list for MongoDB storage
        except Exception as e:
            scraper_logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None

    def process_article(self, article_data: dict) -> dict | None:
        """
        Processes a single raw article dictionary from NewsAPI.
        This includes generating a unique ID, checking for duplicates,
        extracting full content, generating embeddings, and structuring the document.

        Args:
            article_data (dict): A dictionary representing a single article from NewsAPI.

        Returns:
            dict | None: A processed article document ready for MongoDB insertion,
                         or None if the article is skipped or fails processing.
        """
        try:
            title = article_data.get("title", "").strip()
            url = article_data.get("url", "").strip()
            source_name = article_data.get("source", {}).get("name", "Unknown")
            published_at_str = article_data.get("publishedAt", "")
            description = article_data.get("description", "")

            if not title or not url:
                scraper_logger.warning("Skipping article: missing title or URL.")
                return None

            # Generate a unique, deterministic ID for the article based on its URL.
            article_id = hashlib.md5(url.encode('utf-8')).hexdigest()

            # Check if an article with this ID (URL) already exists in the database.
            if self.collection.count_documents({"article_id": article_id}, limit=1) > 0:
                scraper_logger.info(f"Duplicate article skipped: '{title[:50]}...' (URL: {url})")
                self.stats['duplicates_skipped'] += 1
                return None

            # Extract full article content using newspaper3k.
            content = self.extract_full_content(url)
            # If full content extraction fails or is empty, use the description as a fallback (if available).
            if not content and description:
                scraper_logger.debug(f"Using description as fallback content for article: {title[:50]}...")
                content = description

            # Skip articles with insufficient content (e.g., less than 150 characters).
            # This helps filter out paywalled previews, error pages, or very short notices.
            min_content_length = 150
            if len(content) < min_content_length:
                scraper_logger.warning(f"Skipping article with insufficient content (length {len(content)} chars): '{title[:50]}...'")
                return None

            # Generate vector embeddings for the content and title.
            scraper_logger.debug(f"Generating embeddings for article: {title[:50]}...")
            content_embedding = self.generate_embedding(content)
            title_embedding = self.generate_embedding(title)

            # Parse 'publishedAt' string to a datetime object.
            published_at_dt = None
            if published_at_str:
                try:
                    # NewsAPI returns UTC timestamps in ISO 8601 format (e.g., "2023-01-01T12:00:00Z")
                    published_at_dt = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                except ValueError:
                    scraper_logger.warning(f"Could not parse 'publishedAt' date: '{published_at_str}' for article: {title[:50]}...")

            # Construct the article document to be stored in MongoDB.
            article_doc = {
                "article_id": article_id,  # Unique MD5 hash of the URL
                "title": title,
                "url": url,
                "source": source_name,
                "published_at": published_at_dt, # Store as datetime object for proper date queries
                "content": content,
                "description": description,     # Original description from NewsAPI
                "scraped_at": datetime.utcnow(),# Timestamp of when the article was scraped
                "processed": False,             # Flag indicating if AI analysis has been run (legacy, use processing_status)
                "processing_status": "pending", # Detailed status: pending, analyzed, analyzed_fallback, failed_analysis
                "content_hash": hashlib.md5(content.encode('utf-8')).hexdigest(), # MD5 hash of content for change detection
                "word_count": len(content.split()),
                "content_embedding": content_embedding, # Vector embedding of the article content
                "title_embedding": title_embedding,     # Vector embedding of the article title
                "data_source": "news_api"       # Indicates the origin of the data
            }
            self.stats['articles_processed_successfully'] += 1
            return article_doc
        except Exception as e:
            scraper_logger.error(f"Error processing article (URL: {article_data.get('url', 'N/A')}): {e}", exc_info=True)
            self.stats['processing_errors'] += 1
            return None
    def store_articles(self, articles_to_store: list[dict]) -> int:
        """
        Stores a list of processed article documents in MongoDB using bulk operations.

        Args:
            articles_to_store (list[dict]): A list of article documents to insert.

        Returns:
            int: The number of articles successfully inserted.
        """
        if not articles_to_store:
            scraper_logger.info("No articles provided to store_articles.")
            return 0

        # Filter out any None values that might have resulted from failed processing
        valid_articles = [doc for doc in articles_to_store if doc]
        if not valid_articles:
            scraper_logger.info("No valid articles to store after filtering.")
            return 0

        try:
            scraper_logger.info(f"Attempting to bulk insert {len(valid_articles)} articles into MongoDB...")
            # Prepare operations for bulk_write
            operations = [pymongo.InsertOne(doc) for doc in valid_articles]

            result = self.collection.bulk_write(operations, ordered=False) # ordered=False allows all valid inserts to proceed even if some fail (e.g., due to duplicate key if somehow not caught)

            inserted_count = result.inserted_count
            self.stats['articles_stored_in_db'] += inserted_count
            scraper_logger.info(f"Successfully stored {inserted_count} new articles in MongoDB.")

            # Log details about any write errors if they occurred
            if result.bulk_api_result.get('writeErrors'):
                self.stats['storage_errors'] += len(result.bulk_api_result['writeErrors'])
                scraper_logger.error(f"Errors during bulk write: {result.bulk_api_result['writeErrors']}")

            return inserted_count
        except pymongo.errors.BulkWriteError as bwe:
            # This exception is raised if ordered=True and an error occurs,
            # or for other reasons even with ordered=False.
            # Details are in bwe.details
            num_inserted = bwe.details.get('nInserted', 0)
            self.stats['articles_stored_in_db'] += num_inserted
            self.stats['storage_errors'] += len(bwe.details.get('writeErrors', []))
            scraper_logger.error(f"Bulk write error storing articles. Inserted: {num_inserted}. Errors: {bwe.details.get('writeErrors')}", exc_info=True)
            return num_inserted # Return how many were inserted before the error
        except Exception as e:
            scraper_logger.error(f"Unexpected error storing articles: {e}", exc_info=True)
            self.stats['storage_errors'] += len(valid_articles) # Assume all failed if general exception
            return 0

    def save_scraping_summary(self, articles_processed_list: list[dict]):
        """
        Saves a summary of the scraping process and a sample of articles to JSON files.
        These files can be used for logging, artifacts in CI/CD, or quick checks.

        Args:
            articles_processed_list (list[dict]): The list of articles that were processed (attempted, not necessarily all stored).
        """
        summary_path = os.path.join(DATA_DIR, 'scraping_summary.json')
        sample_path = os.path.join(DATA_DIR, 'articles_sample.json')

        self.stats['end_time'] = datetime.utcnow().isoformat()
        # Determine final status based on errors
        if self.stats['fetch_errors'] > 0 or self.stats['processing_errors'] > 0 or self.stats['storage_errors'] > 0:
            self.stats['status'] = 'completed_with_errors'
        else:
            self.stats['status'] = 'completed_successfully'

        # Prepare the summary document
        summary_doc = {
            'scraping_run_id': hashlib.md5(self.stats['start_time'].encode('utf-8')).hexdigest(),
            'timestamp_start': self.stats['start_time'],
            'timestamp_end': self.stats['end_time'],
            'duration_seconds': (datetime.fromisoformat(self.stats['end_time']) - datetime.fromisoformat(self.stats['start_time'])).total_seconds(),
            'statistics': self.stats,
            'categories_attempted': CATEGORIES,
            'topics_attempted': TOPICS,
            'sample_articles_processed_count': len(articles_processed_list), # Count of articles attempted
            'sample_articles_preview': [ # Preview of first few *processed* articles
                {
                    'title': art.get('title', 'N/A') if art else 'N/A',
                    'url': art.get('url', 'N/A') if art else 'N/A',
                    'source': art.get('source', 'N/A') if art else 'N/A',
                } for art in articles_processed_list[:10]
            ]
        }

        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_doc, f, indent=4, default=str)
            scraper_logger.info(f"Scraping summary saved to {summary_path}")
        except Exception as e:
            scraper_logger.error(f"Error saving scraping summary to {summary_path}: {e}", exc_info=True)

        # Prepare a sample of *processed* articles for another file
        stored_sample_data = []
        if articles_processed_list:
            sample_candidates = [art for art in articles_processed_list if art] # Filter out None values (failed processing)
            for art_doc in sample_candidates[:20]: # Limit sample size
                 stored_sample_data.append({
                        'title': art_doc.get('title'),
                        'url': art_doc.get('url'),
                        'source': art_doc.get('source'),
                        'content_preview': (art_doc.get('content', '')[:200] + '...') if art_doc.get('content') else '',
                        'has_content_embedding': art_doc.get('content_embedding') is not None,
                        'has_title_embedding': art_doc.get('title_embedding') is not None,
                 })
        try:
            with open(sample_path, 'w', encoding='utf-8') as f:
                json.dump(stored_sample_data, f, indent=4, default=str)
            scraper_logger.info(f"Scraped articles sample saved to {sample_path}")
        except Exception as e:
            scraper_logger.error(f"Error saving articles sample to {sample_path}: {e}", exc_info=True)

    def run_scraping_task_logic(self) -> dict:
        """
        The core logic for a single scraping run.
        Fetches articles from categories and topics, processes them, and stores them.

        Returns:
            dict: The statistics dictionary for this scraping run.
        """
        scraper_logger.info(f"Starting News API fetching task run. Categories: {CATEGORIES}, Topics: {TOPICS}")
        self.stats['status'] = 'running'

        all_fetched_raw_articles = [] # All articles as received from NewsAPI

        # Using ThreadPoolExecutor for concurrent fetching from NewsAPI
        # Max workers should be chosen carefully based on NewsAPI rate limits
        # and whether the client library handles rate limiting internally.
        # For NewsAPI free/developer tiers, sequential might be safer or very few workers.
        # Let's assume 2 workers for now for minor concurrency.
        # NewsAPI free tier: 100 requests per day. Developer: 1000/day.
        # Each category/topic is one request.
        num_requests = len(CATEGORIES) + len(TOPICS)
        scraper_logger.info(f"Preparing to make {num_requests} requests to NewsAPI.")

        with ThreadPoolExecutor(max_workers=2, thread_name_prefix='NewsAPIFetch') as executor:
            future_to_source = {} # To map future to its source (category/topic) for logging

            # Submit tasks for fetching top headlines by category
            for category in CATEGORIES:
                # Reducing page_size to get fewer articles per request, to stay within limits if testing.
                # NewsAPI free plan is very limited.
                future = executor.submit(self.fetch_top_headlines, category=category, page_size=10)
                future_to_source[future] = f"Category: {category}"

            # Submit tasks for fetching articles by topic query
            for topic in TOPICS:
                future = executor.submit(self.fetch_everything, query=topic, page_size=10)
                future_to_source[future] = f"Topic: {topic}"

            # Process futures as they complete
            for future in as_completed(future_to_source):
                source_info = future_to_source[future]
                try:
                    articles_batch = future.result() # This will be a list of article dicts
                    if articles_batch:
                        scraper_logger.info(f"Successfully fetched {len(articles_batch)} articles from {source_info}")
                        all_fetched_raw_articles.extend(articles_batch)
                    else:
                        scraper_logger.info(f"No articles returned from {source_info}")

                    # Update stats based on source type
                    if "Category" in source_info:
                         self.stats['categories_processed'] += 1
                    else: # Topic
                         self.stats['topics_processed'] += 1
                except Exception as exc: # Catch exceptions from the task itself
                    scraper_logger.error(f"{source_info} generated an exception during fetch: {exc}", exc_info=True)
                    self.stats['fetch_errors'] += 1 # Increment general fetch error for this source

        scraper_logger.info(f"Total raw articles fetched from NewsAPI: {len(all_fetched_raw_articles)} (Updated stats count: {self.stats['articles_found_from_api']})")

        # Process all fetched articles
        processed_article_docs = []
        if all_fetched_raw_articles:
            scraper_logger.info(f"Processing {len(all_fetched_raw_articles)} raw articles...")
            for article_data in all_fetched_raw_articles:
                # Optional: Add a small delay here if newspaper3k is hitting many unique domains rapidly
                # time.sleep(0.1) # Be kind to servers
                processed_doc = self.process_article(article_data)
                if processed_doc:
                    processed_article_docs.append(processed_doc)
            scraper_logger.info(f"Successfully processed {len(processed_article_docs)} articles out of {len(all_fetched_raw_articles)} raw articles.")
        else:
            scraper_logger.info("No raw articles fetched from API to process.")

        # Store the successfully processed articles in MongoDB
        if processed_article_docs:
            scraper_logger.info(f"Attempting to store {len(processed_article_docs)} processed articles in MongoDB.")
            self.store_articles(processed_article_docs) # This method updates self.stats['articles_stored_in_db']
        else:
            scraper_logger.info("No articles were processed successfully to be stored.")

        # Save summary files (regardless of errors, to capture stats)
        self.save_scraping_summary(processed_article_docs)

        scraper_logger.info(f"News API fetching task run finished. Final Stats: {json.dumps(self.stats, indent=2)}")
        return self.stats

def run_scraping_task() -> dict:
    """
    Main function to run the news scraping task.
    It initializes the NewsAPIFetcher and executes the scraping logic.
    If new articles are stored, it subsequently triggers the analysis task.

    This function is intended to be called by the Flask scheduler or a manual API trigger.

    Returns:
        dict: A dictionary containing statistics about the scraping run.
              Includes `analysis_triggered_result` if analysis was run.
    """
    scraper_logger.info("--- Initiating new scraping task run ---")

    # Fetch necessary configurations from environment variables
    news_api_key = os.getenv('NEWS_API_KEY')
    mongodb_uri = os.getenv('MONGODB_URI')

    if not news_api_key:
        scraper_logger.error("CRITICAL: NEWS_API_KEY environment variable not set. Scraping task cannot proceed.")
        return {"status": "error", "message": "NEWS_API_KEY not configured for scraper."}
    if not mongodb_uri:
        scraper_logger.error("CRITICAL: MONGODB_URI environment variable not set. Scraping task cannot proceed.")
        return {"status": "error", "message": "MONGODB_URI not configured for scraper."}

    start_run_time = time.time()
    try:
        fetcher = NewsAPIFetcher(news_api_key=news_api_key, mongodb_uri=mongodb_uri)
        scraping_stats = fetcher.run_scraping_task_logic() # This now returns the stats dict

        scraper_logger.info(f"Scraping task logic completed. Status: {scraping_stats.get('status')}, Articles Stored: {scraping_stats.get('articles_stored_in_db', 0)}")

        # If new articles were successfully stored by the scraper, trigger the analysis task.
        if scraping_stats.get('articles_stored_in_db', 0) > 0:
            scraper_logger.info(f"{scraping_stats['articles_stored_in_db']} new articles were stored. Triggering analysis task...")
            try:
                # Determine batch size for analysis from environment or use a default.
                analysis_batch_size = int(os.getenv('BATCH_SIZE_ANALYSIS', "10")) # Default 10

                # Call the analysis task. It will find 'pending' articles.
                # Consider if a more direct "analyze these specific new N articles" is needed in future.
                # For now, run_analysis_task processes a batch of any pending articles.
                analysis_stats = run_analysis_task(batch_size=analysis_batch_size)
                scraper_logger.info(f"Analysis task finished after scraping. Analysis status: {analysis_stats.get('status', 'unknown')}")
                scraping_stats['analysis_triggered_result'] = analysis_stats # Include analysis outcome in overall result
            except Exception as analysis_exc:
                scraper_logger.error(f"Error occurred while trying to trigger analysis task after scraping: {analysis_exc}", exc_info=True)
                scraping_stats['analysis_triggered_result'] = {"status": "error", "message": f"Failed to run analysis: {analysis_exc}"}
        else:
            scraper_logger.info("No new articles were stored in this run. Analysis task will not be triggered by scraper.")

        end_run_time = time.time()
        scraper_logger.info(f"--- Scraping task run completed in {end_run_time - start_run_time:.2f} seconds ---")
        return scraping_stats

    except ValueError as ve: # Catch configuration errors from NewsAPIFetcher init (e.g., missing keys)
        scraper_logger.error(f"Configuration error during scraping task setup: {ve}", exc_info=True)
        return {"status": "error", "message": str(ve), "details": "ValueError during NewsAPIFetcher initialization."}
    except Exception as e: # Catch any other unexpected errors during the scraping process
        scraper_logger.error(f"An unexpected error occurred during the main scraping task: {e}", exc_info=True)
        end_run_time = time.time()
        scraper_logger.info(f"--- Scraping task run failed after {end_run_time - start_run_time:.2f} seconds ---")
        return {"status": "error", "message": "An unexpected error occurred during scraping.", "details": str(e)}

# Example of how to run it directly (for testing purposes, not for Flask app use)
# if __name__ == "__main__":
#     print("Running scraper module directly for testing...")
#     # For direct execution, ensure .env is in flask_backend or vars are set.
#     # This assumes .env is in the same directory as this script if run directly.
#     # However, when run by Flask, app.py handles .env loading.
#     dotenv_path_local = os.path.join(os.path.dirname(__file__), '.env')
#     if os.path.exists(dotenv_path_local):
#         load_dotenv(dotenv_path_local)
#         print(f"Loaded .env file from {dotenv_path_local}")
#     else:
#         print(f"Warning: .env file not found at {dotenv_path_local}. "
#               "Ensure NEWS_API_KEY, MONGODB_URI, GOOGLE_API_KEY etc. are set in your environment for direct testing.")

#     results = run_scraping_task()
#     print("\n--- Scraping Task Direct Run Results ---")
#     print(json.dumps(results, indent=2, default=str))
#     if results.get("status") == "error":
#         sys.exit(1) # Exit with error code if scraping failed
#     sys.exit(0)
