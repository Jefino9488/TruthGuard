# flask_backend/app/routes/main.py

from flask import Blueprint, request, jsonify, current_app
from app.tasks import NewsAPIFetcherTask, GeminiAnalyzerTask
from app.services import ArticleService
from app import db # Import the global db client

main_bp = Blueprint('main', __name__)

@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "TruthGuard Backend is healthy!"}), 200

@main_bp.route('/scrape', methods=['POST'])
def trigger_scrape():
    """
    API endpoint to trigger the news scraping task.
    """
    try:
        # Get configuration from Flask app config
        news_api_key = current_app.config['NEWS_API_KEY']

        # Instantiate the scraper task
        scraper = NewsAPIFetcherTask(db, news_api_key)

        # Run scraper in a non-blocking way (e.g., using a thread or process for a simple app)
        # For production, consider using Celery or similar task queue.
        # Here, we'll run it directly but in a new thread to not block the request.
        import threading
        thread = threading.Thread(target=scraper.run_scraper)
        thread.start()

        return jsonify({"message": "News scraping initiated successfully!", "status": "processing"}), 202 # 202 Accepted
    except Exception as e:
        current_app.logger.error(f"Error triggering scraping: {e}")
        return jsonify({"error": "Failed to initiate scraping task", "details": str(e)}), 500

@main_bp.route('/analyze', methods=['POST'])
def trigger_analysis():
    """
    API endpoint to trigger the AI analysis task.
    """
    try:
        # Get configuration from Flask app config
        google_api_key = current_app.config['GOOGLE_API_KEY']
        batch_size = current_app.config['BATCH_SIZE_ANALYSIS']

        # Instantiate the analyzer task
        analyzer = GeminiAnalyzerTask(db, google_api_key)

        # Run analyzer in a non-blocking way
        import threading
        thread = threading.Thread(target=analyzer.run_analyzer, args=(batch_size,))
        thread.start()

        return jsonify({"message": "AI analysis initiated successfully!", "status": "processing"}), 202
    except Exception as e:
        current_app.logger.error(f"Error triggering analysis: {e}")
        return jsonify({"error": "Failed to initiate analysis task", "details": str(e)}), 500

@main_bp.route('/articles', methods=['GET'])
def get_articles():
    """
    API endpoint to retrieve a paginated list of articles.
    Query parameters: page, limit, sort_by, sort_order
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'published_at', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)

    service = ArticleService(db)
    result = service.get_all_articles(page, limit, sort_by, sort_order)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200

@main_bp.route('/articles/<article_id>', methods=['GET'])
def get_article_detail(article_id):
    """
    API endpoint to retrieve details of a single article by its ID.
    """
    service = ArticleService(db)
    article = service.get_article_by_id(article_id)
    if article:
        return jsonify(article), 200
    return jsonify({"message": "Article not found"}), 404

@main_bp.route('/articles/search', methods=['GET'])
def search_articles_endpoint():
    """
    API endpoint to search articles.
    Query parameters: q (query string), page, limit, sort_by, sort_order
    """
    query = request.args.get('q', type=str)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'score', type=str) # Default sort by text score for search
    sort_order = request.args.get('sort_order', 'desc', type=str)

    if not query:
        return jsonify({"error": "Query parameter 'q' is required for search."}), 400

    service = ArticleService(db)
    result = service.search_articles(query, page, limit, sort_by, sort_order)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200

@main_bp.route('/articles/high-bias', methods=['GET'])
def get_high_bias_articles():
    """
    API endpoint to retrieve articles flagged with high bias.
    Query parameters: min_score, page, limit, sort_order
    """
    min_score = request.args.get('min_score', 0.7, type=float)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    sort_order = request.args.get('sort_order', 'desc', type=str)

    service = ArticleService(db)
    result = service.get_articles_by_bias_score(min_score, page, limit, sort_order)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200

@main_bp.route('/articles/misinformation-risk', methods=['GET'])
def get_misinformation_risk_articles():
    """
    API endpoint to retrieve articles flagged with high misinformation risk.
    Query parameters: min_risk, page, limit, sort_order
    """
    min_risk = request.args.get('min_risk', 0.6, type=float)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    sort_order = request.args.get('sort_order', 'desc', type=str)

    service = ArticleService(db)
    result = service.get_articles_by_misinformation_risk(min_risk, page, limit, sort_order)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200