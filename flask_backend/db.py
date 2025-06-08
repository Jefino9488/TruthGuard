# -*- coding: utf-8 -*-
"""
Database initialization and configuration for the Flask application.

This module initializes the Flask-PyMongo extension and creates necessary
MongoDB indexes when the application starts. It relies on the MONGO_URI
being set in the Flask application's configuration.
"""
from flask_pymongo import PyMongo
import pymongo # For pymongo.ASCENDING, pymongo.DESCENDING, and error handling

# Global PyMongo instance.
# This will be initialized with the Flask app context.
mongo = PyMongo()

def init_db(app):
    """
    Initializes the PyMongo extension and ensures essential MongoDB indexes.

    This function is called during Flask app setup. It configures PyMongo
    using the MONGO_URI from the app's config and then attempts to create
    several indexes on the 'articles' collection to optimize common queries.

    Args:
        app (Flask): The Flask application instance.

    Raises:
        ValueError: If MONGO_URI is not found in the app configuration.
    """
    mongo_uri = app.config.get("MONGO_URI") # Get URI from Flask app config
    if not mongo_uri:
        app.logger.error("MONGO_URI not found in Flask app config during init_db.")
        raise ValueError("MONGO_URI not found in Flask app config. Please set it.")

    # Initialize PyMongo with the app. Flask-PyMongo will use app.config["MONGO_URI"].
    mongo.init_app(app)
    app.logger.info("Flask-PyMongo extension initialized.")

    # --- Verify MongoDB Connection and Database Object ---
    if mongo.cx is None:
        app.logger.critical("MongoDB client (mongo.cx) is None after init_app. Check MONGODB_URI and server status.")
        raise RuntimeError("Failed to connect to MongoDB: Client connection is None. Verify MONGODB_URI and ensure the MongoDB server is accessible.")

    if mongo.db is None:
        app.logger.critical("MongoDB database object (mongo.db) is None after init_app. This usually means the database specified in MONGODB_URI is inaccessible or does not exist, or there's an issue with authentication/authorization.")
        raise RuntimeError("Failed to connect to MongoDB: Database object is None. Verify MONGODB_URI (including database name, user, password) and ensure the MongoDB server is accessible and configured correctly.")

    app.logger.info(f"MongoDB connection client: {mongo.cx}")
    app.logger.info(f"MongoDB database object: {mongo.db.name}")


    # --- Create Indexes after PyMongo is initialized ---
    # This ensures that critical indexes for querying are present.
    # `create_index` is idempotent; it only creates an index if it doesn't already exist or if the definition has changed.
    # These indexes support common query patterns used by the API.
    # Scraper/Analyzer modules might create their own specific indexes (e.g., text index).
    app.logger.info("Attempting to ensure MongoDB indexes for 'articles' collection...")
    try:
        # It's good practice to have the app context available for `mongo.db`
        # Although with recent Flask versions and Flask-PyMongo, mongo.db might be accessible
        # directly after init_app if the app context from init_db's call is still effectively active.
        # Using app_context() explicitly here is safer.
        with app.app_context():
            # We've already checked mongo.db is not None, so this access should be safe.
            articles_collection = mongo.db.articles

            # Indexes for common sorting and filtering fields in the API
            articles_collection.create_index([("published_at", pymongo.DESCENDING)], background=True, name="idx_published_at_desc")
            articles_collection.create_index([("source", pymongo.ASCENDING)], background=True, name="idx_source_asc")
            articles_collection.create_index([("processing_status", pymongo.ASCENDING)], background=True, name="idx_processing_status_asc")
            articles_collection.create_index([("bias_score", pymongo.DESCENDING)], background=True, name="idx_bias_score_desc")
            articles_collection.create_index([("credibility_score", pymongo.DESCENDING)], background=True, name="idx_credibility_score_desc")
            articles_collection.create_index([("misinformation_risk", pymongo.DESCENDING)], background=True, name="idx_misinfo_risk_desc")
            articles_collection.create_index([("sentiment", pymongo.ASCENDING)], background=True, name="idx_sentiment_asc")
            articles_collection.create_index([("analyzed_at", pymongo.DESCENDING)], background=True, name="idx_analyzed_at_desc")
            articles_collection.create_index([("scraped_at", pymongo.DESCENDING)], background=True, name="idx_scraped_at_desc")
            # Note: The unique index on 'article_id' and the text index on 'title'/'content'
            # are expected to be created by the scraper.py module when it first runs.
            # Adding them here as well would be redundant but safe.

            app.logger.info("Successfully ensured API-related MongoDB indexes for 'articles' collection.")
    except pymongo.errors.ConnectionFailure as cf_err:
        app.logger.error(f"MongoDB ConnectionFailure during index creation: {cf_err}", exc_info=True)
        # This might indicate the DB is not reachable. The app might still run but DB operations will fail.
    except pymongo.errors.OperationFailure as op_err:
        app.logger.error(f"MongoDB OperationFailure during index creation: {op_err}", exc_info=True)
        # This could be due to permissions issues or other operational problems.
    except Exception as e:
        # Catch any other unexpected errors during index creation.
        app.logger.error(f"An unexpected error occurred creating MongoDB indexes: {e}", exc_info=True)

# Example helper function (optional, can also use mongo.db directly in routes)
# def get_articles_collection():
#     """Returns the 'articles' collection instance."""
#     return mongo.db.articles
