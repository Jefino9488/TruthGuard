import pytest
import json
from unittest.mock import patch

# Assuming client fixture is from conftest.py

@patch('flask_backend.app.run_analysis_task') # Patch where it's imported in app.py
def test_trigger_analysis_success(mock_run_analysis_task, client):
    """Test POST /api/analyze successfully triggers analysis task with default batch_size."""
    mock_run_analysis_task.return_value = {
        "status": "success",
        "message": "Analysis task completed.",
        "articles_successfully_analyzed": 8
    }

    # Test with no body (should use default batch_size)
    response = client.post('/api/analyze')

    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["status"] == "success"
    assert "Analysis task initiated and completed" in json_data["message"]
    assert json_data["data"]["articles_successfully_analyzed"] == 8

    # Default BATCH_SIZE_ANALYSIS is "10" in .env.sample, then converted to int
    mock_run_analysis_task.assert_called_once_with(batch_size=10)


@patch('flask_backend.app.run_analysis_task')
def test_trigger_analysis_success_with_custom_batch_size(mock_run_analysis_task, client):
    """Test POST /api/analyze successfully triggers analysis task with custom batch_size."""
    mock_run_analysis_task.return_value = {
        "status": "success",
        "message": "Analysis task completed.",
        "articles_successfully_analyzed": 3
    }

    custom_batch_size = 5
    response = client.post('/api/analyze', data=json.dumps({"batch_size": custom_batch_size}), content_type='application/json')

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["data"]["articles_successfully_analyzed"] == 3
    mock_run_analysis_task.assert_called_once_with(batch_size=custom_batch_size)


@patch('flask_backend.app.run_analysis_task')
def test_trigger_analysis_invalid_batch_size(mock_run_analysis_task, client):
    """Test POST /api/analyze with an invalid (non-integer) batch_size."""
    # The route currently logs a warning and uses default if batch_size is invalid.
    # So, the call to run_analysis_task should still happen with the default.
    mock_run_analysis_task.return_value = {"status": "success", "articles_successfully_analyzed": 10}

    response = client.post('/api/analyze', data=json.dumps({"batch_size": "invalid_str"}), content_type='application/json')

    assert response.status_code == 200 # Still success as it falls back to default
    json_data = response.get_json()
    assert json_data["status"] == "success"

    # Default BATCH_SIZE_ANALYSIS is "10"
    mock_run_analysis_task.assert_called_once_with(batch_size=10)


@patch('flask_backend.app.run_analysis_task')
def test_trigger_analysis_task_returns_error(mock_run_analysis_task, client):
    """Test POST /api/analyze when the analysis task itself returns an error status."""
    mock_run_analysis_task.return_value = {
        "status": "error",
        "message": "Analysis failed due to API key issue."
    }

    response = client.post('/api/analyze')

    assert response.status_code == 500 # As per current app.py logic
    json_data = response.get_json()

    assert json_data["status"] == "error"
    assert "Analysis failed" in json_data["message"] # From app.py error handling
    assert "API key issue" in json_data["message"]

    mock_run_analysis_task.assert_called_once()


@patch('flask_backend.app.run_analysis_task')
def test_trigger_analysis_task_raises_exception(mock_run_analysis_task, client):
    """Test POST /api/analyze when the analysis task raises an unexpected exception."""
    mock_run_analysis_task.side_effect = Exception("Unexpected runtime error in analyzer")

    response = client.post('/api/analyze')

    assert response.status_code == 500 # General error handler in app.py
    json_data = response.get_json()

    assert json_data["status"] == "error"
    assert "An unexpected error occurred while trying to start analysis." in json_data["message"]

    mock_run_analysis_task.assert_called_once()
