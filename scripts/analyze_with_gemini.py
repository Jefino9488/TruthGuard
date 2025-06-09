#!/usr/bin/env python3
"""
Google Gemini AI Analysis for TruthGuard
Advanced bias detection and content analysis with vector embeddings
"""

import os
import json
import logging
import sys
import random
from datetime import datetime, timezone
import pymongo
from google import genai
from google.genai import types
from google.genai import errors
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis_reports/gemini_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log Python version for debugging
# logger.info(f"Python version: {sys.version}") # This will be logged by self.logger in __init__ if needed, or remains global for standalone

# Pydantic models for structured JSON response
class FactCheck(BaseModel):
    claim: str
    verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str

class BiasAnalysis(BaseModel):
    overall_score: float = Field(ge=0.0, le=1.0)
    political_leaning: str
    bias_indicators: list[str]
    language_bias: float = Field(ge=0.0, le=1.0)
    source_bias: float = Field(ge=0.0, le=1.0)
    framing_bias: float = Field(ge=0.0, le=1.0)

class MisinformationAnalysis(BaseModel):
    risk_score: float = Field(ge=0.0, le=1.0)
    fact_checks: list[FactCheck]
    red_flags: list[str]

class SentimentAnalysis(BaseModel):
    overall_sentiment: float = Field(ge=-1.0, le=1.0)
    emotional_tone: str
    key_phrases: list[str]

class CredibilityAssessment(BaseModel):
    overall_score: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    source_reliability: float = Field(ge=0.0, le=1.0)

class AnalysisResponse(BaseModel):
    bias_analysis: BiasAnalysis
    misinformation_analysis: MisinformationAnalysis
    sentiment_analysis: SentimentAnalysis
    credibility_assessment: CredibilityAssessment
    confidence: float = Field(ge=0.0, le=1.0)

class GeminiAnalyzer:
    def __init__(self, google_api_key: str, mongo_uri: str, app_logger=None):
        if app_logger:
            self.logger = app_logger
        else:
            # Configure a default logger for standalone use
            self.logger = logging.getLogger(__name__ + ".GeminiAnalyzer")
            if not self.logger.handlers: # Avoid adding multiple handlers
                os.makedirs('analysis_reports', exist_ok=True) # Ensure dir exists for standalone log
                log_file_handler = logging.FileHandler('analysis_reports/gemini_analyzer.log', mode='a')
                log_stream_handler = logging.StreamHandler()
                log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                log_file_handler.setFormatter(log_formatter)
                log_stream_handler.setFormatter(log_formatter)
                self.logger.addHandler(log_file_handler)
                self.logger.addHandler(log_stream_handler)
                self.logger.setLevel(logging.INFO)

        self.logger.info(f"Python version: {sys.version}") # Moved here

        # Configure Gemini client
        self.google_api_key = google_api_key
        if not self.google_api_key:
            self.logger.error("GOOGLE_API_KEY not provided to GeminiAnalyzer.")
            raise ValueError("GOOGLE_API_KEY is required for GeminiAnalyzer")
        self.client = genai.Client(api_key=self.google_api_key)

        # Initialize sentence transformer model for embeddings
        self.logger.info("Loading sentence transformer model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

        # MongoDB connection
        self.mongo_uri = mongo_uri
        if not self.mongo_uri:
            self.logger.error("MONGODB_URI not provided to GeminiAnalyzer.")
            raise ValueError("MONGODB_URI is required for GeminiAnalyzer")
        self.mongo_client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.mongo_client.truthguard
        self.collection = self.db.articles

        # Create directories - analysis_results for output files, analysis_reports for logs (handled by logger setup)
        os.makedirs('analysis_results', exist_ok=True)
        # os.makedirs('analysis_reports', exist_ok=True) # Handled by logger setup if standalone

        # Statistics
        self.stats = {
            'articles_analyzed': 0,
            'high_bias_detected': 0,
            'misinformation_flagged': 0,
            'embeddings_generated': 0,
            'processing_errors': 0
        }

    def generate_embedding(self, text):
        """Generate vector embedding for text using sentence-transformers"""
        try:
            max_length = 10000
            if len(text) > max_length:
                text = text[:max_length]
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return None

    def analyze_article_comprehensive(self, article, max_retries=3):
        """Comprehensive analysis using Gemini AI with retry logic"""
        for attempt in range(max_retries):
            try:
                prompt = f"""
                You are TruthGuard AI, an expert media bias and misinformation detection system.

                Analyze this news article comprehensively:

                Title: {article['title']}
                Source: {article['source']}
                Content: {article['content'][:8000]}
                """
                content = types.Content(
                    role='user',
                    parts=[types.Part.from_text(text=prompt)]
                )

                # Estimate token usage
                token_count = self.client.models.count_tokens(
                    model='gemini-2.0-flash-001',
                    contents=content
                ).total_tokens
                self.logger.debug(f"Estimated tokens for article {article['_id']}: {token_count}")

                response = self.client.models.generate_content(
                    model='gemini-2.0-flash-001',
                    contents=content,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json',
                        response_schema=AnalysisResponse,
                        temperature=0.3,
                        max_output_tokens=2000,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    )
                )

                try:
                    analysis = json.loads(response.text)
                    update_fields = {
                        'ai_analysis': analysis,
                        'bias_score': analysis['bias_analysis']['overall_score'],
                        'misinformation_risk': analysis['misinformation_analysis']['risk_score'],
                        'sentiment': analysis['sentiment_analysis']['overall_sentiment'],
                        'credibility_score': analysis['credibility_assessment']['overall_score'],
                        'processing_status': 'analyzed',
                        'analyzed_at': datetime.now(timezone.utc),
                        'analysis_model': 'gemini-2.0-flash-001'
                    }

                    if 'content_embedding' not in article or article['content_embedding'] is None:
                        content_embedding = self.generate_embedding(article['content'])
                        if content_embedding:
                            update_fields['content_embedding'] = content_embedding
                            self.stats['embeddings_generated'] += 1

                    if 'title_embedding' not in article or article['title_embedding'] is None:
                        title_embedding = self.generate_embedding(article['title'])
                        if title_embedding:
                            update_fields['title_embedding'] = title_embedding
                            self.stats['embeddings_generated'] += 1

                    analysis_text = f"{analysis['bias_analysis']['political_leaning']} {' '.join(analysis['bias_analysis']['bias_indicators'])} {' '.join(analysis['misinformation_analysis']['red_flags'])} {analysis['sentiment_analysis']['emotional_tone']}"
                    analysis_embedding = self.generate_embedding(analysis_text)
                    if analysis_embedding:
                        update_fields['analysis_embedding'] = analysis_embedding
                        self.stats['embeddings_generated'] += 1

                    self.collection.update_one(
                        {'_id': article['_id']},
                        {'$set': update_fields}
                    )

                    self.stats['articles_analyzed'] += 1
                    if analysis['bias_analysis']['overall_score'] > 0.7:
                        self.stats['high_bias_detected'] += 1
                    if analysis['misinformation_analysis']['risk_score'] > 0.6:
                        self.stats['misinformation_flagged'] += 1

                    self.logger.info(f"Analyzed: {article['title'][:50]}...")
                    return analysis

                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse Gemini response for article {article['_id']}")
                    return self.generate_fallback_analysis(article)

            except errors.APIError as e:
                if e.code in [429, 503]: # Retriable errors
                    wait_time = 5 * (2 ** attempt) + random.uniform(0, 1) # Exponential backoff with jitter
                    self.logger.warning(f"Retrying article {article['_id']} (attempt {attempt + 1}/{max_retries}) after {wait_time:.2f}s due to API error: {e.code} - {e.message}")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        self.logger.error(f"Max retries reached for article {article['_id']}. API error: {e.code} - {e.message}")
                        self.stats['processing_errors'] += 1
                        return self.generate_fallback_analysis(article) # Fallback after max retries
                else: # Non-retriable API errors
                    self.logger.error(f"Non-retriable Gemini API error for article {article['_id']}: {e.code} - {e.message}")
                    self.stats['processing_errors'] += 1
                    return self.generate_fallback_analysis(article)
            except Exception as e: # Catch any other unexpected errors
                self.logger.error(f"Unexpected error analyzing article {article['_id']}: {e}", exc_info=True)
                self.stats['processing_errors'] += 1
                return self.generate_fallback_analysis(article) # Fallback for other errors
        return None # Should only be reached if all retries failed for a retriable error

    def generate_fallback_analysis(self, article):
        """Generate fallback analysis when Gemini fails"""
        content = article['content'].lower()
        bias_keywords = {
            'left': ['progressive', 'liberal', 'social justice', 'inequality'],
            'right': ['conservative', 'traditional', 'free market', 'law and order']
        }

        left_score = sum(1 for word in bias_keywords['left'] if word in content)
        right_score = sum(1 for word in bias_keywords['right'] if word in content)
        bias_score = min((left_score + right_score) / 10, 1.0)

        analysis = {
            'bias_analysis': {
                'overall_score': bias_score,
                'political_leaning': 'center',
                'bias_indicators': [],
                'language_bias': bias_score,
                'source_bias': 0.3,
                'framing_bias': bias_score * 0.8
            },
            'misinformation_analysis': {
                'risk_score': 0.3,
                'fact_checks': [],
                'red_flags': []
            },
            'sentiment_analysis': {
                'overall_sentiment': 0.0,
                'emotional_tone': 'neutral',
                'key_phrases': []
            },
            'credibility_assessment': {
                'overall_score': 0.7,
                'evidence_quality': 0.6,
                'source_reliability': 0.7
            },
            'confidence': 0.5
        }

        update_fields = {
            'ai_analysis': analysis,
            'bias_score': analysis['bias_analysis']['overall_score'],
            'misinformation_risk': analysis['misinformation_analysis']['risk_score'],
            'sentiment': analysis['sentiment_analysis']['overall_sentiment'],
            'credibility_score': analysis['credibility_assessment']['overall_score'],
            'processing_status': 'analyzed_fallback',
            'analyzed_at': datetime.now(timezone.utc),
            'analysis_model': 'fallback'
        }

        if 'content_embedding' not in article or article['content_embedding'] is None:
            content_embedding = self.generate_embedding(article['content'])
            if content_embedding:
                update_fields['content_embedding'] = content_embedding
                self.stats['embeddings_generated'] += 1

        if 'title_embedding' not in article or article['title_embedding'] is None:
            title_embedding = self.generate_embedding(article['title'])
            if content_embedding:
                update_fields['title_embedding'] = title_embedding
                self.stats['embeddings_generated'] += 1

        analysis_text = f"center neutral fallback analysis"
        analysis_embedding = self.generate_embedding(analysis_text)
        if analysis_embedding:
            update_fields['analysis_embedding'] = analysis_embedding
            self.stats['embeddings_generated'] += 1

        self.collection.update_one(
            {'_id': article['_id']},
            {'$set': update_fields}
        )

        return analysis

    def run_batch_analysis(self, batch_size=50):
        """Run analysis on unprocessed articles"""
        self.logger.info("Starting Gemini AI batch analysis...")

        unprocessed = list(self.collection.find({
            'processing_status': {'$in': ['pending', None, 'failed_analysis']} # Include previously failed ones
        }).limit(batch_size))

        self.logger.info(f"Found {len(unprocessed)} articles to analyze (pending, None, or failed_analysis).")

        with ThreadPoolExecutor(max_workers=1) as executor: # Gemini API limits might restrict higher concurrency
            future_to_article = {
                executor.submit(self.analyze_article_comprehensive, article): article
                for article in unprocessed
            }

            for future in as_completed(future_to_article):
                article_data = future_to_article[future]
                try:
                    analysis_result = future.result()
                    if analysis_result:
                        self.logger.debug(f"Successfully processed article ID: {article_data['_id']}")
                    else:
                        # This case might happen if generate_fallback_analysis also somehow fails or if max retries are exhausted
                        self.logger.warning(f"Analysis returned no result for article ID: {article_data['_id']}, likely due to max retries or fallback failure.")
                    # Apply rate limiting if necessary, e.g., if not handled by client library or if using a sensitive tier
                    time.sleep(1) # Basic delay between processing results; adjust based on API limits
                except Exception as e:
                    self.logger.error(f"Error processing future for article ID {article_data.get('_id', 'Unknown')}: {e}", exc_info=True)
                    self.stats['processing_errors'] += 1 # Ensure errors in future processing are counted

        self.save_analysis_summary()
        self.logger.info(f"Analysis batch complete. Stats: {self.stats}")
        return self.stats # Return the statistics dictionary

    def save_analysis_summary(self):
        """Save analysis summary for GitLab artifacts"""
        summary = {
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'statistics': self.stats,
            'model_used': 'gemini-2.0-flash-001',
            'embedding_model': 'all-MiniLM-L6-v2',
            'embedding_dimensions': 384,
            'analysis_version': '3.0',
            'vector_search_enabled': True
        }

        embedding_stats = {
            'total_embeddings_generated': self.stats['embeddings_generated'],
            'embedding_types': ['content_embedding', 'title_embedding', 'analysis_embedding'],
            'embedding_model_info': {
                'name': 'all-MiniLM-L6-v2',
                'dimensions': 384,
                'similarity_metric': 'cosine'
            }
        }
        summary['embedding_stats'] = embedding_stats

        with open('analysis_results/gemini_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        self.logger.info("Analysis summary saved with embedding statistics")

if __name__ == "__main__":
    load_dotenv('.env.local') # Load .env for standalone run

    google_key = os.getenv('GOOGLE_API_KEY')
    mongo_connection_string = os.getenv('MONGODB_URI')

    if not google_key:
        print("Error: GOOGLE_API_KEY environment variable not set for standalone run.")
        sys.exit(1)
    if not mongo_connection_string:
        print("Error: MONGODB_URI environment variable not set for standalone run.")
        sys.exit(1)

    # This will use the global logger configured at the top of the file
    standalone_logger = logging.getLogger(__name__)

    analyzer = GeminiAnalyzer(google_api_key=google_key, mongo_uri=mongo_connection_string, app_logger=standalone_logger)
    analyzer.run_batch_analysis()