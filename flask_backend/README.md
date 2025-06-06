# TruthGuard Flask Backend

## Overview

The TruthGuard Flask Backend is a Python-based application responsible for scraping news articles from various sources, performing AI-driven analysis (bias, misinformation, sentiment, credibility), and providing a RESTful API for the frontend to consume this data. It includes a background scheduler for periodic scraping and analysis tasks.

## Features

-   **News Scraping:** Periodically fetches news articles using the NewsAPI.
-   **Content Extraction:** Uses `newspaper3k` to extract full article content.
-   **AI Analysis:** Leverages Google's Gemini Pro model for:
    -   Bias detection
    -   Misinformation risk assessment
    -   Sentiment analysis
    -   Credibility scoring
-   **Vector Embeddings:** Generates sentence embeddings for content, titles, and analysis summaries using `sentence-transformers`.
-   **REST API:** Provides endpoints for:
    -   Managing articles (CRUD operations).
    -   Retrieving aggregated trend data.
    -   Fetching system-wide analytics.
    -   Triggering scraping and analysis tasks manually.
    -   Checking scheduler status.
-   **Database:** Uses MongoDB to store articles, analysis results, and embeddings.
-   **Scheduled Tasks:** Employs `APScheduler` to automate scraping and analysis at regular intervals.
-   **Logging:** Comprehensive logging for application events, scraping, and analysis processes.
-   **CORS:** Configured for allowing frontend requests.
-   **Environment Variable Driven Configuration:** Secure and flexible setup using `.env` files.

## Project Structure

```
flask_backend/
├── app.py                # Main Flask application file (init, config, routes, scheduler)
├── scraper.py            # News scraping logic (NewsAPIFetcher)
├── analyzer.py           # AI analysis logic (GeminiAnalyzer, Pydantic models)
├── db.py                 # Database (Flask-PyMongo) initialization and index creation
├── utils.py              # Utility functions (JSON serialization, response formatting, pagination)
├── routes/               # API Blueprints for different resources
│   ├── __init__.py
│   ├── articles.py       # Article CRUD endpoints
│   ├── trends.py         # Trends aggregation endpoints
│   └── analytics.py      # System analytics endpoints
├── tests/                # Pytest unit tests
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures (e.g., test app client)
│   ├── test_app.py
│   ├── test_utils.py
│   ├── test_articles_api.py
│   ├── ... (other test files for APIs and modules)
├── scraping_logs/        # Log files for the scraper module (e.g., scraper.log)
├── analysis_reports/     # Log files for the analyzer module (e.g., gemini_analysis.log)
├── analysis_results/     # JSON summary files from analysis runs (e.g., analysis_summary.json)
├── scraped_data/         # JSON summary/sample files from scraping runs
├── logs/                 # General application logs (e.g., flask_app.log)
├── .env.sample           # Sample environment variable file
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Setup and Installation

### Prerequisites

-   Python 3.9+
-   pip (Python package installer)
-   MongoDB instance (local or cloud-hosted, e.g., MongoDB Atlas)

### Steps

1.  **Clone the Repository (if applicable):**
    If you're working with this backend as part of a larger project, ensure the main repository is cloned. This README is located within the `flask_backend` directory.

2.  **Navigate to the Backend Directory:**
    ```bash
    cd path/to/your/project/flask_backend
    ```

3.  **Create a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows:
        ```bash
        venv\Scripts\activate
        ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Environment Variables:**
    Create a `.env` file in the `flask_backend` directory by copying the sample file:
    ```bash
    cp .env.sample .env
    ```
    Now, edit the `.env` file and provide actual values for the following variables:

    *   `MONGODB_URI`: **Required.** The connection string for your MongoDB database.
        *   Example: `mongodb://localhost:27017/truthguard_db` or `mongodb+srv://user:pass@cluster.mongodb.net/truthguard_db`
    *   `NEWS_API_KEY`: **Required.** Your API key for NewsAPI.org.
    *   `GOOGLE_API_KEY`: **Required.** Your API key for Google AI Studio (Gemini API).
    *   `FLASK_ENV`: (Optional) Set to `development` for development mode (enables debug mode, auto-reloader). Set to `production` for production. Default: `production` if not set, but `app.py` defaults `is_debug` based on `FLASK_DEBUG`.
    *   `FLASK_DEBUG`: (Optional) Set to `True` or `1` to enable Flask's debug mode. Default: `True` as per `app.py` logic if `FLASK_ENV` is not `production`.
    *   `SCRAPE_INTERVAL_HOURS`: (Optional) Interval in hours for the scheduled scraping task. Default: `4`.
    *   `BATCH_SIZE_ANALYSIS`: (Optional) Default number of articles to analyze in a batch when triggered by API or scheduler. Default: `10`.
    *   `FLASK_LOG_LEVEL`: (Optional) Sets the logging level for the Flask app. Examples: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Default: `INFO`.
    *   `CORS_ORIGINS`: (Optional) Comma-separated list of allowed origins for CORS. Example: `http://localhost:3000,https://yourfrontend.com`. Default: `*` (all origins).

## Running the Application

1.  **Ensure Environment Variables are Set:** Make sure your `.env` file is correctly configured.
2.  **Activate Virtual Environment:** If not already active, `source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
3.  **Run the Flask Development Server:**
    You can run the app using either:
    ```bash
    flask run --port 5001
    ```
    (This uses the Flask CLI. `FLASK_APP=app.py` might need to be set if your entry file is different or not auto-detected. The port can be specified as shown.)
    Or directly using Python:
    ```bash
    python app.py
    ```
    The application will typically start on `http://localhost:5001` (as configured in `app.py`). Check the console output for the exact URL.

## API Endpoints

All endpoints are prefixed with `/api`.

### Health & Status

*   **`GET /`** (Root endpoint, not under `/api`)
    *   Description: Basic health check to see if the app is running.
    *   Response: `{"message": "Hello, World! ...", "status": "ok"}`

### Scraping

*   **`POST /api/scrape`**
    *   Description: Manually triggers the news scraping and subsequent analysis task.
    *   Request Body: None.
    *   Success Response (200 OK):
        ```json
        {
          "status": "success",
          "message": "Scraping task initiated and completed.",
          "data": { /* statistics from scraping run */ }
        }
        ```
    *   Error Response (500 Internal Server Error):
        ```json
        {
          "status": "error",
          "message": "An unexpected error occurred..."
        }
        ```

### Analysis

*   **`POST /api/analyze`**
    *   Description: Manually triggers the AI analysis task for a batch of unprocessed articles.
    *   Request Body (JSON, optional):
        ```json
        {
          "batch_size": 5
        }
        ```
        (If `batch_size` is not provided, defaults to `BATCH_SIZE_ANALYSIS` env var or 10).
    *   Success Response (200 OK):
        ```json
        {
          "status": "success",
          "message": "Analysis task initiated and completed.",
          "data": { /* statistics from analysis run */ }
        }
        ```
    *   Error Response (500 Internal Server Error):
        ```json
        {
          "status": "error",
          "message": "An unexpected error occurred..."
        }
        ```

### Articles (CRUD)

*   **`GET /api/articles`**
    *   Description: Retrieves a paginated list of articles. Supports filtering and sorting.
    *   Query Parameters: `page`, `per_page`, `source`, `processing_status`, `topic`, `sort_by`, `sort_order`.
    *   Success Response (200 OK):
        ```json
        {
          "page": 1,
          "per_page": 10,
          "total_articles": 100,
          "articles": [ { /* article object */ }, ... ]
        }
        ```
*   **`GET /api/articles/<article_id_str>`**
    *   Description: Retrieves a single article by its ID (MongoDB ObjectId or custom `article_id`).
    *   Success Response (200 OK): `{ /* article object */ }`
    *   Error Response (404 Not Found): `{"status": "error", "message": "Article not found."}`
*   **`POST /api/articles`**
    *   Description: Creates a new article.
    *   Request Body (JSON): Article data (see `routes/articles.py` docstring for fields).
    *   Success Response (201 Created): `{"message": "Article created successfully.", "article": { /* created article object */ }}`
    *   Error Response (400 Bad Request, 409 Conflict): `{"status": "error", "message": "Validation error or duplicate."}`
*   **`PUT /api/articles/<article_id_str>`**
    *   Description: Updates an existing article.
    *   Request Body (JSON): Fields to update.
    *   Success Response (200 OK): `{"message": "Article updated successfully.", "article": { /* updated article object */ }}`
*   **`DELETE /api/articles/<article_id_str>`**
    *   Description: Deletes an article.
    *   Success Response (200 OK): `{"message": "Article deleted successfully."}`

### Trends

*   **`GET /api/trends`**
    *   Description: Provides aggregated data for identifying trends (e.g., trending topics, biased sources).
    *   Query Parameters: `days`, `limit_topics`, `min_articles_source`, `limit_sources`, etc.
    *   Success Response (200 OK):
        ```json
        {
          "trending_topics": [ ... ],
          "high_bias_sources": [ ... ],
          "sentiment_over_time": [ ... ],
          "misinformation_risk_over_time": [ ... ]
        }
        ```

### Analytics

*   **`GET /api/analytics`**
    *   Description: Provides overall system statistics.
    *   Query Parameters: `days_scraped`.
    *   Success Response (200 OK):
        ```json
        {
          "total_articles_in_db": 150,
          "articles_by_processing_status": [ ... ],
          /* ... other stats ... */
        }
        ```

### Scheduler

*   **`GET /api/scheduler/status`**
    *   Description: Gets the current status of the APScheduler and lists its jobs.
    *   Success Response (200 OK):
        ```json
        {
          "status": "running", // or "not_running"
          "jobs": [ { "id": "...", "name": "...", ... }, ... ]
        }
        ```

## Testing

Unit tests are written using `pytest`.

1.  **Install Test Dependencies:**
    Ensure `pytest` and `pytest-mock` are installed (they are in `requirements.txt`).
2.  **Run Tests:**
    Navigate to the project root (the directory containing `flask_backend`) and run:
    ```bash
    pytest flask_backend/tests/
    ```
    Or, from within the `flask_backend` directory:
    ```bash
    pytest tests/
    ```

## Logging

The application uses several log files stored in the `flask_backend` directory:

-   **`logs/flask_app.log`**: Main application log for Flask app events, API requests, errors, and general information. Log level is configurable via `FLASK_LOG_LEVEL`.
-   **`scraping_logs/scraper.log`**: Specific logs for the news scraping process from `scraper.py`.
-   **`analysis_reports/gemini_analysis.log`**: Specific logs for the AI analysis process from `analyzer.py`.

Additionally, analysis and scraping modules output JSON summary files to `analysis_results/` and `scraped_data/` respectively upon completion of their tasks.

## Contributing

(Optional: Add guidelines for contributing if this were an open project.)

---

This README provides a comprehensive guide to understanding, setting up, and using the TruthGuard Flask Backend.
