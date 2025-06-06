import pytest
import json
from unittest.mock import patch, MagicMock
from bson import ObjectId
from datetime import datetime

# Assuming client and patched_mongo_db fixtures are from conftest.py

def test_get_articles_list_empty(client, patched_mongo_db):
    """Test GET /api/articles when no articles exist."""
    patched_mongo_db.find.return_value.sort.return_value.skip.return_value.limit.return_value = []
    patched_mongo_db.count_documents.return_value = 0

    response = client.get('/api/articles')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['articles'] == []
    assert json_data['total_articles'] == 0
    assert json_data['page'] == 1
    assert json_data['per_page'] == 10

    patched_mongo_db.find.assert_called_once_with({}) # Default empty filter
    patched_mongo_db.count_documents.assert_called_once_with({})


def test_get_articles_list_with_data(client, patched_mongo_db):
    """Test GET /api/articles with some articles."""
    article1_id = ObjectId()
    article2_id = ObjectId()
    mock_articles = [
        {"_id": article1_id, "title": "Article 1", "source": "Source A", "published_at": datetime.utcnow()},
        {"_id": article2_id, "title": "Article 2", "source": "Source B", "published_at": datetime.utcnow()}
    ]
    # Simulate the chained calls for pagination
    patched_mongo_db.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_articles
    patched_mongo_db.count_documents.return_value = len(mock_articles)

    response = client.get('/api/articles?page=1&per_page=5')
    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data['total_articles'] == 2
    assert len(json_data['articles']) == 2
    assert json_data['articles'][0]['title'] == "Article 1"
    assert json_data['articles'][0]['_id'] == str(article1_id) # Check serialization
    assert json_data['page'] == 1
    assert json_data['per_page'] == 5

    patched_mongo_db.find.assert_called_once_with({})
    # Check that sort was called (default is 'published_at', -1)
    patched_mongo_db.find.return_value.sort.assert_called_once_with([('published_at', -1)])


def test_get_articles_with_filtering_and_sorting(client, patched_mongo_db):
    """Test GET /api/articles with filtering and sorting query parameters."""
    mock_articles = [{"_id": ObjectId(), "title": "Filtered Article", "source": "Test Source"}]
    patched_mongo_db.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_articles
    patched_mongo_db.count_documents.return_value = 1

    response = client.get('/api/articles?source=Test%20Source&sort_by=title&sort_order=asc')
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['articles']) == 1
    assert json_data['articles'][0]['title'] == "Filtered Article"

    expected_filter = {'source': {'$regex': '^Test Source$', '$options': 'i'}}
    patched_mongo_db.find.assert_called_once_with(expected_filter)
    patched_mongo_db.count_documents.assert_called_once_with(expected_filter)
    patched_mongo_db.find.return_value.sort.assert_called_once_with([('title', 1)])


def test_get_single_article_found(client, patched_mongo_db):
    """Test GET /api/articles/<id> when article is found."""
    article_id = ObjectId()
    mock_article = {"_id": article_id, "title": "Specific Article", "content": "Details here"}
    patched_mongo_db.find_one.return_value = mock_article

    response = client.get(f'/api/articles/{str(article_id)}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['_id'] == str(article_id)
    assert json_data['title'] == "Specific Article"

    patched_mongo_db.find_one.assert_called_once_with({'_id': article_id})

def test_get_single_article_not_found(client, patched_mongo_db):
    """Test GET /api/articles/<id> when article is not found."""
    article_id = ObjectId()
    patched_mongo_db.find_one.return_value = None

    response = client.get(f'/api/articles/{str(article_id)}')
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "Article not found" in json_data['message']

    patched_mongo_db.find_one.assert_called_once_with({'_id': article_id})


def test_create_article_success(client, patched_mongo_db):
    """Test POST /api/articles for successful creation."""
    new_article_data = {
        "title": "New Test Article",
        "url": "http://example.com/new_article",
        "source": "Test Source Inc",
        "content": "This is the content.",
        "description": "A brief description.",
        "published_at": datetime.utcnow().isoformat()
    }

    # Mock count_documents for duplicate URL check
    patched_mongo_db.count_documents.return_value = 0

    # Mock insert_one result
    inserted_id = ObjectId()
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = inserted_id
    patched_mongo_db.insert_one.return_value = mock_insert_result

    # Mock find_one to return the "created" article
    created_doc_mock = {**new_article_data, "_id": inserted_id, "scraped_at": datetime.utcnow()}
    # Convert published_at back to datetime for the mock as it would be in DB
    created_doc_mock["published_at"] = datetime.fromisoformat(new_article_data["published_at"])
    patched_mongo_db.find_one.return_value = created_doc_mock

    response = client.post('/api/articles', data=json.dumps(new_article_data), content_type='application/json')

    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == "Article created successfully."
    assert json_data['article']['_id'] == str(inserted_id)
    assert json_data['article']['title'] == new_article_data['title']

    patched_mongo_db.count_documents.assert_called_once_with({'url': new_article_data['url']}, limit=1)
    # Check that insert_one was called (argument matching can be complex, check for call at least)
    patched_mongo_db.insert_one.assert_called_once()
    # Check that find_one was called to retrieve the created document
    patched_mongo_db.find_one.assert_called_once_with({'_id': inserted_id})


def test_create_article_validation_error(client):
    """Test POST /api/articles with missing required fields."""
    incomplete_data = {"url": "http://example.com/incomplete"} # Missing title, source
    response = client.post('/api/articles', data=json.dumps(incomplete_data), content_type='application/json')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'title' in json_data['message'] # Expecting error message about title
    assert 'source' in json_data['message']


def test_create_article_duplicate_url(client, patched_mongo_db):
    """Test POST /api/articles with a duplicate URL."""
    new_article_data = {
        "title": "Duplicate URL Article",
        "url": "http://example.com/duplicate_url",
        "source": "Source D",
        "published_at": datetime.utcnow().isoformat()
    }
    # Simulate that a document with this URL already exists
    patched_mongo_db.count_documents.return_value = 1

    response = client.post('/api/articles', data=json.dumps(new_article_data), content_type='application/json')
    assert response.status_code == 409 # Conflict
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "already exists" in json_data['message']

    patched_mongo_db.count_documents.assert_called_once_with({'url': new_article_data['url']}, limit=1)


def test_update_article_success(client, patched_mongo_db):
    """Test PUT /api/articles/<id> for successful update."""
    article_id = ObjectId()
    update_data = {"title": "Updated Title", "content": "Updated content."}

    # Mock update_one result
    mock_update_result = MagicMock()
    mock_update_result.matched_count = 1
    patched_mongo_db.update_one.return_value = mock_update_result

    # Mock find_one to return the "updated" article
    updated_doc_mock = {"_id": article_id, **update_data, "updated_at": datetime.utcnow()}
    patched_mongo_db.find_one.return_value = updated_doc_mock

    response = client.put(f'/api/articles/{str(article_id)}', data=json.dumps(update_data), content_type='application/json')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == "Article updated successfully."
    assert json_data['article']['title'] == "Updated Title"
    assert json_data['article']['_id'] == str(article_id)

    # Check that update_one was called (first arg is query, second is update doc)
    # The update doc includes '$set' and 'updated_at'
    patched_mongo_db.update_one.assert_called_once()
    args, kwargs = patched_mongo_db.update_one.call_args
    assert args[0] == {'_id': article_id} # Query
    assert '$set' in args[1]
    assert 'updated_at' in args[1]['$set']
    assert args[1]['$set']['title'] == update_data['title']


def test_update_article_not_found(client, patched_mongo_db):
    """Test PUT /api/articles/<id> when article to update is not found."""
    article_id = ObjectId()
    update_data = {"title": "No one home"}

    mock_update_result = MagicMock()
    mock_update_result.matched_count = 0 # Simulate no document matched the query
    patched_mongo_db.update_one.return_value = mock_update_result

    response = client.put(f'/api/articles/{str(article_id)}', data=json.dumps(update_data), content_type='application/json')
    assert response.status_code == 404
    json_data = response.get_json()
    assert "Article not found to update" in json_data['message']


def test_delete_article_success(client, patched_mongo_db):
    """Test DELETE /api/articles/<id> for successful deletion."""
    article_id = ObjectId()

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    patched_mongo_db.delete_one.return_value = mock_delete_result

    response = client.delete(f'/api/articles/{str(article_id)}')
    assert response.status_code == 200 # Or 204 if you prefer
    json_data = response.get_json()
    assert json_data['message'] == "Article deleted successfully."
    patched_mongo_db.delete_one.assert_called_once_with({'_id': article_id})


def test_delete_article_not_found(client, patched_mongo_db):
    """Test DELETE /api/articles/<id> when article to delete is not found."""
    article_id = ObjectId()

    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 0 # Simulate no document was deleted
    patched_mongo_db.delete_one.return_value = mock_delete_result

    response = client.delete(f'/api/articles/{str(article_id)}')
    assert response.status_code == 404
    json_data = response.get_json()
    assert "Article not found or already deleted" in json_data['message']
