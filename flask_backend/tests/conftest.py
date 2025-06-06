import pytest
from unittest.mock import MagicMock
import os

# Set a default MONGODB_URI for testing if not already set
# This is important because app.py tries to read it on import
if 'MONGODB_URI' not in os.environ:
    os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/test_truthguard_db'
if 'GOOGLE_API_KEY' not in os.environ:
    os.environ['GOOGLE_API_KEY'] = 'test_google_api_key'
if 'NEWS_API_KEY' not in os.environ:
    os.environ['NEWS_API_KEY'] = 'test_news_api_key'


@pytest.fixture(scope='session')
def app():
    """
    Session-wide test Flask application.
    This ensures the app is created once per test session.
    """
    # Dynamically import app after env vars are potentially set
    from flask_backend.app import app as actual_app

    # Configuration for testing
    actual_app.config.update({
        "TESTING": True,
        "MONGO_URI": os.environ['MONGODB_URI'], # Use the test URI
        "DEBUG": False, # Ensure DEBUG is False for testing to avoid certain behaviors
        # Disable CSRF protection if you have it and it interferes with tests
        # "WTF_CSRF_ENABLED": False,
        # "SERVER_NAME": "localhost.test" # If you need to test things dependent on server name
    })

    # Mock database initialization and other external services if necessary
    # For example, preventing actual DB connections during unit tests of routes
    # if init_db is imported and called in create_app or similar
    # from flask_backend import db
    # db.init_db = MagicMock() # Mock the entire function if it makes actual connections

    # If your app structure uses an app factory (create_app()):
    # from flask_backend.app import create_app
    # app = create_app(testing=True) # Assuming you have a way to pass testing config
    # For the current structure, we directly import and configure `app` from app.py

    return actual_app


@pytest.fixture()
def client(app):
    """
    Test client for the Flask application.
    This fixture depends on the `app` fixture.
    A new test client is created for each test function.
    """
    return app.test_client()


@pytest.fixture
def mock_mongo(mocker):
    """
    Fixture to mock the mongo object from flask_backend.db.
    This allows mocking collection methods like find, find_one, insert_one, etc.
    """
    # Mock the 'mongo' instance that is imported in route files
    mock_db_instance = MagicMock()

    # Mock specific collections as needed by your tests
    mock_db_instance.db.articles = MagicMock()
    # Example: mock_db_instance.db.users = MagicMock()

    # Patch where 'mongo' is looked up by the routes.
    # This needs to match how it's imported in your route files.
    # If routes do 'from ..db import mongo', then 'flask_backend.routes.module_name.mongo'
    # For simplicity, if all routes use 'from ..db import mongo', we can try to patch 'flask_backend.db.mongo'
    # However, it's often more robust to patch it where it's used if imports are tricky.
    # A common pattern is that 'mongo' from 'flask_backend.db' is already initialized by app startup.
    # We might need to patch the 'mongo.db.articles' object accessed by routes.

    # For now, let's assume we can patch the 'mongo' object that routes import.
    # This is a common source of confusion. If flask_backend.db.mongo is already populated
    # by init_db, then patching that specific instance's 'db' attribute might be better.

    # Let's try patching the 'mongo' object within the 'flask_backend.db' module itself before it's used
    # This is still tricky because init_db is called on app creation.
    # A more direct way for route testing is to patch 'mongo.db.articles' directly where it's accessed
    # or ensure the 'mongo' object used by the app context in tests is this mock.

    # A common approach:
    # 1. Let the app initialize normally with Flask-PyMongo.
    # 2. For tests, patch the methods on `mongo.db.articles` (the actual PyMongo collection object).
    # This fixture can provide a pre-patched `mongo.db.articles` if needed.

    # For this general fixture, we'll provide a mock that can be used with `mocker.patch.object`
    # or `mocker.patch` for specific test cases.
    # Example usage in a test:
    # mocker.patch('flask_backend.routes.articles.mongo', new=mock_mongo)
    # or if mongo.db.articles is what's used:
    # mocker.patch.object(mongo.db, 'articles', new=mock_mongo.db.articles)

    return mock_db_instance

# Note: The current app structure initializes PyMongo directly.
# For pure unit tests of routes without a live DB, you'd typically patch
# `mongo.db.articles.find_one`, `mongo.db.articles.find`, etc., within each test
# or a more specific fixture. The `mock_mongo` fixture above is a starting point.
# The key is that `from ..db import mongo` in your routes should end up using
# a mocked version for DB-interaction tests.

# A more effective way for `mock_mongo` if `init_db` has already run and populated `flask_backend.db.mongo`:
@pytest.fixture
def patched_mongo_db(mocker):
    """
    Mocks mongo.db.articles to prevent actual DB calls in tests.
    This is suitable if flask_backend.db.mongo is already initialized.
    """
    # Import the actual mongo object that would be used by the app
    from flask_backend.db import mongo as actual_mongo_object

    mock_articles_collection = MagicMock()
    mocker.patch.object(actual_mongo_object.db, 'articles', mock_articles_collection)

    # You can return the mock collection itself if that's what tests need to interact with
    return mock_articles_collection
    # Or return the top-level actual_mongo_object if tests use mongo.db.articles
    # return actual_mongo_object


# To ensure routes use the application context and its configured logger
@pytest.fixture(autouse=True)
def app_context(app):
    """
    Ensures that tests run within the Flask application context.
    This makes `current_app` available.
    """
    with app.app_context():
        yield
