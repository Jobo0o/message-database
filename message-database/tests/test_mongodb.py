"""
Tests for the MongoDB connection.
"""
import pytest
from unittest.mock import MagicMock, patch
from pymongo.errors import ConnectionFailure

from src.database.mongodb import MongoDB

@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoClient."""
    with patch('src.database.mongodb.MongoClient') as mock_client:
        # Set up the mock client
        mock_instance = mock_client.return_value
        mock_admin = MagicMock()
        mock_instance.admin = mock_admin
        mock_admin.command.return_value = {'ok': 1}  # Success response for ping
        
        # Mock the database and collection
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        yield mock_client

def test_connect_success(mock_mongo_client):
    """Test successful MongoDB connection."""
    db = MongoDB()
    assert db.connect() is True
    assert db.connected is True
    mock_mongo_client.assert_called_once()
    
    # Verify ping was called
    mock_mongo_client.return_value.admin.command.assert_called_once_with('ping')

def test_connect_failure(mock_mongo_client):
    """Test MongoDB connection failure."""
    # Make ping raise an exception
    mock_mongo_client.return_value.admin.command.side_effect = ConnectionFailure("Connection failed")
    
    db = MongoDB()
    assert db.connect() is False
    assert db.connected is False

def test_disconnect():
    """Test MongoDB disconnect."""
    db = MongoDB()
    db.client = MagicMock()
    db.connected = True
    
    db.disconnect()
    
    db.client.close.assert_called_once()
    assert db.client is None
    assert db.db is None
    assert db.collection is None
    assert db.connected is False

@patch('src.database.mongodb.logger')
def test_insert_message_success(mock_logger):
    """Test successful message insertion."""
    db = MongoDB()
    db.connected = True
    db.collection = MagicMock()
    
    # Mock update_one result
    mock_result = MagicMock()
    mock_result.upserted_id = 'new_id'
    mock_result.modified_count = 0
    db.collection.update_one.return_value = mock_result
    
    message_data = {"message_id": "123", "content": "Test message"}
    
    assert db.insert_message(message_data) is True
    db.collection.update_one.assert_called_once_with(
        {"message_id": "123"},
        {"$set": message_data},
        upsert=True
    )

@patch('src.database.mongodb.logger')
def test_insert_message_not_connected(mock_logger):
    """Test message insertion when not connected."""
    db = MongoDB()
    db.connected = False
    
    message_data = {"message_id": "123", "content": "Test message"}
    
    assert db.insert_message(message_data) is False
    mock_logger.error.assert_called_once() 