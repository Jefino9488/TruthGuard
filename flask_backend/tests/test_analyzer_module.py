import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

# Module to test
from flask_backend.analyzer import GeminiAnalyzer, run_analysis_task, AnalysisResponse, BiasAnalysis, MisinformationAnalysis, SentimentAnalysis, CredibilityAssessment

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key")
    monkeypatch.setenv("MONGODB_URI", "mongodb://test_mongo_uri_analyzer")

@pytest.fixture
def mock_google_genai_configure():
    """Mocks genai.configure."""
    with patch('flask_backend.analyzer.genai.configure') as mock_config:
        yield mock_config

@pytest.fixture
def mock_google_generative_model():
    """Mocks genai.GenerativeModel and its generate_content method."""
    mock_model_instance = MagicMock()

    # Default successful response
    mock_response_part = MagicMock()
    # Simulate Pydantic model structure for the response text
    default_analysis_response = AnalysisResponse(
        bias_analysis=BiasAnalysis(overall_score=0.2, political_leaning="center"),
        misinformation_analysis=MisinformationAnalysis(risk_score=0.1),
        sentiment_analysis=SentimentAnalysis(overall_sentiment=0.05),
        credibility_assessment=CredibilityAssessment(overall_score=0.7),
        confidence=0.8
    )
    mock_response_part.text = default_analysis_response.model_dump_json()

    mock_response_candidate = MagicMock()
    mock_response_candidate.content.parts = [mock_response_part]

    mock_genai_response = MagicMock()
    mock_genai_response.candidates = [mock_response_candidate]
    mock_genai_response.text = default_analysis_response.model_dump_json() # Make text directly accessible
    mock_genai_response.prompt_feedback = None # No block by default

    mock_model_instance.generate_content.return_value = mock_genai_response

    with patch('flask_backend.analyzer.genai.GenerativeModel') as mock_constructor:
        mock_constructor.return_value = mock_model_instance
        yield mock_model_instance # Yield the instance for tests to use

@pytest.fixture
def mock_pymongo_collection_analyzer():
    """Fixture for a mocked PyMongo collection specific to analyzer tests."""
    mock_collection = MagicMock()
    mock_collection.find.return_value = [] # Default to no articles found
    mock_collection.update_one.return_value = MagicMock(matched_count=1, modified_count=1)
    return mock_collection

@pytest.fixture
def mock_sentence_transformer_analyzer():
    """Fixture for a mocked SentenceTransformer model."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.5, 0.6, 0.7] # Dummy embedding
    return mock_model

@pytest.fixture
def analyzer_instance(mock_google_genai_configure, mock_google_generative_model, mock_pymongo_collection_analyzer, mock_sentence_transformer_analyzer, monkeypatch):
    """Creates an instance of GeminiAnalyzer with mocked dependencies."""

    # Mock PyMongo client and collection access
    mock_mongo_client_instance = MagicMock()
    mock_mongo_client_instance.truthguard.articles = mock_pymongo_collection_analyzer
    monkeypatch.setattr("flask_backend.analyzer.pymongo.MongoClient", lambda uri: mock_mongo_client_instance)

    monkeypatch.setattr("flask_backend.analyzer.SentenceTransformer", lambda model_name: mock_sentence_transformer_analyzer)

    # Patch os.makedirs
    monkeypatch.setattr("os.makedirs", MagicMock())

    analyzer = GeminiAnalyzer(google_api_key="test_google_key", mongodb_uri="mongodb://test_uri_analyzer")
    return analyzer

# --- Tests for GeminiAnalyzer ---
def test_gemini_analyzer_init(analyzer_instance, mock_google_genai_configure):
    analyzer = analyzer_instance
    assert analyzer.mongo_client is not None
    assert analyzer.collection is not None
    assert analyzer.embedding_model is not None
    mock_google_genai_configure.assert_called_once_with(api_key="test_google_key")


def test_analyze_article_comprehensive_success(analyzer_instance, mock_google_generative_model, mock_pymongo_collection_analyzer):
    analyzer = analyzer_instance
    article_doc = {
        "_id": ObjectId(),
        "title": "Test Article for Analysis",
        "content": "Some content to analyze.",
        "source": "Test Source",
        "content_embedding": None, # Ensure embedding generation is tested
        "title_embedding": None,
    }

    analysis_result = analyzer.analyze_article_comprehensive(article_doc)

    assert analysis_result is not None
    assert analysis_result["confidence"] == 0.8 # From default mock response

    mock_google_generative_model.generate_content.assert_called_once()
    # Check that update_one was called, implying analysis was stored
    mock_pymongo_collection_analyzer.update_one.assert_called_once()
    call_args = mock_pymongo_collection_analyzer.update_one.call_args[0][1]['$set'] # Get the $set part
    assert "ai_analysis" in call_args
    assert call_args["processing_status"] == "analyzed"
    assert "content_embedding" in call_args # Check if new embeddings were added
    assert "title_embedding" in call_args
    assert "analysis_embedding" in call_args


def test_analyze_article_comprehensive_api_error_fallback(analyzer_instance, mock_google_generative_model, mock_pymongo_collection_analyzer):
    analyzer = analyzer_instance
    # Simulate an API error from Gemini
    from flask_backend.analyzer import google_errors # Import the aliased errors
    mock_google_generative_model.generate_content.side_effect = google_errors.ResourceExhaustedError("Rate limit")

    article_doc = {"_id": ObjectId(), "title": "API Error Test", "content": "Content."}

    analysis_result = analyzer.analyze_article_comprehensive(article_doc, max_retries=1) # Limit retries for test speed

    assert analysis_result is not None
    assert analysis_result["bias_analysis"]["political_leaning"] == "center (fallback)" # Check for fallback data
    assert analyzer.stats['fallback_analyses_used'] == 1
    assert analyzer.stats['processing_errors'] > 0 # Should be at least 1 due to API error leading to fallback

    mock_pymongo_collection_analyzer.update_one.assert_called_once()
    call_args = mock_pymongo_collection_analyzer.update_one.call_args[0][1]['$set']
    assert call_args["processing_status"] == "analyzed_fallback"
    assert "fallback (ResourceExhaustedError)" in call_args["analysis_model"]


def test_run_batch_analysis_no_articles(analyzer_instance, mock_pymongo_collection_analyzer):
    analyzer = analyzer_instance
    mock_pymongo_collection_analyzer.find.return_value = [] # No articles to process

    stats = analyzer.run_batch_analysis(batch_size=5)

    assert stats["articles_processed_for_analysis"] == 0
    assert stats["articles_successfully_analyzed"] == 0
    assert stats["status"] == "completed_no_articles"
    mock_pymongo_collection_analyzer.find.assert_called_once()


@patch('flask_backend.analyzer.GeminiAnalyzer')
def test_run_analysis_task_success(MockGeminiAnalyzer, mock_env_vars):
    # Configure the mock analyzer instance
    mock_analyzer_instance = MockGeminiAnalyzer.return_value
    mock_analyzer_instance.run_batch_analysis.return_value = {
        "status": "completed", "articles_successfully_analyzed": 3, "errors": 0
    }

    result = run_analysis_task(batch_size=3)

    assert result["status"] == "completed"
    assert result["articles_successfully_analyzed"] == 3
    MockGeminiAnalyzer.assert_called_once_with(google_api_key="test_google_key", mongodb_uri="mongodb://test_mongo_uri_analyzer")
    mock_analyzer_instance.run_batch_analysis.assert_called_once_with(batch_size=3)


def test_run_analysis_task_missing_env_vars(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    result = run_analysis_task()
    assert result["status"] == "error"
    assert "GOOGLE_API_KEY not configured" in result["message"]

    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key")
    monkeypatch.delenv("MONGODB_URI", raising=False)
    result = run_analysis_task()
    assert result["status"] == "error"
    assert "MONGODB_URI not configured" in result["message"]


def test_generate_fallback_analysis(analyzer_instance, mock_pymongo_collection_analyzer):
    analyzer = analyzer_instance
    article_doc = {"_id": ObjectId(), "title": "Fallback Test", "content": "Content for fallback."}

    fallback_data = analyzer.generate_fallback_analysis(article_doc, reason="TestReason")

    assert fallback_data["confidence"] == 0.3
    assert fallback_data["bias_analysis"]["political_leaning"] == "center (fallback)"

    mock_pymongo_collection_analyzer.update_one.assert_called_once()
    call_args = mock_pymongo_collection_analyzer.update_one.call_args[0][1]['$set']
    assert call_args["processing_status"] == "analyzed_fallback"
    assert "fallback (TestReason)" in call_args["analysis_model"]
    assert analyzer.stats['fallback_analyses_used'] == 1
