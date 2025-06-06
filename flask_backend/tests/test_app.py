import pytest
from flask import current_app, jsonify

def test_app_creation(app):
    """Test if the Flask app instance is created and configured for testing."""
    assert app is not None
    assert current_app.config["TESTING"] is True
    assert current_app.config["DEBUG"] is False

def test_app_logger_is_correct(app, logger):
    """Test that the app.logger is the one we configured."""
    # The 'logger' fixture here would be the one from conftest if defined,
    # or we can access current_app.logger.
    # This test assumes that the logger configured in app.py is indeed used.
    assert current_app.logger.name == 'flask_backend.app' # or whatever name you gave it
    # Add more specific checks if needed, e.g., handler count or types, if stable.

def test_root_endpoint(client):
    """Test the root endpoint '/'."""
    response = client.get('/')
    assert response.status_code == 200
    json_data = response.get_json()
    assert "message" in json_data
    assert "Hello, World!" in json_data["message"]

def test_custom_error_handler_404(client):
    """Test the custom 404 error handler."""
    response = client.get('/non_existent_route_for_testing_404')
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data["status"] == "error"
    assert "Resource not found" in json_data["message"]

# Example test for another error handler if you have specific ways to trigger them
# def test_custom_error_handler_400(client):
#     # This would require an endpoint that can be made to raise a 400,
#     # or directly testing the error handler function if possible.
#     # For now, the 404 test demonstrates the JSON error response.
#     pass

def test_cors_headers_api(client):
    """Test if CORS headers are present for API routes."""
    # Test an example API route (can be any valid one)
    # Assuming /api/scrape is a valid POST route from your app.py setup
    # If it's a GET route, use client.get()
    # For this test, let's assume /api/scheduler/status is a GET route
    response = client.get('/api/scheduler/status', headers={
        'Origin': 'http://example.com'
    })
    # Even if the route itself has issues (e.g. scheduler not running),
    # CORS headers should still be applied by Flask-CORS.
    # However, if the route doesn't exist, it might hit a 404 before CORS headers are fully applied by the app for that specific route.
    # So, it's best to test with an existing route.

    # If the /api/scheduler/status route exists and is processed:
    if response.status_code != 404: # Ensure route exists
      assert 'Access-Control-Allow-Origin' in response.headers
      # Check for specific origin if not "*" and testing for that
      # For `resources={r"/api/*": {"origins": "*"}}`, this should be "*"
      # However, browser behavior with "*" and credentials can be complex.
      # Flask-CORS often returns the requesting origin if it's allowed.
      # If `origins="*"` is set and no credentials are involved, it might be `*`.
      # If `origins` is a list, and `Origin` is in it, it should be the `Origin` header.
      # For `origins='*'`, it often reflects the Origin header back or is '*'
      # This depends on the exact CORS configuration details and request type.
      # A simple check for the header's presence is a good start.
      # A more specific check would be:
      # assert response.headers['Access-Control-Allow-Origin'] == 'http://example.com' or response.headers['Access-Control-Allow-Origin'] == '*'

# This import assumes your logger fixture is defined in conftest.py and named 'logger'
# If not, remove 'logger' from the test_app_logger_is_correct signature.
# For now, I'll remove it as we are using current_app.logger directly.
# from conftest import logger
