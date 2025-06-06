# -*- coding: utf-8 -*-
"""
API Endpoints for System Analytics.

This module defines the Blueprint for analytics-related data. It provides
an endpoint that aggregates various statistics from the MongoDB database
to give an overview of the system's content and processing status.
"""
from flask import Blueprint, current_app, request # Added request for potential future use
from ..db import mongo # mongo instance from flask_backend.db
from ..utils import make_json_response, error_response, serialize_mongo_doc # Response formatting
from datetime import datetime, timedelta # For time-based calculations if needed

# Blueprint for analytics routes, prefixed with /api via app.py registration
analytics_bp = Blueprint('analytics_bp', __name__, url_prefix='/analytics')


@analytics_bp.route('', methods=['GET']) # Path relative to Blueprint prefix
def get_system_analytics():
    """
    Provides overall system analytics and statistics from the database.

    This includes:
    - Total number of articles in the database.
    - Breakdown of articles by their processing status.
    - Top sources by the number of articles.
    - Average scores (bias, misinformation risk, credibility, sentiment) for analyzed articles.
    - Distribution of misinformation risk scores.
    - Number of articles scraped daily over the last N days.

    Query Parameters:
        days_scraped (int, optional): Number of past days to consider for "articles scraped daily". Default: 7.

    Returns:
        JSON response: A dictionary containing various system statistics.
        On error, returns a JSON error message with status code 500.
    """
    current_app.logger.info("API: GET /analytics called.")
    try:
        # --- Total Articles ---
        total_articles = mongo.db.articles.count_documents({})

        # --- Articles by Processing Status ---
        status_pipeline = [
            {
                '$group': {
                    '_id': '$processing_status',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            }
        ]
        articles_by_status = list(mongo.db.articles.aggregate(status_pipeline))

        # --- Articles by Source ---
        source_pipeline = [
            {
                '$match': {'source': {'$ne': None, '$ne': ""}} # Exclude articles with no source
            },
            {
                '$group': {
                    '_id': '$source',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            },
            {
                '$limit': 20 # Top 20 sources
            }
        ]
        articles_by_source = list(mongo.db.articles.aggregate(source_pipeline))

        # --- Average Scores (Bias, Misinformation, Credibility, Sentiment) ---
        # Only for articles that have been analyzed
        avg_scores_pipeline = [
            {
                '$match': {
                    'processing_status': {'$in': ['analyzed', 'analyzed_fallback']},
                    # Ensure fields exist to avoid errors in $avg if some docs don't have them
                    'bias_score': {'$exists': True, '$ne': None},
                    'misinformation_risk': {'$exists': True, '$ne': None},
                    'credibility_score': {'$exists': True, '$ne': None},
                    'sentiment': {'$exists': True, '$ne': None},
                }
            },
            {
                '$group': {
                    '_id': None, # Group all matched documents together
                    'average_bias_score': {'$avg': '$bias_score'},
                    'average_misinformation_risk': {'$avg': '$misinformation_risk'},
                    'average_credibility_score': {'$avg': '$credibility_score'},
                    'average_sentiment': {'$avg': '$sentiment'},
                    'analyzed_article_count': {'$sum': 1}
                }
            }
        ]
        avg_scores_result = list(mongo.db.articles.aggregate(avg_scores_pipeline))
        average_scores = avg_scores_result[0] if avg_scores_result else {
            'average_bias_score': 0, 'average_misinformation_risk': 0,
            'average_credibility_score': 0, 'average_sentiment': 0, 'analyzed_article_count': 0
        }
        if '_id' in average_scores: del average_scores['_id'] # Remove the null _id field

        # --- Misinformation Risk Distribution (Example: Low, Medium, High) ---
        misinfo_distribution_pipeline = [
            {
                '$match': {
                    'processing_status': {'$in': ['analyzed', 'analyzed_fallback']},
                    'misinformation_risk': {'$exists': True, '$ne': None}
                }
            },
            {
                '$bucket': {
                    'groupBy': '$misinformation_risk',
                    'boundaries': [0, 0.3, 0.7, 1.01], # Low (0-0.3), Medium (0.3-0.7), High (0.7-1.0)
                                                     # 1.01 as upper bound to include 1.0
                    'default': 'Other', # For values outside boundaries, though risk is 0-1
                    'output': {
                        'count': {'$sum': 1}
                    }
                }
            }
        ]
        misinformation_distribution = list(mongo.db.articles.aggregate(misinfo_distribution_pipeline))
        # Remap bucket _id for clarity
        for bucket in misinformation_distribution:
            if bucket['_id'] == 0: bucket['risk_level'] = 'Low (0.0-0.3)'
            elif bucket['_id'] == 0.3: bucket['risk_level'] = 'Medium (0.3-0.7)'
            elif bucket['_id'] == 0.7: bucket['risk_level'] = 'High (0.7-1.0)'
            else: bucket['risk_level'] = str(bucket['_id']) # Should be 'Other' if any


        # --- Articles Scraped Over Last N Days ---
        days_filter_scrape = int(request.args.get('days_scraped', 7))
        time_filter_scrape = datetime.utcnow() - timedelta(days=days_filter_scrape)
        scraped_last_n_days_pipeline = [
            {
                '$match': {'scraped_at': {'$gte': time_filter_scrape}}
            },
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$scraped_at'},
                        'month': {'$month': '$scraped_at'},
                        'day': {'$dayOfMonth': '$scraped_at'}
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}}
        ]
        articles_scraped_daily = list(mongo.db.articles.aggregate(scraped_last_n_days_pipeline))


        return make_json_response({
            "total_articles_in_db": total_articles,
            "articles_by_processing_status": serialize_mongo_doc(articles_by_status),
            "top_sources_by_article_count": serialize_mongo_doc(articles_by_source),
            "average_scores_of_analyzed_articles": serialize_mongo_doc(average_scores),
            "misinformation_risk_distribution": serialize_mongo_doc(misinformation_distribution),
            "articles_scraped_daily_last_7_days": serialize_mongo_doc(articles_scraped_daily)
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching system analytics: {e}", exc_info=True)
        return error_response(f"An error occurred while fetching system analytics: {str(e)}", 500)
