import json
from bson import ObjectId
from datetime import datetime, date

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder that handles MongoDB ObjectId and datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def serialize_mongo_doc(doc):
    """
    Serializes a MongoDB document (or a list of documents) using the CustomJSONEncoder.
    This converts ObjectId and datetime objects to strings.
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [json.loads(json.dumps(item, cls=CustomJSONEncoder)) for item in doc]
    return json.loads(json.dumps(doc, cls=CustomJSONEncoder))

# Example usage within a Flask route:
# from flask import jsonify
# from .utils import serialize_mongo_doc
#
# @app.route('/some_data')
# def get_some_data():
#     data_from_mongo = mongo.db.my_collection.find_one()
#     return jsonify(serialize_mongo_doc(data_from_mongo))

def make_json_response(data, status_code=200):
    """
    Creates a Flask JSON response, automatically serializing MongoDB documents.
    :param data: The data to be JSONified. Can be a single MongoDB doc or a list.
    :param status_code: HTTP status code for the response.
    :return: Flask Response object.
    """
    from flask import current_app, jsonify # Local import to avoid circular dependency issues at module level

    if isinstance(data, dict) and data.get("status") == "error": # If it's already an error dict
        return jsonify(data), status_code

    # Use current_app.json_encoder if available and configured, otherwise fallback
    # For Flask-PyMongo, it often replaces the default encoder.
    # However, explicit serialization before jsonify can be more robust.
    serialized_data = serialize_mongo_doc(data)
    return jsonify(serialized_data), status_code

def error_response(message, status_code):
    """
    Creates a standardized JSON error response.
    :param message: Error message string.
    :param status_code: HTTP status code.
    :return: Flask Response object.
    """
    from flask import jsonify # Local import
    return jsonify({"status": "error", "message": message}), status_code

# --- Pagination Helper ---
def get_pagination_params(request_args):
    """
    Extracts and validates pagination parameters (page, per_page) from request arguments.
    """
    try:
        page = int(request_args.get('page', 1))
        per_page = int(request_args.get('per_page', 10)) # Default 10 items per page
        if page < 1: page = 1
        if per_page < 1: per_page = 1
        if per_page > 100: per_page = 100 # Max 100 items per page
    except ValueError:
        page = 1
        per_page = 10
    return page, per_page

def paginate_query(query, collection, page, per_page, filter_criteria=None, sort_criteria=None):
    """
    Paginates a MongoDB query.
    Args:
        query: The base pymongo find query (e.g., mongo.db.articles.find(filter_criteria)).
               This argument is somewhat redundant if filter_criteria is passed and used directly.
               Let's simplify to just pass the collection and criteria.
        collection: The PyMongo collection object.
        page: Current page number.
        per_page: Items per page.
        filter_criteria: Dictionary for MongoDB find() method.
        sort_criteria: List of tuples for MongoDB sort() method, e.g., [('published_at', -1)].
    Returns:
        A tuple: (paginated_results_list, total_items_count)
    """
    if filter_criteria is None:
        filter_criteria = {}

    total_items = collection.count_documents(filter_criteria)

    find_query = collection.find(filter_criteria)

    if sort_criteria:
        find_query = find_query.sort(sort_criteria)

    items = list(find_query.skip((page - 1) * per_page).limit(per_page))

    return items, total_items
