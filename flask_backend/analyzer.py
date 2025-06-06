#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Analysis Module for TruthGuard Backend.

This module uses Google's Gemini Pro model via the 'google-generativeai'
library to perform various analyses on news articles. It includes:
- Comprehensive analysis covering bias, misinformation, sentiment, and credibility.
- Generation of vector embeddings for content, title, and analysis text.
- Structured Pydantic models for the analysis response.
- Fallback mechanisms if AI analysis fails.
- Batch processing of articles fetched from MongoDB.

The main entry point for analysis tasks is `run_analysis_task()`.
Pydantic models define the expected structure for AI responses.
"""

import os
import json
import logging
import sys
import random
from datetime import datetime, timezone
import pymongo
from google import genai
from google.genai import types as google_types # Renamed to avoid conflict with 'types' module
from google.genai import errors as google_errors # Renamed
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv # Keep for now, might be redundant if Flask handles it
from pydantic import BaseModel, Field, ValidationError

# Configure logging - paths will be relative to flask_backend
LOG_DIR = 'analysis_reports'
RESULTS_DIR = 'analysis_results'

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Configure logging for this module.
# This logger will write to its own file 'gemini_analysis.log' and will not
# propagate messages to the main app logger by default if app.py's logger is also named `__name__`.
# Using a specific name for this logger ensures its independence if needed.
analyzer_logger = logging.getLogger(__name__) # Logger named after the module: 'flask_backend.analyzer'
analyzer_logger.setLevel(logging.INFO) # Default level

# File Handler for analyzer-specific logs
analyzer_file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'gemini_analysis.log'), mode='a')
analyzer_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
analyzer_logger.addHandler(analyzer_file_handler)

# Optional: Console Handler for analyzer logs (can be verbose)
# analyzer_stream_handler = logging.StreamHandler()
# analyzer_stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# analyzer_logger.addHandler(analyzer_stream_handler)

analyzer_logger.propagate = False # Avoid duplicate logs if root logger is also configured


# --- Pydantic Models for Structured AI Analysis Response ---
# These models define the expected JSON structure for the analysis results from Gemini.
# They include default values and type validation.
class FactCheck(BaseModel):
    """Represents a single fact-check claim and its verdict."""
    claim: str = "N/A"
    verdict: str = "N/A"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = "N/A"

class BiasAnalysis(BaseModel):
    """Represents the bias analysis of an article."""
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall bias score, 0 (low) to 1 (high)")
    political_leaning: str = Field(default="center", description="Detected political leaning (e.g., left, right, center, moderate)")
    bias_indicators: list[str] = Field(default=[], description="List of specific phrases or indicators of bias found")
    language_bias: float = Field(default=0.0, ge=0.0, le=1.0, description="Score for language-specific bias")
    source_bias: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated bias of the source")
    framing_bias: float = Field(default=0.0, ge=0.0, le=1.0, description="Score for framing or presentation bias")

class MisinformationAnalysis(BaseModel):
    """Represents the misinformation analysis of an article."""
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall misinformation risk, 0 (low) to 1 (high)")
    fact_checks: list[FactCheck] = Field(default=[], description="List of fact-checks related to claims in the article")
    red_flags: list[str] = Field(default=[], description="List of detected misinformation red flags or questionable claims")

class SentimentAnalysis(BaseModel):
    """Represents the sentiment analysis of an article."""
    overall_sentiment: float = Field(default=0.0, ge=-1.0, le=1.0, description="Overall sentiment score, -1 (negative) to 1 (positive)")
    emotional_tone: str = Field(default="neutral", description="Predominant emotional tone (e.g., neutral, angry, joyful)")
    key_phrases: list[str] = Field(default=[], description="Key phrases contributing to the sentiment")

class CredibilityAssessment(BaseModel):
    """Represents the credibility assessment of an article."""
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall credibility score, 0 (low) to 1 (high)")
    evidence_quality: float = Field(default=0.0, ge=0.0, le=1.0, description="Assessed quality of evidence presented")
    source_reliability: float = Field(default=0.0, ge=0.0, le=1.0, description="Assessed reliability of the source")

class AnalysisResponse(BaseModel):
    """The overall structured response from the AI analysis."""
    bias_analysis: BiasAnalysis = Field(default_factory=BiasAnalysis)
    misinformation_analysis: MisinformationAnalysis = Field(default_factory=MisinformationAnalysis)
    sentiment_analysis: SentimentAnalysis = Field(default_factory=SentimentAnalysis)
    credibility_assessment: CredibilityAssessment = Field(default_factory=CredibilityAssessment)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall confidence in the analysis, 0 (low) to 1 (high)")


class GeminiAnalyzer:
    """
    Handles AI-powered analysis of news articles using Google's Gemini model.

    This class is responsible for:
    - Connecting to Google Gemini API.
    - Connecting to MongoDB to fetch articles and store analysis results.
    - Generating vector embeddings for text.
    - Performing comprehensive analysis (bias, misinformation, etc.).
    - Handling API errors and providing fallback analysis if needed.
    - Managing batch processing of articles.
    """
    def __init__(self, google_api_key: str, mongodb_uri: str):
        """
        Initializes the GeminiAnalyzer.

        Args:
            google_api_key (str): API key for Google Gemini.
            mongodb_uri (str): Connection URI for MongoDB.

        Raises:
            ValueError: If API keys or URI are missing.
        """
        if not google_api_key:
            analyzer_logger.error("CRITICAL: GOOGLE_API_KEY not provided to GeminiAnalyzer constructor.")
            raise ValueError("GOOGLE_API_KEY is required for GeminiAnalyzer.")
        genai.configure(api_key=google_api_key)
        self.genai_model_name = 'gemini-1.5-flash-latest' # Specify the Gemini model to use
        analyzer_logger.info(f"Google Gemini client configured with model: {self.genai_model_name}")

        analyzer_logger.info("Loading sentence transformer model 'all-MiniLM-L6-v2' for embeddings...")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2') # 384-dim embeddings
        except Exception as e:
            analyzer_logger.error(f"Failed to load SentenceTransformer model: {e}. Ensure it's installed.", exc_info=True)
            raise

        if not mongodb_uri:
            analyzer_logger.error("CRITICAL: MONGODB_URI not provided to GeminiAnalyzer constructor.")
            raise ValueError("MONGODB_URI is required for GeminiAnalyzer.")
        analyzer_logger.info("Connecting to MongoDB for analyzer...")
        self.mongo_client = pymongo.MongoClient(mongodb_uri)
        self.db = self.mongo_client.truthguard       # Database name
        self.collection = self.db.articles          # Collection for articles
        analyzer_logger.info("MongoDB connection for analyzer established.")

        # Statistics for the current analysis run
        self.stats = {
            'start_time': datetime.utcnow().isoformat(),
            'end_time': None,
            'articles_processed_for_analysis': 0, # Number of articles attempted
            'articles_successfully_analyzed': 0,  # Number of articles successfully analyzed by Gemini
            'fallback_analyses_used': 0,          # Number of times fallback analysis was used
            'high_bias_detected': 0,              # Articles flagged with high bias score
            'misinformation_flagged': 0,          # Articles flagged with high misinformation risk
            'embeddings_generated_during_analysis': 0, # Count of new embeddings created
            'processing_errors': 0,               # Errors during Pydantic validation or other local processing
            'api_retries': 0,                     # Number of retries made to Gemini API
            'status': 'pending'                   # Overall status of the analysis task
        }

    def generate_embedding(self, text: str) -> list[float] | None:
        """
        Generates a vector embedding for the given text.

        Args:
            text (str): The text to embed.

        Returns:
            list[float] | None: The embedding vector, or None if an error occurs.
        """
        if not text:
            analyzer_logger.warning("Attempted to generate embedding for empty text in analyzer.")
            return None
        try:
            # Using a common model, all-MiniLM-L6-v2, which has a max sequence length of 256 tokens.
            # SentenceTransformer handles truncation, but good to be aware.
            # For longer texts, consider chunking strategies if full context is vital beyond model's limit.
            analyzer_logger.debug(f"Generating embedding for text (approx length: {len(text)} chars).")
            embedding = self.embedding_model.encode(text, show_progress_bar=False)
            return embedding.tolist()
        except Exception as e:
            analyzer_logger.error(f"Error generating embedding in analyzer: {e}", exc_info=True)
            return None

    def analyze_article_comprehensive(self, article_doc: dict, max_retries: int = 2) -> dict | None:
        """
        Performs comprehensive AI analysis on a single article document using Gemini.
        Includes retry logic for API calls and fallback mechanism.

        Args:
            article_doc (dict): The article document from MongoDB.
            max_retries (int): Maximum number of retries for Gemini API calls.

        Returns:
            dict | None: The AI analysis result (dictionary parsed from AnalysisResponse model),
                         or None if analysis fails definitively after retries.
        """
        self.stats['articles_processed_for_analysis'] += 1
        article_id_str = str(article_doc.get('_id', 'UnknownID'))
        analyzer_logger.info(f"Attempting AI analysis for article ID: {article_id_str} - Title: '{article_doc.get('title', 'N/A')[:60]}...'")

        # Truncate content for the prompt to avoid excessive length, Gemini 1.5 Flash has a large context window.
        # The model itself will also truncate based on its token limit.
        content_for_prompt = article_doc.get('content', '')[:20000] # Approx first 20k chars

        # Construct the prompt for Gemini API
        prompt = f"""
Analyze the following news article comprehensively for bias, misinformation, sentiment, and credibility.
Focus on identifying specific indicators and providing scores where applicable (0.0 for low, 1.0 for high).

Article Title: {article_doc.get('title', '')}
Article Source: {article_doc.get('source', '')}
Article Content:
{content_for_prompt}

Return your analysis STRICTLY as a JSON object matching this Pydantic schema:
{AnalysisResponse.model_json_schema(indent=2)}

Ensure all fields in the schema are present in your JSON output.
Output JSON only, with no other text before or after the JSON object.
"""
        # Configuration for Gemini API call
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json", # Expect JSON response
            temperature=0.2,                      # Lower temperature for more factual/deterministic responses
            max_output_tokens=8192                # Max tokens for the response (Gemini 1.5 Flash can handle large outputs)
        )

        # Safety settings to configure content blocking by Gemini
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        for attempt in range(max_retries + 1): # attempts = max_retries + initial try
            try:
                analyzer_logger.debug(f"Gemini API call attempt {attempt + 1}/{max_retries + 1} for article ID: {article_id_str}")
                model_to_use = genai.GenerativeModel(self.genai_model_name)
                response = model_to_use.generate_content(
                    contents=prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )

                # Validate response: Check for empty candidates or blocked content
                if not response.candidates or not response.candidates[0].content.parts:
                    block_reason = "Unknown"
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        block_reason = response.prompt_feedback.block_reason.name
                    analyzer_logger.warning(f"Gemini response empty or blocked for article {article_id_str}. Reason: {block_reason}. Attempt {attempt + 1}")
                    if block_reason == "SAFETY": # If blocked for safety, don't retry with same prompt.
                        raise google_errors.BlockedPromptError(f"Content blocked due to safety settings: {block_reason}")
                    if attempt < max_retries: # Retry for non-safety blocks if retries left
                        time.sleep((2 ** attempt) + random.uniform(0, 1)) # Exponential backoff
                        self.stats['api_retries'] += 1
                        continue
                    else: # Max retries reached for non-safety block
                        analyzer_logger.error(f"Max retries reached for article {article_id_str} due to empty/blocked response (non-safety).")
                        return self.generate_fallback_analysis(article_doc, f"BlockedOrEmptyResponse-{block_reason}")

                analysis_json_str = response.text # Gemini should return a JSON string directly based on response_mime_type

                try:
                    # Validate and parse the JSON response using Pydantic model
                    analysis_data = AnalysisResponse.model_validate_json(analysis_json_str)
                    analysis = analysis_data.model_dump() # Convert Pydantic model to dict for MongoDB
                except ValidationError as ve:
                    analyzer_logger.error(f"Pydantic validation failed for article {article_id_str}: {ve}. Response snippet: {analysis_json_str[:500]}...", exc_info=False)
                    self.stats['processing_errors'] += 1
                    if attempt < max_retries: # Retry if validation fails and retries are left
                        analyzer_logger.info(f"Retrying Pydantic validation failure for article {article_id_str}, attempt {attempt + 1}")
                        time.sleep((2 ** attempt) + random.uniform(0, 1))
                        self.stats['api_retries'] +=1 # Count this as an API retry as we'll call it again
                        continue
                    analyzer_logger.error(f"Max retries reached for Pydantic validation, using fallback for article {article_id_str}.")
                    return self.generate_fallback_analysis(article_doc, "PydanticValidationError")

                # Prepare fields to update in MongoDB
                update_fields = {
                    'ai_analysis': analysis, # Store the full structured analysis
                    'bias_score': analysis.get('bias_analysis', {}).get('overall_score'),
                    'misinformation_risk': analysis.get('misinformation_analysis', {}).get('risk_score'),
                    'sentiment': analysis.get('sentiment_analysis', {}).get('overall_sentiment'),
                    'credibility_score': analysis.get('credibility_assessment', {}).get('overall_score'),
                    'processing_status': 'analyzed',
                    'analyzed_at': datetime.now(timezone.utc),
                    'analysis_model': self.genai_model_name
                }

                # Generate embeddings for content and title if they don't already exist
                if not article_doc.get('content_embedding'):
                    content_embedding = self.generate_embedding(article_doc.get('content', ''))
                    if content_embedding:
                        update_fields['content_embedding'] = content_embedding
                        self.stats['embeddings_generated_during_analysis'] += 1
                if not article_doc.get('title_embedding'):
                    title_embedding = self.generate_embedding(article_doc.get('title', ''))
                    if title_embedding:
                        update_fields['title_embedding'] = title_embedding
                        self.stats['embeddings_generated_during_analysis'] += 1

                # Generate an embedding for key textual parts of the analysis itself
                analysis_text_parts = [
                    analysis.get('bias_analysis', {}).get('political_leaning', ''),
                    *analysis.get('bias_analysis', {}).get('bias_indicators', []),
                    *analysis.get('misinformation_analysis', {}).get('red_flags', []),
                    analysis.get('sentiment_analysis', {}).get('emotional_tone', '')
                ]
                analysis_text_combined = " ".join(filter(None, analysis_text_parts)).strip()
                if analysis_text_combined:
                    analysis_embedding = self.generate_embedding(analysis_text_combined)
                    if analysis_embedding:
                        update_fields['analysis_embedding'] = analysis_embedding
                        self.stats['embeddings_generated_during_analysis'] += 1

                # Update the document in MongoDB
                self.collection.update_one({'_id': article_doc['_id']}, {'$set': update_fields})
                self.stats['articles_successfully_analyzed'] += 1
                # Update high-level stats based on analysis scores
                if analysis.get('bias_analysis', {}).get('overall_score', 0) > 0.7: self.stats['high_bias_detected'] += 1
                if analysis.get('misinformation_analysis', {}).get('risk_score', 0) > 0.6: self.stats['misinformation_flagged'] += 1

                analyzer_logger.info(f"Successfully analyzed and updated article ID: {article_id_str}")
                return analysis # Success

            except (google_errors.DeadlineExceededError, google_errors.InternalServerError,
                    google_errors.ResourceExhaustedError, google_errors.ServiceUnavailableError) as e:
                analyzer_logger.warning(f"Gemini API call failed (Attempt {attempt + 1}/{max_retries + 1}) for article {article_id_str}: {type(e).__name__} - {e}")
                self.stats['api_retries'] += 1
                if attempt == max_retries: # Last attempt failed
                    analyzer_logger.error(f"Max retries reached for article {article_id_str} due to API error: {type(e).__name__}.")
                    self.stats['processing_errors'] += 1 # Mark as processing error as analysis failed
                    return self.generate_fallback_analysis(article_doc, f"GeminiAPIError-{type(e).__name__}")
                # Exponential backoff with jitter before retrying
                time.sleep(random.uniform(1, 3) * (2 ** attempt))
            except google_errors.BlockedPromptError as e: # Handle content blocking specifically
                analyzer_logger.error(f"Gemini prompt blocked for article {article_id_str} due to safety/other settings: {e}")
                self.stats['processing_errors'] += 1
                return self.generate_fallback_analysis(article_doc, "GeminiBlockedPromptError")
            except Exception as e: # Catch any other unexpected errors
                analyzer_logger.error(f"Unexpected error analyzing article {article_id_str} (Attempt {attempt + 1}/{max_retries + 1}): {e}", exc_info=True)
                self.stats['processing_errors'] += 1
                if attempt == max_retries: # Last attempt failed
                    return self.generate_fallback_analysis(article_doc, f"UnexpectedError-{type(e).__name__}")
                time.sleep((2 ** attempt) + random.uniform(0, 1)) # Backoff before retrying

        analyzer_logger.error(f"AI analysis failed for article {article_id_str} after all retries and error handling.")
        # This line should ideally not be reached if fallback is always returned, but as a safeguard:
        return self.generate_fallback_analysis(article_doc, "MaxRetriesOrUnhandledPath")

    def generate_fallback_analysis(self, article_doc: dict, reason: str = "UnknownError") -> dict:
        """
        Generates a fallback analysis structure when the primary AI analysis fails.
        This ensures that the article record is still updated and marked appropriately.

        Args:
            article_doc (dict): The original article document.
            reason (str): A brief reason why fallback is being used (e.g., "GeminiAPIError", "PydanticValidationError").

        Returns:
            dict: A dictionary containing the fallback analysis data.
        """
        analyzer_logger.warning(f"Using fallback analysis for article ID: {str(article_doc.get('_id'))} due to: {reason}")
        self.stats['fallback_analyses_used'] += 1

        # Create a default AnalysisResponse Pydantic model and convert to dict
        # This ensures a consistent structure even for fallback data.
        fallback_response = AnalysisResponse(
            bias_analysis=BiasAnalysis(political_leaning=f"center (fallback - {reason[:20]})"), # Truncate reason
            misinformation_analysis=MisinformationAnalysis(risk_score=0.1), # Default low risk
            sentiment_analysis=SentimentAnalysis(emotional_tone=f"neutral (fallback - {reason[:20]})"),
            credibility_assessment=CredibilityAssessment(overall_score=0.3), # Default low credibility
            confidence=0.1 # Very low confidence for fallback
        )
        analysis_dict = fallback_response.model_dump()

        update_fields = {
            'ai_analysis': analysis_dict,
            'bias_score': analysis_dict['bias_analysis']['overall_score'],
            'misinformation_risk': analysis_dict['misinformation_analysis']['risk_score'],
            'sentiment': analysis_dict['sentiment_analysis']['overall_sentiment'],
            'credibility_score': analysis_dict['credibility_assessment']['overall_score'],
            'processing_status': 'analyzed_fallback', # Mark as analyzed with fallback
            'analyzed_at': datetime.now(timezone.utc),
            'analysis_model': f'fallback ({reason})' # Note the reason for fallback
        }

        # Attempt to generate embeddings even in fallback if they are missing
        if not article_doc.get('content_embedding'):
            content_embedding = self.generate_embedding(article_doc.get('content', ''))
            if content_embedding:
                update_fields['content_embedding'] = content_embedding
                self.stats['embeddings_generated_during_analysis'] += 1
        if not article_doc.get('title_embedding'):
            title_embedding = self.generate_embedding(article_doc.get('title', ''))
            if title_embedding:
                update_fields['title_embedding'] = title_embedding
                self.stats['embeddings_generated_during_analysis'] += 1

        # Update the document in MongoDB with fallback analysis
        try:
            self.collection.update_one({'_id': article_doc['_id']}, {'$set': update_fields})
            analyzer_logger.info(f"Fallback analysis applied and DB updated for article ID: {str(article_doc.get('_id'))}")
        except Exception as e:
            analyzer_logger.error(f"Error updating article with fallback analysis (ID: {str(article_doc.get('_id'))}): {e}", exc_info=True)
            self.stats['processing_errors'] +=1 # Count as a processing error if DB update fails for fallback

        return analysis_dict

    def run_batch_analysis(self, batch_size: int = 10, query_filter: dict = None) -> dict:
        """
        Runs AI analysis on a batch of unprocessed articles from MongoDB.

        Args:
            batch_size (int): The number of articles to process in this batch. Default is 10.
            query_filter (dict, optional): Custom MongoDB query filter to select articles.
                                          Defaults to fetching articles with 'pending' or similar statuses.

        Returns:
            dict: Statistics for this analysis batch run.
        """
        analyzer_logger.info(f"Starting AI analysis batch run. Batch size: {batch_size}")
        self.stats['status'] = 'running'

        if query_filter is None:
            # Default filter: select articles that are pending, failed previously, or never analyzed.
            query_filter = {'processing_status': {'$in': ['pending', 'failed_analysis', None, 'pending_analysis']}}

        analyzer_logger.debug(f"Using query filter for fetching articles: {query_filter}")

        try:
            unprocessed_articles = list(self.collection.find(query_filter).limit(batch_size))
            analyzer_logger.info(f"Found {len(unprocessed_articles)} articles matching filter criteria for analysis batch.")
        except Exception as e:
            analyzer_logger.error(f"Error fetching articles for analysis batch: {e}", exc_info=True)
            self.stats['status'] = 'error_db_fetch'
            self.stats['processing_errors'] +=1
            return self.stats


        if not unprocessed_articles:
            analyzer_logger.info("No articles found to analyze in this batch.")
            self.stats['status'] = 'completed_no_articles_found'
            self.stats['end_time'] = datetime.utcnow().isoformat()
            self.save_analysis_summary() # Save summary even if no articles
            return self.stats

        # Using ThreadPoolExecutor for concurrent API calls (if max_workers > 1).
        # Gemini API has RPM limits (e.g., 60 RPM for gemini-1.5-flash).
        # Set max_workers=1 to process sequentially to respect potential strict RPM limits
        # and avoid overwhelming the API or local resources if analysis is CPU-intensive.
        # Can be increased with careful monitoring and if the API plan allows higher concurrency.
        max_workers = 1
        analyzer_logger.info(f"Processing analysis batch with max_workers={max_workers}.")

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='GeminiAnalyze') as executor:
            # Submit analysis tasks for each article
            future_to_article_id = {
                executor.submit(self.analyze_article_comprehensive, article): str(article.get('_id'))
                for article in unprocessed_articles
            }

            # Process results as they complete
            for future in as_completed(future_to_article_id):
                article_id_str = future_to_article_id[future]
                try:
                    analysis_result = future.result() # This will be the analysis dict or None
                    if analysis_result:
                        analyzer_logger.info(f"Successfully processed (or applied fallback) for article ID: {article_id_str}")
                    else:
                        # This case should be rare if fallback always returns a dict.
                        analyzer_logger.warning(f"No analysis result (None) returned for article ID: {article_id_str}. This indicates an issue in analyze_article_comprehensive.")
                        self.stats['processing_errors'] += 1
                except Exception as exc: # Catch errors from the future execution itself
                    analyzer_logger.error(f"Analysis task for article ID '{article_id_str}' generated an unhandled exception: {exc}", exc_info=True)
                    self.stats['processing_errors'] += 1
                    # Optionally, mark the article as 'failed_analysis' in DB here if not already handled by fallback
                    self.collection.update_one(
                        {'_id': ObjectId(article_id_str)}, # Ensure it's an ObjectId if querying by _id
                        {'$set': {'processing_status': 'failed_analysis', 'last_error_details': str(exc)[:500]}}
                    )

        self.stats['end_time'] = datetime.utcnow().isoformat()
        if self.stats['processing_errors'] > 0 or self.stats['fallback_analyses_used'] > 0 :
             self.stats['status'] = 'completed_with_errors_or_fallbacks'
        else:
             self.stats['status'] = 'completed_successfully'

        self.save_analysis_summary()
        analyzer_logger.info(f"AI analysis batch run finished. Final Stats: {json.dumps(self.stats, indent=2, default=str)}")
        return self.stats

    def save_analysis_summary(self):
        """Saves a summary of the analysis batch run to a JSON file."""
        summary_path = os.path.join(RESULTS_DIR, 'analysis_summary.json')

        # Ensure all stats are serializable
        final_stats = self.stats.copy()
        final_stats['end_time'] = final_stats.get('end_time', datetime.utcnow().isoformat())
        if final_stats.get('start_time') and final_stats.get('end_time'):
             final_stats['duration_seconds'] = (datetime.fromisoformat(final_stats['end_time']) -
                                              datetime.fromisoformat(final_stats['start_time'])).total_seconds()
        else:
            final_stats['duration_seconds'] = 0

        summary_doc = {
            'analysis_run_id': hashlib.md5(final_stats['start_time'].encode('utf-8')).hexdigest() if final_stats['start_time'] else None,
            'timestamp_start': final_stats['start_time'],
            'timestamp_end': final_stats['end_time'],
            'duration_seconds': final_stats['duration_seconds'],
            'statistics': final_stats,
            'model_used': self.genai_model_name,
            'embedding_model': 'all-MiniLM-L6-v2', # As configured in __init__
        }
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_doc, f, indent=4, default=str)
            analyzer_logger.info(f"Analysis summary saved to {summary_path}")
        except Exception as e:
            analyzer_logger.error(f"Error saving analysis summary to {summary_path}: {e}", exc_info=True)

def run_analysis_task(batch_size: int = 10) -> dict:
    """
    Main function to run the AI analysis task for a batch of articles.
    Initializes and uses the GeminiAnalyzer.

    Args:
        batch_size (int): The number of articles to process in this run.

    Returns:
        dict: Statistics from the analysis run.
    """
    analyzer_logger.info(f"--- Initiating new AI analysis task run (batch_size: {batch_size}) ---")
    google_api_key = os.getenv('GOOGLE_API_KEY')
    mongodb_uri = os.getenv('MONGODB_URI')

    if not google_api_key:
        analyzer_logger.error("CRITICAL: GOOGLE_API_KEY not set. Analysis task cannot proceed.")
        return {"status": "error", "message": "GOOGLE_API_KEY not configured for analyzer."}
    if not mongodb_uri:
        analyzer_logger.error("CRITICAL: MONGODB_URI not set. Analysis task cannot proceed.")
        return {"status": "error", "message": "MONGODB_URI not configured for analyzer."}

    start_run_time = time.time()
    try:
        analyzer = GeminiAnalyzer(google_api_key=google_api_key, mongodb_uri=mongodb_uri)
        stats = analyzer.run_batch_analysis(batch_size=batch_size)
        analyzer_logger.info("AI analysis task completed successfully via run_analysis_task wrapper.")
        end_run_time = time.time()
        analyzer_logger.info(f"--- AI analysis task run completed in {end_run_time - start_run_time:.2f} seconds ---")
        return stats
    except ValueError as ve: # Configuration errors from GeminiAnalyzer init
        analyzer_logger.error(f"Configuration error during analysis task setup: {ve}", exc_info=True)
        return {"status": "error", "message": str(ve), "details": "ValueError during GeminiAnalyzer initialization."}
    except Exception as e: # Any other unexpected error
        analyzer_logger.error(f"An unexpected error occurred during the main analysis task: {e}", exc_info=True)
        end_run_time = time.time()
        analyzer_logger.info(f"--- AI analysis task run failed after {end_run_time - start_run_time:.2f} seconds ---")
        return {"status": "error", "message": "An unexpected error occurred during analysis.", "details": str(e)}

# Example of how to run it directly (for testing purposes, not for Flask app use)
# if __name__ == "__main__":
#     print("Running analyzer module directly for testing...")
#     # Ensure .env or environment variables are set for direct testing.
#     dotenv_path_local = os.path.join(os.path.dirname(__file__), '.env')
#     if os.path.exists(dotenv_path_local):
#         load_dotenv(dotenv_path_local)
#         print(f"Loaded .env file from {dotenv_path_local}")
#     else:
#         print(f"Warning: .env file not found at {dotenv_path_local}. "
#               "Ensure GOOGLE_API_KEY and MONGODB_URI are set for direct testing.")

#     results = run_analysis_task(batch_size=2) # Test with a small batch
#     print("\n--- Analysis Task Direct Run Results ---")
#     print(json.dumps(results, indent=2, default=str))
#     if results.get("status") == "error":
#         sys.exit(1)
#     sys.exit(0)

import hashlib # Ensure hashlib is imported as it's used in save_analysis_summary but was not at top-level
