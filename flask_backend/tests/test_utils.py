import pytest
from flask import Flask, jsonify, make_response as flask_make_response
from bson import ObjectId
from datetime import datetime, date
from unittest.mock import MagicMock

# Assuming utils.py is in flask_backend directory, and tests are run from project root
# or flask_backend is in PYTHONPATH.
from flask_backend.utils import (
    CustomJSONEncoder,
    serialize_mongo_doc,
    make_json_response as util_make_json_response, # Alias to avoid conflict
    error_response as util_error_response, # Alias
    get_pagination_params,
    paginate_query
)

# --- Tests for CustomJSONEncoder and serialize_mongo_doc ---
def test_custom_json_encoder_objectid():
    obj_id = ObjectId()
    encoded = CustomJSONEncoder().encode({"_id": obj_id})
    # Encoded will be a JSON string: '{"_id": "str(obj_id)"}'
    # We need to load it back to check the value
    import json
    assert json.loads(encoded) == {"_id": str(obj_id)}

def test_custom_json_encoder_datetime():
    dt = datetime(2023, 1, 1, 12, 30, 0)
    encoded = CustomJSONEncoder().encode({"timestamp": dt})
    assert json.loads(encoded) == {"timestamp": dt.isoformat()}

def test_custom_json_encoder_date():
    d = date(2023, 1, 1)
    encoded = CustomJSONEncoder().encode({"event_date": d})
    assert json.loads(encoded) == {"event_date": d.isoformat()}

def test_serialize_mongo_doc_single():
    obj_id = ObjectId()
    dt = datetime.utcnow()
    doc = {"_id": obj_id, "name": "Test Item", "created_at": dt, "value": 123}
    serialized = serialize_mongo_doc(doc)
    assert isinstance(serialized, dict)
    assert serialized["_id"] == str(obj_id)
    assert serialized["name"] == "Test Item"
    assert serialized["created_at"] == dt.isoformat()
    assert serialized["value"] == 123

def test_serialize_mongo_doc_list():
    obj_id1 = ObjectId()
    obj_id2 = ObjectId()
    docs = [
        {"_id": obj_id1, "name": "Item 1"},
        {"_id": obj_id2, "name": "Item 2"}
    ]
    serialized_list = serialize_mongo_doc(docs)
    assert isinstance(serialized_list, list)
    assert len(serialized_list) == 2
    assert serialized_list[0]["_id"] == str(obj_id1)
    assert serialized_list[1]["name"] == "Item 2"

def test_serialize_mongo_doc_none():
    assert serialize_mongo_doc(None) is None

# --- Tests for make_json_response and error_response ---
# These need an app context to run jsonify
def test_make_json_response_success(app): # app fixture from conftest
    with app.test_request_context(): # To allow jsonify to work
        obj_id = ObjectId()
        data = {"_id": obj_id, "message": "Success"}
        response = util_make_json_response(data, 200)
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["_id"] == str(obj_id)
        assert json_data["message"] == "Success"

def test_make_json_response_error_dict(app):
    with app.test_request_context():
        error_data = {"status": "error", "message": "Preformatted error"}
        response = util_make_json_response(error_data, 400)
        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data == error_data

def test_util_error_response(app):
    with app.test_request_context():
        response = util_error_response("Test error message", 403)
        assert response.status_code == 403
        json_data = response.get_json()
        assert json_data["status"] == "error"
        assert json_data["message"] == "Test error message"

# --- Tests for Pagination Helpers ---
def test_get_pagination_params_defaults():
    mock_request_args = {}
    page, per_page = get_pagination_params(mock_request_args)
    assert page == 1
    assert per_page == 10

def test_get_pagination_params_custom():
    mock_request_args = {'page': '3', 'per_page': '25'}
    page, per_page = get_pagination_params(mock_request_args)
    assert page == 3
    assert per_page == 25

def test_get_pagination_params_invalid():
    mock_request_args = {'page': 'invalid', 'per_page': '-5'}
    page, per_page = get_pagination_params(mock_request_args)
    assert page == 1  # Falls back to default
    assert per_page == 10 # Falls back to default

def test_get_pagination_params_limits():
    mock_request_args = {'page': '0', 'per_page': '200'}
    page, per_page = get_pagination_params(mock_request_args)
    assert page == 1 # Min page is 1
    assert per_page == 100 # Max per_page is 100

def test_paginate_query():
    mock_collection = MagicMock()

    # Mock data items
    item1_id = ObjectId()
    item2_id = ObjectId()
    items_data = [
        {"_id": item1_id, "name": "Item 1", "value": 100},
        {"_id": item2_id, "name": "Item 2", "value": 200}
    ]

    # Configure mock collection's methods
    mock_collection.count_documents.return_value = 2

    # Mock the find query chain
    mock_find_query = MagicMock()
    mock_collection.find.return_value = mock_find_query
    mock_find_query.sort.return_value = mock_find_query # sort returns self
    mock_find_query.skip.return_value = mock_find_query  # skip returns self
    mock_find_query.limit.return_value = items_data[:1] # limit returns a list of docs

    page = 1
    per_page = 1
    filter_criteria = {"status": "active"}
    sort_criteria = [("value", -1)] # PyMongo.DESCENDING

    paginated_items, total_count = paginate_query(
        None, # query object (first arg) is not used in the current paginate_query implementation
        mock_collection,
        page,
        per_page,
        filter_criteria=filter_criteria,
        sort_criteria=sort_criteria
    )

    mock_collection.count_documents.assert_called_once_with(filter_criteria)
    mock_collection.find.assert_called_once_with(filter_criteria)
    mock_find_query.sort.assert_called_once_with(sort_criteria)
    mock_find_query.skip.assert_called_once_with(0) # (1-1)*1
    mock_find_query.limit.assert_called_once_with(per_page)

    assert total_count == 2
    assert len(paginated_items) == 1
    assert paginated_items[0]["name"] == "Item 1"

def test_paginate_query_no_sort_no_filter():
    mock_collection = MagicMock()
    items_data = [{"name": "Item 1"}, {"name": "Item 2"}]
    mock_collection.count_documents.return_value = 2

    mock_find_query = MagicMock()
    mock_collection.find.return_value = mock_find_query
    mock_find_query.skip.return_value = mock_find_query
    mock_find_query.limit.return_value = items_data

    page = 1
    per_page = 10

    paginated_items, total_count = paginate_query(
        None, mock_collection, page, per_page
    )

    mock_collection.count_documents.assert_called_once_with({})
    mock_collection.find.assert_called_once_with({})
    mock_find_query.sort.assert_not_called() # No sort criteria
    mock_find_query.skip.assert_called_once_with(0)
    mock_find_query.limit.assert_called_once_with(per_page)

    assert total_count == 2
    assert len(paginated_items) == 2
