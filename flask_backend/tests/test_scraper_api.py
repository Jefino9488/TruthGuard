import pytest
import json
from unittest.mock import patch

# Assuming client fixture is from conftest.py

@patch('flask_backend.app.run_scraping_task') # Patch where it's imported in app.py
def test_trigger_scrape_success(mock_run_scraping_task, client):
    """Test POST /api/scrape successfully triggers scraping task."""
    mock_run_scraping_task.return_value = {
        "status": "success",
        "message": "Scraping task initiated and completed.",
        "articles_stored": 5,
        "analysis_triggered_result": {"status": "success", "articles_analyzed": 5}
    }

    response = client.post('/api/scrape')

    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["status"] == "success"
    assert "Scraping task initiated and completed" in json_data["message"]
    assert json_data["data"]["articles_stored"] == 5
    assert json_data["data"]["analysis_triggered_result"]["articles_analyzed"] == 5

    mock_run_scraping_task.assert_called_once()


@patch('flask_backend.app.run_scraping_task')
def test_trigger_scrape_task_returns_error(mock_run_scraping_task, client):
    """Test POST /api/scrape when the scraping task itself returns an error status."""
    mock_run_scraping_task.return_value = {
        "status": "error",
        "message": "Scraping failed due to API key limit."
    }

    response = client.post('/api/scrape')

    assert response.status_code == 500 # As per current app.py logic for this case
    json_data = response.get_json()

    assert json_data["status"] == "error"
    assert "Scraping failed" in json_data["message"] # From app.py error handling
    assert "API key limit" in json_data["message"]

    mock_run_scraping_task.assert_called_once()


@patch('flask_backend.app.run_scraping_task')
def test_trigger_scrape_task_raises_exception(mock_run_scraping_task, client):
    """Test POST /api/scrape when the scraping task raises an unexpected exception."""
    mock_run_scraping_task.side_effect = Exception("Unexpected runtime error in scraper")

    response = client.post('/api/scrape')

    assert response.status_code == 500 # General error handler in app.py
    json_data = response.get_json()

    assert json_data["status"] == "error"
    assert "An unexpected error occurred while trying to start scraping." in json_data["message"]

    mock_run_scraping_task.assert_called_once()

# Note: The current /api/scrape endpoint in app.py does not take a JSON body.
# If it were to (e.g., to pass parameters to the scraper),
# tests for valid and invalid bodies would be added here.
