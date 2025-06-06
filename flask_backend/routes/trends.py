# -*- coding: utf-8 -*-
"""
API Endpoints for Trends Analysis.

This module defines the Blueprint for trend-related data. It provides
endpoints that aggregate article data from MongoDB to identify various
trends, such as popular topics, sources with high bias, sentiment shifts,
and misinformation risk evolution over time.
"""
from flask import Blueprint, request, current_app
from ..db import mongo # mongo instance from flask_backend.db
from ..utils import make_json_response, error_response, serialize_mongo_doc # Response formatting utilities
from datetime import datetime, timedelta # For time-based filtering

# Blueprint for trends routes, prefixed with /api via app.py registration
trends_bp = Blueprint('trends_bp', __name__, url_prefix='/trends')


@trends_bp.route('', methods=['GET']) # Path relative to Blueprint prefix
def get_trends_data():
    """
    Provides aggregated data for identifying various trends from analyzed articles.

    This endpoint supports several types of trend analysis through MongoDB aggregation pipelines.
    Query parameters can be used to customize the time window and result limits for these analyses.

    Query Parameters:
        days (int, optional): Number of past days to consider for time-sensitive trends. Default: 7.
        limit_topics (int, optional): Number of top trending topics/keywords to return. Default: 10.
        min_articles_source (int, optional): Minimum number of articles a source must have to be included
                                             in "high bias sources" list. Default: 3.
        limit_sources (int, optional): Number of top sources with highest bias to return. Default: 5.
        limit_sentiment_days (int, optional): Number of daily sentiment data points to return. Default: 30.
        limit_misinfo_days (int, optional): Number of daily misinformation risk data points to return. Default: 30.

    Returns:
        JSON response: A dictionary containing different trend datasets:
            - "trending_topics": List of trending keywords/red_flags and their counts.
            - "high_bias_sources": List of sources with highest average bias scores.
            - "sentiment_over_time": List of daily average sentiment scores.
            - "misinformation_risk_over_time": List of daily average misinformation risk scores.
        On error, returns a JSON error message with status code 500.
    """
    current_app.logger.info("API: GET /trends called with args: %s", request.args)
    try:
        # --- 1. Trending Topics/Keywords (from ai_analysis.misinformation_analysis.red_flags or similar) ---
        # Look at articles analyzed in the last N days (e.g., 7 days)
        days_filter = int(request.args.get('days', 7)) # Allow dynamic day range
        time_filter = datetime.utcnow() - timedelta(days=days_filter)

        trending_topics_pipeline = [
            {
                '$match': {
                    'analyzed_at': {'$gte': time_filter},
                    'processing_status': 'analyzed', # Consider 'analyzed_fallback' too
                    'ai_analysis.misinformation_analysis.red_flags': {'$exists': True, '$ne': []}
                }
            },
            {
                '$unwind': '$ai_analysis.misinformation_analysis.red_flags'
            },
            {
                '$group': {
                    '_id': {'$toLower': '$ai_analysis.misinformation_analysis.red_flags'}, # Group by lowercase red_flag
                    'count': {'$sum': 1},
                    'related_articles': {'$addToSet': '$article_id'} # Optional: list some article IDs
                }
            },
            {
                '$sort': {'count': -1}
            },
            {
                '$limit': int(request.args.get('limit_topics', 10)) # Top N topics
            }
        ]
        trending_topics = list(mongo.db.articles.aggregate(trending_topics_pipeline))

        # --- 2. Sources with Highest Average Bias ---
        # (Can also be filtered by time 'analyzed_at')
        high_bias_sources_pipeline = [
            {
                '$match': {
                    'analyzed_at': {'$gte': time_filter},
                    'processing_status': {'$in': ['analyzed', 'analyzed_fallback']},
                    'bias_score': {'$exists': True, '$ne': None}
                }
            },
            {
                '$group': {
                    '_id': '$source',
                    'average_bias_score': {'$avg': '$bias_score'},
                    'article_count': {'$sum': 1}
                }
            },
            {
                '$match': { # Optional: filter for sources with at least N articles
                    'article_count': {'$gte': int(request.args.get('min_articles_source', 3))}
                }
            },
            {
                '$sort': {'average_bias_score': -1}
            },
            {
                '$limit': int(request.args.get('limit_sources', 5))
            }
        ]
        high_bias_sources = list(mongo.db.articles.aggregate(high_bias_sources_pipeline))

        # --- 3. Sentiment Over Time (Example for a specific keyword/topic if provided) ---
        # This is more complex and might require more specific querying or pre-aggregation.
        # For a general overview, you could show average sentiment per day.
        sentiment_over_time_pipeline = [
            {
                '$match': {
                    'analyzed_at': {'$gte': time_filter}, # Filter by time
                    'processing_status': {'$in': ['analyzed', 'analyzed_fallback']},
                    'sentiment': {'$exists': True, '$ne': None}
                    # Optional: Add a $match for a specific topic/keyword here if desired
                    # 'title': {'$regex': 'some_topic', '$options': 'i'}
                }
            },
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$analyzed_at'},
                        'month': {'$month': '$analyzed_at'},
                        'day': {'$dayOfMonth': '$analyzed_at'}
                    },
                    'average_sentiment': {'$avg': '$sentiment'},
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}
            },
            {
                '$limit': int(request.args.get('limit_sentiment_days', 30)) # Last 30 data points
            }
        ]
        sentiment_over_time = list(mongo.db.articles.aggregate(sentiment_over_time_pipeline))


        # --- 4. Misinformation Risk Evolution (Average risk score over time) ---
        misinfo_risk_pipeline = [
            {
                '$match': {
                    'analyzed_at': {'$gte': time_filter},
                    'processing_status': {'$in': ['analyzed', 'analyzed_fallback']},
                    'misinformation_risk': {'$exists': True, '$ne': None}
                }
            },
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$analyzed_at'},
                        'month': {'$month': '$analyzed_at'},
                        'day': {'$dayOfMonth': '$analyzed_at'}
                    },
                    'average_misinformation_risk': {'$avg': '$misinformation_risk'},
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}
            },
            {
                '$limit': int(request.args.get('limit_misinfo_days', 30))
            }
        ]
        misinformation_risk_over_time = list(mongo.db.articles.aggregate(misinfo_risk_pipeline))


        return make_json_response({
            "trending_topics": serialize_mongo_doc(trending_topics),
            "high_bias_sources": serialize_mongo_doc(high_bias_sources),
            "sentiment_over_time": serialize_mongo_doc(sentiment_over_time),
            "misinformation_risk_over_time": serialize_mongo_doc(misinformation_risk_over_time)
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching trends data: {e}", exc_info=True)
        return error_response(f"An error occurred while fetching trends data: {str(e)}", 500)
