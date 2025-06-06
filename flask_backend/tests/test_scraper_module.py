import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import hashlib

# Module to test
from flask_backend.scraper import NewsAPIFetcher, run_scraping_task

# Mock environment variables if scraper module tries to load them directly (though it shouldn't if app passes them)
# For NewsAPIFetcher, keys are passed in constructor. For run_scraping_task, it uses os.getenv.
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("NEWS_API_KEY", "test_news_key")
    monkeypatch.setenv("MONGODB_URI", "mongodb://test_mongo_uri")
    monkeypatch.setenv("BATCH_SIZE_ANALYSIS", "5") # For when analysis is triggered

@pytest.fixture
def mock_newsapi_client():
    """Fixture for a mocked NewsApiClient instance."""
    mock_client = MagicMock()
    # Example successful response for get_top_headlines
    mock_client.get_top_headlines.return_value = {
        "status": "ok",
        "articles": [
            {"title": "Test Article 1", "url": "http://example.com/article1", "source": {"name": "Test Source"}, "publishedAt": datetime.utcnow().isoformat(), "description": "Desc 1"},
            {"title": "Test Article 2", "url": "http://example.com/article2", "source": {"name": "Test Source"}, "publishedAt": datetime.utcnow().isoformat(), "description": "Desc 2"},
        ]
    }
    # Example successful response for get_everything
    mock_client.get_everything.return_value = {
        "status": "ok",
        "articles": [
            {"title": "Topic Article 1", "url": "http://example.com/topic1", "source": {"name": "Topic Source"}, "publishedAt": datetime.utcnow().isoformat(), "description": "Topic Desc 1"},
        ]
    }
    return mock_client

@pytest.fixture
def mock_pymongo_collection():
    """Fixture for a mocked PyMongo collection."""
    mock_collection = MagicMock()
    mock_collection.count_documents.return_value = 0 # Assume no duplicates by default
    mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

    mock_bulk_result = MagicMock()
    mock_bulk_result.inserted_count = 0 # Default to 0, will be set by test
    mock_collection.bulk_write.return_value = mock_bulk_result
    return mock_collection

@pytest.fixture
def mock_sentence_transformer():
    """Fixture for a mocked SentenceTransformer model."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.1, 0.2, 0.3] # Dummy embedding
    return mock_model

@pytest.fixture
def news_fetcher_instance(mock_newsapi_client, mock_pymongo_collection, mock_sentence_transformer, monkeypatch):
    """Creates an instance of NewsAPIFetcher with mocked dependencies."""
    # Patch the constructors or classes if they are instantiated inside NewsAPIFetcher's methods
    monkeypatch.setattr("flask_backend.scraper.NewsApiClient", lambda api_key: mock_newsapi_client)

    # Mock PyMongo client and collection access within NewsAPIFetcher
    mock_mongo_client_instance = MagicMock()
    mock_mongo_client_instance.truthguard.articles = mock_pymongo_collection
    monkeypatch.setattr("flask_backend.scraper.pymongo.MongoClient", lambda uri: mock_mongo_client_instance)

    monkeypatch.setattr("flask_backend.scraper.SentenceTransformer", lambda model_name: mock_sentence_transformer)

    # Patch os.makedirs as it's called in the module
    monkeypatch.setattr("os.makedirs", MagicMock())


    fetcher = NewsAPIFetcher(news_api_key="test_key", mongodb_uri="mongodb://test_uri")
    # Replace client/db/collection instances with mocks directly if preferred over patching constructors
    # fetcher.newsapi = mock_newsapi_client
    # fetcher.collection = mock_pymongo_collection
    # fetcher.model = mock_sentence_transformer
    return fetcher


# --- Tests for NewsAPIFetcher ---
def test_newsapifetcher_init(news_fetcher_instance, mock_pymongo_collection):
    fetcher = news_fetcher_instance
    assert fetcher.api_key == "test_key"
    assert fetcher.collection is not None # Should be the mock
    mock_pymongo_collection.create_index.assert_any_call([("title", "text"), ("content", "text")], background=True)
    mock_pymongo_collection.create_index.assert_any_call([("article_id", 1)], unique=True, background=True)


def test_newsapifetcher_process_article_success(news_fetcher_instance):
    fetcher = news_fetcher_instance
    api_article_data = {
        "title": "A Valid Article",
        "url": "http://example.com/valid",
        "source": {"name": "Valid Source"},
        "publishedAt": datetime.utcnow().isoformat(),
        "description": "This is a valid description of sufficient length to be processed." * 5
    }

    # Mock extract_full_content to return enough content
    fetcher.extract_full_content = MagicMock(return_value="Full article content, long enough for processing. " * 10)

    processed_doc = fetcher.process_article(api_article_data)

    assert processed_doc is not None
    assert processed_doc["title"] == "A Valid Article"
    assert processed_doc["article_id"] == hashlib.md5("http://example.com/valid".encode()).hexdigest()
    assert "content_embedding" in processed_doc
    assert "title_embedding" in processed_doc
    fetcher.extract_full_content.assert_called_once_with("http://example.com/valid")


def test_newsapifetcher_process_article_skip_duplicate(news_fetcher_instance, mock_pymongo_collection):
    fetcher = news_fetcher_instance
    mock_pymongo_collection.count_documents.return_value = 1 # Simulate article already exists

    api_article_data = {"title": "Duplicate", "url": "http://example.com/duplicate"}
    processed_doc = fetcher.process_article(api_article_data)

    assert processed_doc is None
    assert fetcher.stats['duplicates_skipped'] == 1
    expected_article_id = hashlib.md5("http://example.com/duplicate".encode()).hexdigest()
    mock_pymongo_collection.count_documents.assert_called_once_with({"article_id": expected_article_id}, limit=1)


def test_newsapifetcher_process_article_insufficient_content(news_fetcher_instance):
    fetcher = news_fetcher_instance
    api_article_data = {"title": "Short Content", "url": "http://example.com/short", "source": {"name": "Shorts Weekly"}}
    fetcher.extract_full_content = MagicMock(return_value="Too short.") # newspaper3k returns short content

    processed_doc = fetcher.process_article(api_article_data)
    assert processed_doc is None


@patch('flask_backend.scraper.NewsAPIFetcher')
@patch('flask_backend.scraper.run_analysis_task') # Mock the analysis task import
def test_run_scraping_task_success(mock_run_analysis, MockNewsAPIFetcher, mock_env_vars):
    # Configure the mock fetcher instance that will be created
    mock_fetcher_instance = MockNewsAPIFetcher.return_value
    mock_fetcher_instance.run_scraping_task_logic.return_value = {
        "status": "completed", "articles_stored": 5, "errors": 0
    }
    # Configure mock analysis task
    mock_run_analysis.return_value = {"status": "success_analysis"}

    result = run_scraping_task()

    assert result["status"] == "completed"
    assert result["articles_stored"] == 5
    MockNewsAPIFetcher.assert_called_once_with(news_api_key="test_news_key", mongodb_uri="mongodb://test_mongo_uri")
    mock_fetcher_instance.run_scraping_task_logic.assert_called_once()
    mock_run_analysis.assert_called_once_with(batch_size=5) # From BATCH_SIZE_ANALYSIS env var
    assert "analysis_triggered_result" in result
    assert result["analysis_triggered_result"]["status"] == "success_analysis"


@patch('flask_backend.scraper.NewsAPIFetcher')
@patch('flask_backend.scraper.run_analysis_task')
def test_run_scraping_task_no_articles_stored(mock_run_analysis, MockNewsAPIFetcher, mock_env_vars):
    mock_fetcher_instance = MockNewsAPIFetcher.return_value
    mock_fetcher_instance.run_scraping_task_logic.return_value = {
        "status": "completed", "articles_stored": 0, "errors": 0
    }

    result = run_scraping_task()

    assert result["articles_stored"] == 0
    mock_run_analysis.assert_not_called() # Analysis should not run if no articles stored
    assert "analysis_triggered_result" not in result


def test_run_scraping_task_missing_env_vars(monkeypatch):
    monkeypatch.delenv("NEWS_API_KEY", raising=False)
    result = run_scraping_task()
    assert result["status"] == "error"
    assert "NEWS_API_KEY not configured" in result["message"]

    monkeypatch.setenv("NEWS_API_KEY", "fake_key") # Restore for next potential test
    monkeypatch.delenv("MONGODB_URI", raising=False)
    result = run_scraping_task()
    assert result["status"] == "error"
    assert "MONGODB_URI not configured" in result["message"]

# Need ObjectId for the mock_pymongo_collection fixture
from bson import ObjectId
