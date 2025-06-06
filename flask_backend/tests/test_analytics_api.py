import pytest
import json
from unittest.mock import patch, MagicMock

# Assuming client fixture is from conftest.py

def test_get_system_analytics_success(client, mocker):
    """Test GET /api/analytics successfully returns aggregated data."""

    mock_db_articles = MagicMock()

    # Define return values for each aggregation call
    # Order matters based on calls in the route:
    # 1. total_articles (count_documents)
    # 2. articles_by_status
    # 3. articles_by_source
    # 4. avg_scores_result
    # 5. misinformation_distribution
    # 6. articles_scraped_daily

    mock_db_articles.count_documents.return_value = 150 # For total_articles

    mock_status_agg = [{"_id": "analyzed", "count": 100}, {"_id": "pending", "count": 50}]
    mock_source_agg = [{"_id": "Source A", "count": 70}, {"_id": "Source B", "count": 80}]
    mock_avg_scores_agg = [{
        # _id: None is removed in the route, so don't include it here
        "average_bias_score": 0.3, "average_misinformation_risk": 0.2,
        "average_credibility_score": 0.7, "average_sentiment": 0.1,
        "analyzed_article_count": 100
    }]
    mock_misinfo_dist_agg = [
        {"_id": 0, "count": 60, "risk_level": "Low (0.0-0.3)"}, # risk_level added in route
        {"_id": 0.3, "count": 30, "risk_level": "Medium (0.3-0.7)"},
        {"_id": 0.7, "count": 10, "risk_level": "High (0.7-1.0)"}
    ]
    mock_scraped_daily_agg = [
        {"_id": {"year": 2023, "month": 1, "day": 1}, "count": 20},
        {"_id": {"year": 2023, "month": 1, "day": 2}, "count": 25},
    ]

    mock_db_articles.aggregate.side_effect = [
        mock_status_agg,
        mock_source_agg,
        mock_avg_scores_agg,
        mock_misinfo_dist_agg,
        mock_scraped_daily_agg
    ]

    mocker.patch('flask_backend.routes.analytics.mongo.db.articles', new=mock_db_articles)

    response = client.get('/api/analytics?days_scraped=2') # Add param if route uses it

    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["total_articles_in_db"] == 150

    assert "articles_by_processing_status" in json_data
    assert len(json_data["articles_by_processing_status"]) == 2
    assert json_data["articles_by_processing_status"][0]["_id"] == "analyzed"

    assert "top_sources_by_article_count" in json_data
    assert len(json_data["top_sources_by_article_count"]) == 2

    assert "average_scores_of_analyzed_articles" in json_data
    assert json_data["average_scores_of_analyzed_articles"]["analyzed_article_count"] == 100

    assert "misinformation_risk_distribution" in json_data
    assert len(json_data["misinformation_risk_distribution"]) == 3
    assert json_data["misinformation_risk_distribution"][0]["risk_level"] == "Low (0.0-0.3)"

    assert "articles_scraped_daily_last_7_days" in json_data # Name in route
    assert len(json_data["articles_scraped_daily_last_7_days"]) == 2

    mock_db_articles.count_documents.assert_called_once_with({})
    assert mock_db_articles.aggregate.call_count == 5 # Check number of aggregation calls


def test_get_system_analytics_db_error_on_count(client, mocker):
    """Test GET /api/analytics when count_documents fails."""
    mock_db_articles = MagicMock()
    mock_db_articles.count_documents.side_effect = Exception("DB count error")

    mocker.patch('flask_backend.routes.analytics.mongo.db.articles', new=mock_db_articles)

    response = client.get('/api/analytics')

    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "An error occurred while fetching system analytics" in json_data['message']
    assert "DB count error" in json_data['message']

    mock_db_articles.count_documents.assert_called_once()


def test_get_system_analytics_db_error_on_aggregate(client, mocker):
    """Test GET /api/analytics when an aggregation fails."""
    mock_db_articles = MagicMock()
    mock_db_articles.count_documents.return_value = 10 # Let count pass
    mock_db_articles.aggregate.side_effect = Exception("DB aggregate error") # Fail on first aggregate

    mocker.patch('flask_backend.routes.analytics.mongo.db.articles', new=mock_db_articles)

    response = client.get('/api/analytics')

    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "An error occurred while fetching system analytics" in json_data['message']
    assert "DB aggregate error" in json_data['message']

    mock_db_articles.count_documents.assert_called_once()
    mock_db_articles.aggregate.assert_called_once() # Failed on the first call
