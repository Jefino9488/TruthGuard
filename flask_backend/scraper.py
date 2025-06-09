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
# from newsapi import NewsApiClient # Comment out if NewsAPIFetcher handles this
import json # Added import
from .analyzer import run_analysis_task # Import the analysis task runner
from flask import current_app # Ensure current_app is imported
# Ensure os is imported - it's already imported at the top of the file
from scripts.scrape_news_enhanced import NewsAPIFetcher # Import the new fetcher

# The old scraper_logger and its specific directory setup are removed.
# Flask's current_app.logger is used in run_scraping_task.
# The external NewsAPIFetcher handles its own logging needs if run standalone,
# or uses the passed app_logger.

# Old constants related to the embedded scraper are removed.
# If CATEGORIES/TOPICS are needed for the Flask app's logic (e.g. to pass to the fetcher),
# they should be defined in Flask config or elsewhere as appropriate.

# Comment out or remove the old NewsAPIFetcher class definition
# class NewsAPIFetcher:
#    ... (entire old class definition) ...
# The old class definition (approx 450 lines) has been removed for brevity in this diff proposal.
# It started with: class NewsAPIFetcher:
# And ended with: return self.stats

def run_scraping_task():
    """
    # This function will be called by the APScheduler or a manual trigger.
    # It needs to operate within an application context if it accesses current_app.config
    # The scheduler in app.py already wraps calls in app_context.

    logger = current_app.logger # Use Flask app's logger
    logger.info("--- Initiating scheduled news scraping task via NewsAPIFetcher from scripts ---")

    try:
        news_key = current_app.config.get('NEWS_API_KEY_SCRAPER')
        mongo_db_uri = current_app.config.get('MONGODB_URI')

        if not news_key:
            logger.error("NEWS_API_KEY_SCRAPER not configured in Flask app.")
            return {"status": "error", "message": "NEWS_API_KEY_SCRAPER not configured."}
        if not mongo_db_uri:
            logger.error("MONGODB_URI not configured in Flask app.") # Should be caught by app init
            return {"status": "error", "message": "MONGODB_URI not configured."}

        # Use the imported NewsAPIFetcher
        fetcher = NewsAPIFetcher(
            news_api_key=news_key,
            mongo_uri=mongo_db_uri,
            app_logger=logger # Pass the Flask app's logger
        )

        scraped_stats = fetcher.run() # This now returns the stats dictionary

        # The external NewsAPIFetcher returns stats like:
        # { 'categories_processed': N, 'topics_processed': M, 'articles_found': X,
        #   'articles_stored': Y, 'duplicates_skipped': Z, 'errors': E }
        logger.info(f"NewsAPIFetcher task finished. Stats: {scraped_stats}")

        analysis_triggered_results = {} # Initialize
        # Key for articles stored from external fetcher is 'articles_stored'
        if scraped_stats.get('articles_stored', 0) > 0: # Check key from scripts.scrape_news_enhanced.NewsAPIFetcher.stats
            logger.info(f"Scraping stored {scraped_stats['articles_stored']} new articles. Triggering analysis task...")
            try:
                # Call the analysis task. Pass a relevant batch_size.
                num_new_articles = scraped_stats['articles_stored']
                # Use a configured batch size or a heuristic (e.g., number of new articles, capped)
                # Ensure 'ANALYSIS_DEFAULT_BATCH_SIZE' is a sensible name if you add it to config
                default_batch_size_for_analysis = current_app.config.get('ANALYSIS_DEFAULT_BATCH_SIZE', 20)
                analysis_batch_size = min(num_new_articles, default_batch_size_for_analysis)

                # run_analysis_task is imported from .analyzer at the top of the file
                analysis_triggered_results = run_analysis_task(batch_size=analysis_batch_size)
                logger.info(f"Analysis task call completed. Result: {analysis_triggered_results}")
            except Exception as e:
                logger.error(f"Failed to trigger or complete analysis task after scraping: {e}", exc_info=True)
                analysis_triggered_results = {"status": "error", "message": f"Analysis task failed: {str(e)}"}
        else:
            logger.info("No new articles stored by scraper. Analysis task not triggered.")

        return {
            "status": "success", # Overall status is success of scraping, analysis is separate
            "message": "Scraping task completed using NewsAPIFetcher from scripts.",
            "details": scraped_stats,
            "analysis_triggered_result": analysis_triggered_results
        }

    except Exception as e:
        logger.error(f"An error occurred during the NewsAPIFetcher (from scripts) scraping task: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

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
