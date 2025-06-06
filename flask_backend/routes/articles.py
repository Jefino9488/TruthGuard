# -*- coding: utf-8 -*-
"""
API Endpoints for Article Management.

This module defines the Blueprint for article-related operations, including
CRUD (Create, Read, Update, Delete) for articles. It handles requests related
to fetching, creating, modifying, and deleting news articles stored in the
MongoDB database.
"""
from flask import Blueprint, request, current_app
from bson import ObjectId
from ..db import mongo # mongo instance from flask_backend.db
from ..utils import make_json_response, error_response, get_pagination_params, paginate_query, serialize_mongo_doc
from datetime import datetime
import hashlib # For generating article_id if needed
import pymongo # For pymongo.errors

# Blueprint for article routes, prefixed with /api via app.py registration
articles_bp = Blueprint('articles_bp', __name__, url_prefix='/articles')


# --- Helper for Article Data Validation ---
def validate_article_data(data: dict, is_update: bool = False) -> dict:
    """
    Validates incoming article data for POST (create) and PUT (update) requests.

    Args:
        data (dict): The JSON data received in the request.
        is_update (bool): If True, some fields might be optional for updates.
                          Default is False (for creation, more fields required).

    Returns:
        dict: A dictionary of validation errors. Empty if data is valid.
    """
    errors = {}
    required_fields = ['title', 'url', 'source'] # Define core required fields

    if not is_update: # For new article creation
        for field in required_fields:
            if not data.get(field): # Check for presence and non-empty value
                errors[field] = f"Field '{field}' is required and cannot be empty."

    if "url" in data and data.get("url") and not data["url"].startswith(("http://", "https://")):
        errors["url"] = "Field 'url' must be a valid URL starting with 'http://' or 'https://'."

    if "published_at" in data and data.get("published_at"):
        try:
            # Attempt to parse, but actual conversion to datetime is done in the route
            datetime.fromisoformat(data["published_at"].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            errors["published_at"] = "Field 'published_at' must be a valid ISO 8601 datetime string."

    # Example: Validate numerical score fields if present
    score_fields = ['bias_score', 'misinformation_risk', 'credibility_score', 'sentiment']
    for field in score_fields:
        if field in data and data.get(field) is not None: # Check if field exists and is not None
            try:
                score = float(data[field])
                # Specific range checks, e.g., sentiment is -1 to 1, others 0 to 1
                if field == 'sentiment' and not (-1 <= score <= 1):
                    errors[field] = f"Field '{field}' must be a number between -1 and 1."
                elif field != 'sentiment' and not (0 <= score <= 1):
                    errors[field] = f"Field '{field}' must be a number between 0 and 1."
            except (ValueError, TypeError):
                errors[field] = f"Field '{field}' must be a valid number."
    return errors


# --- API Route Definitions ---
@articles_bp.route('', methods=['GET']) # Note: url_prefix='/articles' is on Blueprint
def list_articles():
    """
    Retrieve a list of articles with pagination, filtering, and sorting.

    Query Parameters:
        page (int, optional): Page number for pagination. Default: 1.
        per_page (int, optional): Number of articles per page. Default: 10. Max: 100.
        source (str, optional): Filter by source name (case-insensitive exact match).
        processing_status (str, optional): Filter by processing status (e.g., 'pending', 'analyzed').
        topic (str, optional): Filter by articles containing this topic/keyword in title, content, or description
                               (case-insensitive regex search).
        sort_by (str, optional): Field to sort by. Allowed fields: 'published_at', 'scraped_at',
                                 'analyzed_at', 'credibility_score', 'bias_score',
                                 'misinformation_risk', 'sentiment', 'source', 'title'.
                                 Default: 'published_at'.
        sort_order (str, optional): 'asc' or 'desc'. Default: 'desc'.

    Returns:
        JSON response: Paginated list of articles or error message.
    """
    current_app.logger.info("API: GET /articles called with args: %s", request.args)
    try:
        page, per_page = get_pagination_params(request.args)

        query_filters = {}

        # Filtering examples
        if 'source' in request.args:
            query_filters['source'] = {'$regex': f"^{request.args['source']}$", '$options': 'i'} # Exact match, case insensitive
        if 'processing_status' in request.args:
            query_filters['processing_status'] = request.args['processing_status']
        if 'topic' in request.args: # Basic text search on title and content
            topic_regex = {'$regex': request.args['topic'], '$options': 'i'}
            query_filters['$or'] = [{'title': topic_regex}, {'content': topic_regex}, {'description': topic_regex}]

        # Add more filters as needed: date ranges for published_at, score ranges, etc.
        # Example: Filter by credibility_score greater than a value
        # if 'min_credibility' in request.args:
        #     try:
        #         query_filters['credibility_score'] = {'$gte': float(request.args['min_credibility'])}
        #     except ValueError:
        #         return error_response("Invalid value for min_credibility.", 400)


        # Sorting
        sort_field = request.args.get('sort_by', 'published_at') # Default sort by published_at
        sort_order_str = request.args.get('sort_order', 'desc').lower()
        sort_order = -1 if sort_order_str == 'desc' else 1

        # Validate sort_field against a list of allowed fields to prevent arbitrary field sorting
        allowed_sort_fields = ['published_at', 'scraped_at', 'analyzed_at', 'credibility_score', 'bias_score', 'misinformation_risk', 'sentiment', 'source', 'title']
        if sort_field not in allowed_sort_fields:
            sort_field = 'published_at' # Default back if not allowed

        sort_criteria = [(sort_field, sort_order)]

        articles_cursor, total_articles = paginate_query(
            None, # query object not needed due to how paginate_query is structured
            mongo.db.articles,
            page,
            per_page,
            filter_criteria=query_filters,
            sort_criteria=sort_criteria
        )

        # Serialize after fetching from DB
        # articles_list = [serialize_mongo_doc(article) for article in articles_cursor]
        # The make_json_response will handle serialization.

        return make_json_response({
            'page': page,
            'per_page': per_page,
            'total_articles': total_articles,
            'articles': articles_cursor # Pass the list of dicts
        })

    except Exception as e:
        current_app.logger.error(f"Error listing articles: {e}", exc_info=True)
        return error_response("An unexpected error occurred while fetching articles.", 500)


@articles_bp.route('/articles/<string:article_id_str>', methods=['GET'])
def get_article(article_id_str):
    """
    Retrieve a single article by its MongoDB _id or custom article_id.
    """
    try:
        # Determine if article_id_str is a valid ObjectId, otherwise assume it's our custom 'article_id'
        query = {}
        if ObjectId.is_valid(article_id_str):
            query['_id'] = ObjectId(article_id_str)
        else:
            # If you have a unique 'article_id' field (like the md5 hash of URL)
            query['article_id'] = article_id_str

        article = mongo.db.articles.find_one(query)

        if not article:
            return error_response("Article not found.", 404)

        return make_json_response(article) # Serialization handled by make_json_response

    except Exception as e:
        current_app.logger.error(f"Error fetching article {article_id_str}: {e}", exc_info=True)
        return error_response(f"An error occurred while fetching the article: {str(e)}", 500)


@articles_bp.route('/articles', methods=['POST'])
def create_article():
    """
    Create a new article.
    Expects JSON data in the request body.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("Invalid JSON data in request body.", 400)

        validation_errors = validate_article_data(data)
        if validation_errors:
            return error_response(validation_errors, 400)

        # Check for duplicates based on URL (if applicable)
        if 'url' in data and mongo.db.articles.count_documents({'url': data['url']}, limit=1) > 0:
            return error_response(f"Article with URL '{data['url']}' already exists.", 409) # Conflict

        # Prepare document for insertion
        article_doc = {
            "title": data.get("title"),
            "url": data.get("url"),
            "source": data.get("source"),
            "content": data.get("content"),
            "description": data.get("description"),
            "published_at": datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None, # Ensure datetime object
            "scraped_at": datetime.utcnow(),
            "article_id": data.get("article_id") or hashlib.md5(data["url"].encode()).hexdigest() if data.get("url") else None, # Optional: generate if not provided
            "processing_status": data.get("processing_status", "pending_manual_creation"), # Custom status
            "data_source": data.get("data_source", "manual_api"),
            # Add other fields as needed, ensure they are sanitized or have defaults
            "ai_analysis": None,
            "bias_score": None,
            "misinformation_risk": None,
            # ... other analysis fields initialized to None or default
        }

        # Remove None values if you don't want them stored explicitly
        # article_doc = {k: v for k, v in article_doc.items() if v is not None}


        result = mongo.db.articles.insert_one(article_doc)

        # Fetch the inserted document to return it (optional, but good practice)
        created_article = mongo.db.articles.find_one({'_id': result.inserted_id})

        return make_json_response({
            "message": "Article created successfully.",
            "article": serialize_mongo_doc(created_article) # Ensure it's serialized for the response
        }, 201)

    except Exception as e:
        current_app.logger.error(f"Error creating article: {e}", exc_info=True)
        return error_response(f"An error occurred while creating the article: {str(e)}", 500)


@articles_bp.route('/articles/<string:article_id_str>', methods=['PUT'])
def update_article(article_id_str):
    """
    Update an existing article by its MongoDB _id or custom article_id.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("Invalid JSON data in request body.", 400)

        validation_errors = validate_article_data(data, is_update=True)
        if validation_errors:
            return error_response(validation_errors, 400)

        query = {}
        if ObjectId.is_valid(article_id_str):
            query['_id'] = ObjectId(article_id_str)
        else:
            query['article_id'] = article_id_str

        # Ensure URL uniqueness if it's being changed and needs to be unique
        if 'url' in data:
            existing_article_by_url = mongo.db.articles.find_one({'url': data['url']})
            if existing_article_by_url and str(existing_article_by_url['_id']) != article_id_str and (ObjectId.is_valid(article_id_str) and existing_article_by_url['_id'] != ObjectId(article_id_str)): # check if URL belongs to another doc
                 return error_response(f"Another article with URL '{data['url']}' already exists.", 409)


        update_doc = {"$set": {}}
        for key, value in data.items():
            if key == "published_at" and value:
                try:
                    update_doc["$set"][key] = datetime.fromisoformat(value)
                except ValueError:
                    return error_response(f"Invalid date format for published_at: {value}. Use ISO format.", 400)
            elif key not in ["_id", "article_id"]: # Don't allow changing these identifiers directly via $set
                update_doc["$set"][key] = value

        if not update_doc["$set"]:
            return error_response("No valid fields provided for update.", 400)

        update_doc["$set"]["updated_at"] = datetime.utcnow() # Add an updated_at timestamp

        result = mongo.db.articles.update_one(query, update_doc)

        if result.matched_count == 0:
            return error_response("Article not found to update.", 404)

        updated_article = mongo.db.articles.find_one(query)
        return make_json_response({
            "message": "Article updated successfully.",
            "article": serialize_mongo_doc(updated_article)
        })

    except Exception as e:
        current_app.logger.error(f"Error updating article {article_id_str}: {e}", exc_info=True)
        return error_response(f"An error occurred while updating the article: {str(e)}", 500)


@articles_bp.route('/articles/<string:article_id_str>', methods=['DELETE'])
def delete_article(article_id_str):
    """
    Delete an article by its MongoDB _id or custom article_id.
    """
    try:
        query = {}
        if ObjectId.is_valid(article_id_str):
            query['_id'] = ObjectId(article_id_str)
        else:
            query['article_id'] = article_id_str

        result = mongo.db.articles.delete_one(query)

        if result.deleted_count == 0:
            return error_response("Article not found or already deleted.", 404)

        return make_json_response({"message": "Article deleted successfully."}, 200) # Or 204 No Content

    except Exception as e:
        current_app.logger.error(f"Error deleting article {article_id_str}: {e}", exc_info=True)
        return error_response(f"An error occurred while deleting the article: {str(e)}", 500)

# Need to import hashlib for the POST route if article_id generation is used there
import hashlib
