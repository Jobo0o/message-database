import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Adjust the import path according to your project structure
# Assuming your main app is in src.api_v2.main
from src.api_v2.main import app, db
from src.models.message import Message  # For constructing expected responses

# Sample message data for mocking
SAMPLE_MESSAGE_DATA_1 = {
    "message_id": "test_id_001",
    "property": {"id": "prop1", "name": "Property Alpha"},
    "guest": {"name": "John Doe", "email": "john@example.com"},
    "content": "Hello from test 1",
    "timestamp": "2023-01-01T10:00:00Z",
    "direction": "incoming",
    "message_type": "manual",
    "created_at": "2023-01-01T10:00:00Z",
    "updated_at": "2023-01-01T10:00:00Z"
}

SAMPLE_MESSAGE_DATA_2 = {
    "message_id": "test_id_002",
    "property": {"id": "prop2", "name": "Property Beta"},
    "guest": {"name": "Jane Smith", "email": "jane@example.com"},
    "content": "Test message 2 here",
    "timestamp": "2023-01-02T11:00:00Z",
    "direction": "outgoing",
    "message_type": "automated",
    "created_at": "2023-01-02T11:00:00Z",
    "updated_at": "2023-01-02T11:00:00Z"
}

# Initialize the TestClient
client = TestClient(app)

# --- Test Cases ---

def test_read_root():
    """Test the root GET / endpoint."""
    # The TestClient is for the 'app' from api_v2.main, so paths are relative to that app's root.
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Message API V2"}


# --- Tests for GET /messages ---

@patch('src.api_v2.main.db.collection') # Patching the collection used by the endpoints
def test_list_messages_success(mock_collection):
    """Test GET /messages successfully returns a list of messages."""
    mock_messages = [SAMPLE_MESSAGE_DATA_1, SAMPLE_MESSAGE_DATA_2]
    mock_collection.find.return_value.skip.return_value.limit.return_value = mock_messages
    
    response = client.get("/messages?skip=0&limit=10")
    
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["message_id"] == SAMPLE_MESSAGE_DATA_1["message_id"]
    assert response_data[1]["content"] == SAMPLE_MESSAGE_DATA_2["content"]
    mock_collection.find.return_value.skip.assert_called_once_with(0)
    mock_collection.find.return_value.skip.return_value.limit.assert_called_once_with(10)

@patch('src.api_v2.main.db.collection')
def test_list_messages_pagination(mock_collection):
    """Test GET /messages with pagination parameters."""
    mock_messages = [SAMPLE_MESSAGE_DATA_2] # Assume only one message fits the pagination
    mock_collection.find.return_value.skip.return_value.limit.return_value = mock_messages
    
    response = client.get("/messages?skip=5&limit=5")
    
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["message_id"] == SAMPLE_MESSAGE_DATA_2["message_id"]
    mock_collection.find.return_value.skip.assert_called_once_with(5)
    mock_collection.find.return_value.skip.return_value.limit.assert_called_once_with(5)

@patch('src.api_v2.main.db.collection')
def test_list_messages_empty(mock_collection):
    """Test GET /messages when no messages are found."""
    mock_collection.find.return_value.skip.return_value.limit.return_value = []
    
    response = client.get("/messages")
    
    assert response.status_code == 200
    assert response.json() == []

@patch('src.api_v2.main.db.collection')
def test_list_messages_db_error(mock_collection):
    """Test GET /messages when a database error occurs."""
    from pymongo.errors import PyMongoError
    mock_collection.find.side_effect = PyMongoError("Simulated DB Error")
    
    response = client.get("/messages")
    
    assert response.status_code == 500
    assert response.json() == {"detail": "Error fetching messages from database"}

# --- Tests for GET /messages/{message_id} ---

@patch('src.api_v2.main.db.collection')
def test_get_message_success(mock_collection):
    """Test GET /messages/{message_id} successfully returns a single message."""
    mock_collection.find_one.return_value = SAMPLE_MESSAGE_DATA_1
    
    response = client.get(f"/messages/{SAMPLE_MESSAGE_DATA_1['message_id']}")
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message_id"] == SAMPLE_MESSAGE_DATA_1["message_id"]
    assert response_data["content"] == SAMPLE_MESSAGE_DATA_1["content"]
    mock_collection.find_one.assert_called_once_with({"message_id": SAMPLE_MESSAGE_DATA_1["message_id"]})

@patch('src.api_v2.main.db.collection')
def test_get_message_not_found(mock_collection):
    """Test GET /messages/{message_id} when the message is not found."""
    mock_collection.find_one.return_value = None
    test_id = "non_existent_id"
    
    response = client.get(f"/messages/{test_id}")
    
    assert response.status_code == 404
    assert response.json() == {"detail": f"Message with ID '{test_id}' not found"}
    mock_collection.find_one.assert_called_once_with({"message_id": test_id})

@patch('src.api_v2.main.db.collection')
def test_get_message_db_error(mock_collection):
    """Test GET /messages/{message_id} when a database error occurs."""
    from pymongo.errors import PyMongoError
    test_id = "any_id"
    mock_collection.find_one.side_effect = PyMongoError("Simulated DB Error")
    
    response = client.get(f"/messages/{test_id}")
    
    assert response.status_code == 500
    assert response.json() == {"detail": f"Error fetching message {test_id} from database"}

# Ensure db.connected is True for tests that require it, or mock it.
# The lifespan manager handles connection, but for unit tests, direct mocking or ensuring
# the db.connected state is often simpler if the lifespan events aren't fully executed
# by TestClient in the same way as a real server.
# For these tests, we assume db.connected is True, or the endpoint logic handles it.
# A fixture could be used to manage db.connected state if necessary.

@patch('src.api_v2.main.db') # Patching the entire db object
def test_list_messages_db_not_connected(mock_db_object):
    """Test GET /messages when database is not connected."""
    mock_db_object.connected = False # Simulate db not being connected
    
    response = client.get("/messages")
    
    assert response.status_code == 503
    assert response.json() == {"detail": "Database not connected"}

@patch('src.api_v2.main.db') # Patching the entire db object
def test_get_message_db_not_connected(mock_db_object):
    """Test GET /messages/{message_id} when database is not connected."""
    mock_db_object.connected = False # Simulate db not being connected
    test_id = "any_id_for_disconnect_test"
    
    response = client.get(f"/messages/{test_id}")
    
    assert response.status_code == 503
    assert response.json() == {"detail": "Database not connected"}

# More tests will be added here
# Mocking db.collection will be done within individual test functions or fixtures.
# The 'db' imported from src.api_v2.main is the global MongoDB instance.
# We will patch its 'collection' attribute.

# To run these tests, ensure PYTHONPATH is set up to include the 'src' directory's parent.
# Example from message-database dir: export PYTHONPATH=$(pwd)
# Then run: pytest tests/test_api_v2.py
# Or rely on run_tests.sh to handle PYTHONPATH.
