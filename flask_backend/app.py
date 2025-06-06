"""
Main Flask application file for the TruthGuard Backend.

This file initializes the Flask app, configures logging, database, CORS,
background scheduler, registers API blueprints, and defines global error handlers
and request/response logging.
"""
import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS # Will be used later, but good to have if API is called from a different domain
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# --- Environment Variable Loading ---
# This should be one of the first things to do, to ensure all modules have access to env vars
# when they are imported.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print("INFO: .env file loaded.") # Optional: for debugging startup
else:
    # Fallback for environments where .env might not be present (e.g., production if vars are set directly)
    print("Warning: .env file not found. Relying on environment variables being set directly.")


# --- Module Imports ---
# Import local modules after .env has been loaded, as they might use os.getenv at import time.
from .scraper import run_scraping_task
from .analyzer import run_analysis_task
from .db import init_db
from .utils import error_response


# ---- Logging Setup ----
# Determine log level from environment or default to INFO for the application logger.
# Other libraries might have their own default levels unless explicitly configured.
log_level_str = os.getenv('FLASK_LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

log_dir = 'logs'  # Main directory for application logs
os.makedirs(log_dir, exist_ok=True) # Ensure log directory exists

# Standardized log format for consistency across handlers
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Get a logger instance named after the current module (__name__ will be 'flask_backend.app')
# This logger will be configured and then assigned to app.logger.
module_logger = logging.getLogger(__name__)
module_logger.setLevel(log_level)
module_logger.propagate = False  # Prevent passing log messages to the root logger if it's configured separately

# File Handler: Writes logs to a file in the 'logs' directory.
file_handler = logging.FileHandler(os.path.join(log_dir, 'flask_app.log'), mode='a')
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
module_logger.addHandler(file_handler)

# Console Handler: Outputs logs to the console (stderr by default).
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
module_logger.addHandler(stream_handler)

# Use this configured logger as the primary logger for the application.
# This replaces Flask's default unconfigured logger.
logger = module_logger


# ---- Flask App Initialization ----
app = Flask(__name__)
app.logger = logger  # Assign the configured logger to the Flask app instance.
logger.info("Flask application initialized.")


# ---- Application Configuration ----
# Database URI: Loaded from environment variable. Critical for database operations.
mongo_db_uri = os.getenv('MONGODB_URI')
if not mongo_db_uri:
    logger.critical("CRITICAL: MONGODB_URI environment variable not set. Database will not be available.")
    # Consider raising an error or exiting if DB is essential for startup:
    # raise EnvironmentError("Critical: MONGODB_URI is not set, cannot start application.")
app.config["MONGO_URI"] = mongo_db_uri
logger.info(f"MongoDB URI set from environment (length: {len(mongo_db_uri) if mongo_db_uri else 0}).")


# ---- Database Initialization ----
# Initialize Flask-PyMongo extension.
try:
    if mongo_db_uri: # Only attempt init if URI was found
        init_db(app)
        logger.info("Flask-PyMongo database initialized successfully.")
    else:
        logger.warning("Database initialization skipped due to missing MONGODB_URI.")
except ValueError as e: # Catch errors from init_db, e.g., if URI is invalid
    logger.error(f"Flask-PyMongo database initialization failed: {e}", exc_info=True)
    # Depending on severity, might re-raise or exit.
    # For now, app continues, but DB-dependent routes will fail.


# ---- CORS (Cross-Origin Resource Sharing) Setup ----
# Configures which frontend origins are allowed to make requests to this API.
# For development, allowing "*" is common. For production, specify exact frontend domain(s).
# Example: origins=["http://localhost:3000", "https://your.production.domain"]
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*").split(",")}})
logger.info(f"Flask-CORS initialized for API routes. Allowed origins: {os.getenv('CORS_ORIGINS', '*')}")


# ---- APScheduler (Background Task Scheduler) Setup ----
scheduler = BackgroundScheduler(daemon=True, logger=logger) # Pass app logger to APScheduler

def scheduled_scraping_job():
    """Scheduled job to run the news scraping task."""
    # It's important that this job runs within an app context if it needs access to
    # app config, extensions (like PyMongo via current_app), or other app-bound resources.
    with app.app_context():
        logger.info("APScheduler: Triggering scheduled news scraping task.")
        try:
            # run_scraping_task is expected to handle its own errors and logging internally.
            # It now also triggers analysis if new articles are stored.
            result = run_scraping_task()
            logger.info(f"APScheduler: Scheduled scraping task finished. Status: {result.get('status', 'unknown')}, Articles Stored: {result.get('articles_stored', 0)}")
            if 'analysis_triggered_result' in result:
                logger.info(f"APScheduler: Analysis triggered by scraper. Analysis Status: {result['analysis_triggered_result'].get('status', 'unknown')}")
        except Exception as e:
            # This top-level catch is for unexpected errors in the task execution itself.
            logger.error(f"APScheduler: Unhandled error during scheduled scraping task: {e}", exc_info=True)

# Configure the scraping job interval using an environment variable (default: 4 hours).
scrape_interval_hours = int(os.getenv('SCRAPE_INTERVAL_HOURS', "4"))
if scrape_interval_hours > 0:
    scheduler.add_job(
        id='scheduled_scraping_job', # Job ID for easier management
        func=scheduled_scraping_job,
        trigger='interval',
        hours=scrape_interval_hours,
        replace_existing=True # Replace job if it already exists from a previous run (e.g. due to reloader)
    )
    logger.info(f"APScheduler: Scraping job scheduled to run every {scrape_interval_hours} hours.")
else:
    logger.warning("APScheduler: SCRAPE_INTERVAL_HOURS is set to 0 or less. Scheduled scraping is disabled.")

# Start the scheduler if it's not already running (e.g., in some dev environments with reloader).
# It's generally better to start it only once.
if os.getenv('FLASK_ENV') != 'testing': # Don't run scheduler during tests by default
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler started successfully.")
    except Exception as e: # Catch potential errors during scheduler start (e.g., issues with timezone on some systems)
        logger.error(f"APScheduler: Failed to start: {e}", exc_info=True)
else:
    logger.info("APScheduler: Not starting scheduler in TESTING environment.")


# ---- Global Request Hooks ----
@app.before_request
def log_request_info():
    """Logs incoming request details before each request is processed."""
    # For DEBUG level, log more details including args and small JSON bodies.
    if logger.isEnabledFor(logging.DEBUG):
        debug_message = f"Incoming Request: {request.method} {request.url} from {request.remote_addr}"
        if request.args:
            debug_message += f" Query Params: {request.args.to_dict()}"
        if request.is_json and request.content_length is not None and request.content_length > 0:
            try:
                json_body = request.get_json(silent=True) # Use silent=True to avoid raising error on parse failure
                if json_body is None: # If parsing failed or content_type is wrong
                     debug_message += " JSON Body: (Could not parse or not valid JSON)"
                elif len(str(json_body)) < 1000:  # Log small JSON bodies fully
                    debug_message += f" JSON Body: {json_body}"
                else:  # For larger bodies, log keys and size to avoid overly verbose logs
                    debug_message += f" JSON Body: (Keys: {list(json_body.keys())}, Size: {request.content_length} bytes)"
            except Exception as e: # Catch any error during get_json or processing
                logger.warning(f"Could not log JSON body for request {request.path}: {e}", exc_info=True)
                debug_message += " JSON Body: (Error logging body)"
        logger.debug(debug_message)
    else: # For INFO level, log a more concise message.
        logger.info(f"Incoming Request: {request.method} {request.url} from {request.remote_addr}")


@app.after_request
def log_response_info(response):
    """Logs outgoing response details after each request is processed."""
    logger.info(
        f"Outgoing Response: {request.method} {request.url} - Status: {response.status_code} ({response.content_length} bytes)"
    )
    return response


# ---- Global Error Handlers ----
# These handlers ensure that errors are returned in a consistent JSON format.
@app.errorhandler(400) # Bad Request
def handle_bad_request_error(error):
    """Handles 400 Bad Request errors with a JSON response."""
    logger.warning(f"Bad Request (400): {error.description if hasattr(error, 'description') else 'Invalid request'}. URL: {request.url}")
    return error_response(
        getattr(error, 'description', 'The browser (or proxy) sent a request that this server could not understand.'),
        400
    )

@app.errorhandler(401) # Unauthorized
def handle_unauthorized_error(error):
    """Handles 401 Unauthorized errors with a JSON response."""
    logger.warning(f"Unauthorized (401): {error.description if hasattr(error, 'description') else 'Authentication required'}. URL: {request.url}")
    return error_response(getattr(error, 'description', 'Valid authentication is required to access this resource.'), 401)

@app.errorhandler(403) # Forbidden
def handle_forbidden_error(error):
    """Handles 403 Forbidden errors with a JSON response."""
    logger.warning(f"Forbidden (403): {error.description if hasattr(error, 'description') else 'Access denied'}. URL: {request.url}")
    return error_response(getattr(error, 'description', 'You do not have the permission to access the requested resource.'), 403)

@app.errorhandler(404) # Not Found
def handle_not_found_error(error):
    """Handles 404 Not Found errors with a JSON response."""
    logger.info(f"Not Found (404): Resource at {request.url} not found. {error.description if hasattr(error, 'description') else ''}")
    return error_response(getattr(error, 'description', 'The requested resource was not found on the server.'), 404)

@app.errorhandler(405) # Method Not Allowed
def handle_method_not_allowed_error(error):
    """Handles 405 Method Not Allowed errors with a JSON response."""
    logger.warning(f"Method Not Allowed (405): Method '{request.method}' not supported for URL '{request.url}'. {error.description if hasattr(error, 'description') else ''}")
    return error_response(
        getattr(error, 'description', f"The method {request.method} is not allowed for the requested URL."),
        405
    )

@app.errorhandler(Exception)  # Catch-all for 500s and other unhandled exceptions
def handle_internal_server_error(error):
    """
    Handles any unhandled exceptions (resulting in 500 Internal Server Error)
    with a generic JSON error message and logs the full exception trace.
    """
    logger.error(f"Unhandled Exception caught by global handler: {error}", exc_info=True)

    # If the error is a known werkzeug HTTPException (like a 500 explicitly raised),
    # it might have specific attributes. Otherwise, it's an unexpected exception.
    if hasattr(error, 'code') and isinstance(error.code, int) and error.code != 500:
        # This case handles non-500 HTTPExceptions that might bubble up if not caught by specific handlers.
        # It's a bit of a safeguard.
        return error_response(getattr(error, 'description', 'An HTTP exception occurred.'), error.code)

    # For all other exceptions, or explicit 500s:
    return error_response('An unexpected internal server error occurred. Please try again later.', 500)


# ---- Core API Endpoints ----
# These are simple, direct routes. More complex routes are in Blueprints.

@app.route('/')
def hello_world():
    """A simple root endpoint to confirm the app is running."""
    logger.info("Root endpoint '/' accessed successfully.")
    return jsonify({"message": "Hello, World! This is the TruthGuard Flask Backend. Logging is active.", "status": "ok"})


@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """
    Triggers the news scraping task.
    This is an asynchronous operation initiated by this endpoint.
    Returns:
        JSON response indicating task initiation status.
    """
    logger.info("API: Received request to trigger news scraping task.")
    # In a more complex app, you might check for active jobs or add to a queue.
    # Here, we directly call the task (which is synchronous in its current form).
    try:
        # Call the scraping task
        # The task should ideally run in a background thread if it's very long,
        # to avoid tying up the HTTP request.
        # For now, run_scraping_task is synchronous.
        # Consider using Flask-Executor or Celery for long tasks.

        # For immediate execution outside of the scheduler's cycle:
        stats = run_scraping_task()

        if stats.get("status") == "error":
            logger.error(f"Manual scraping task failed. Stats: {stats}")
            return jsonify({"status": "error", "message": stats.get("message", "Scraping failed"), "details": stats.get("details")}), 500

        logger.info(f"Manual scraping task completed. Stats: {stats}")
        return jsonify({
            "status": "success",
            "message": "Scraping task initiated and completed.",
            "data": stats
        }), 200

    except Exception as e:
        logger.error(f"Exception when trying to run manual scrape: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected error occurred while trying to start scraping."}), 500

@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    logger.info("'/api/scheduler/status' GET endpoint called.")
    if scheduler.running:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run_time": str(job.next_run_time) if job.next_run_time else None
            })
        return jsonify({"status": "running", "jobs": jobs}), 200
    else:
        return jsonify({"status": "not_running"}), 200

@app.route('/api/analyze', methods=['POST'])
def trigger_analysis():
    logger.info("'/api/analyze' POST endpoint called.")
    # Add authentication/authorization here in a real app

    # Get batch_size from request or use default from env
    try:
        data = request.get_json()
        batch_size = int(data.get('batch_size', os.getenv('BATCH_SIZE_ANALYSIS', "10")))
    except Exception: # Broad exception for if get_json fails or batch_size is not int
        batch_size = int(os.getenv('BATCH_SIZE_ANALYSIS', "10"))
        logger.warning(f"Could not parse batch_size from request, using default: {batch_size}")


    logger.info(f"Initiating manual analysis task with batch_size: {batch_size}...")
    try:
        # Call the analysis task
        # Similar to scraping, this is synchronous. Consider background tasks for long analyses.
        stats = run_analysis_task(batch_size=batch_size)

        if stats.get("status") == "error":
            logger.error(f"Manual analysis task failed. Stats: {stats}")
            return jsonify({"status": "error", "message": stats.get("message", "Analysis failed"), "details": stats.get("details")}), 500

        logger.info(f"Manual analysis task completed. Stats: {stats}")
        return jsonify({
            "status": "success",
            "message": "Analysis task initiated and completed.",
            "data": stats
        }), 200

    except Exception as e:
        logger.error(f"Exception when trying to run manual analysis: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected error occurred while trying to start analysis."}), 500


# It's good practice to ensure the scheduler shuts down when the app exits.
import atexit
atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

if __name__ == '__main__':
    # Note: FLASK_ENV and FLASK_DEBUG are typically set by environment variables
    # or when running `flask run`. Setting them here is mostly for direct `python app.py` execution.
    is_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5001)) # Changed port to avoid conflict with Next.js
    logger.info(f"Starting Flask app in {'debug' if is_debug else 'production'} mode on port {port}")

    # When running with `python app.py`, the reloader can cause the scheduler to start twice.
    # The `use_reloader=False` is important here if you manage the scheduler instance directly
    # and don't want it duplicated or to face issues with job persistence across reloads.
    # However, for development, the reloader is very useful.
    # The check `if not scheduler.running:` above helps mitigate some issues with the reloader.
    # If deploying with Gunicorn/uWSGI, they manage workers differently.

    # ---- Register Blueprints ----
    from .routes.articles import articles_bp
    from .routes.trends import trends_bp
    from .routes.analytics import analytics_bp

    app.register_blueprint(articles_bp, url_prefix='/api')
    app.register_blueprint(trends_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    logger.info("API Blueprints registered.")

    app.run(debug=is_debug, port=port, host='0.0.0.0', use_reloader=is_debug)
