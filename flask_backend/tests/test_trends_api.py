import pytest
import json
from unittest.mock import patch, MagicMock

# Assuming client and patched_mongo_db fixtures are from conftest.py
# Note: For aggregation, patched_mongo_db.aggregate needs to be mocked.

def test_get_trends_data_success(client, mocker):
    """Test GET /api/trends successfully returns aggregated data."""

    # Mock the aggregate function on the 'articles' collection
    mock_aggregate_result_topics = [
        {"_id": "ai", "count": 50, "related_articles": ["id1", "id2"]},
        {"_id": "politics", "count": 45, "related_articles": ["id3"]},
    ]
    mock_aggregate_result_sources = [
        {"_id": "News Source X", "average_bias_score": 0.8, "article_count": 10},
        {"_id": "News Source Y", "average_bias_score": 0.75, "article_count": 5},
    ]
    mock_aggregate_result_sentiment = [
        {"_id": {"year": 2023, "month": 1, "day": 1}, "average_sentiment": 0.2, "count": 100},
    ]
    mock_aggregate_result_misinfo = [
        {"_id": {"year": 2023, "month": 1, "day": 1}, "average_misinformation_risk": 0.4, "count": 100},
    ]

    # Use a side_effect to return different results for each aggregate call
    # The order of calls in the route handler matters here.
    # 1. trending_topics_pipeline
    # 2. high_bias_sources_pipeline
    # 3. sentiment_over_time_pipeline
    # 4. misinformation_risk_over_time_pipeline
    mock_db_articles = MagicMock()
    mock_db_articles.aggregate.side_effect = [
        mock_aggregate_result_topics,
        mock_aggregate_result_sources,
        mock_aggregate_result_sentiment,
        mock_aggregate_result_misinfo
    ]

    # Patch the 'mongo.db.articles' object used by the trends route
    # This assumes 'from ..db import mongo' is used in trends.py
    mocker.patch('flask_backend.routes.trends.mongo.db.articles', new=mock_db_articles)

    response = client.get('/api/trends?days=7&limit_topics=2&limit_sources=2')

    assert response.status_code == 200
    json_data = response.get_json()

    assert "trending_topics" in json_data
    assert len(json_data["trending_topics"]) == 2
    assert json_data["trending_topics"][0]["_id"] == "ai"

    assert "high_bias_sources" in json_data
    assert len(json_data["high_bias_sources"]) == 2
    assert json_data["high_bias_sources"][0]["_id"] == "News Source X"

    assert "sentiment_over_time" in json_data
    assert len(json_data["sentiment_over_time"]) == 1
    assert json_data["sentiment_over_time"][0]["average_sentiment"] == 0.2

    assert "misinformation_risk_over_time" in json_data
    assert len(json_data["misinformation_risk_over_time"]) == 1
    assert json_data["misinformation_risk_over_time"][0]["average_misinformation_risk"] == 0.4

    # Verify aggregate was called multiple times (4 times in this case)
    assert mock_db_articles.aggregate.call_count == 4

    # Example: Check arguments of the first call (trending_topics_pipeline)
    first_call_args = mock_db_articles.aggregate.call_args_list[0][0][0] # Args of first call
    assert isinstance(first_call_args, list)
    assert first_call_args[0]['$match']['analyzed_at'] is not None # Check a field from the pipeline
    assert first_call_args[-1]['$limit'] == 2 # Check limit_topics


def test_get_trends_data_db_error(client, mocker):
    """Test GET /api/trends when a database error occurs."""
    mock_db_articles = MagicMock()
    mock_db_articles.aggregate.side_effect = Exception("Database connection failed")

    mocker.patch('flask_backend.routes.trends.mongo.db.articles', new=mock_db_articles)

    response = client.get('/api/trends')

    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "An error occurred while fetching trends data" in json_data['message']
    assert "Database connection failed" in json_data['message'] # The original exception message is included

    assert mock_db_articles.aggregate.call_count > 0 # It should have been attempted
