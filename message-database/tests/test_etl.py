"""
Tests for the ETL pipeline.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.pipeline.etl import ETLPipeline

@pytest.fixture
def mock_api_client():
    """Mock the API client."""
    with patch('src.pipeline.etl.api_client') as mock_client:
        yield mock_client

@pytest.fixture
def mock_db():
    """Mock the database."""
    with patch('src.pipeline.etl.db') as mock_db:
        # Set up mock connection
        mock_db.connect.return_value = True
        yield mock_db

@pytest.fixture
def etl_pipeline():
    """Create an ETL pipeline instance."""
    return ETLPipeline()

def test_etl_process_success(etl_pipeline, mock_api_client, mock_db):
    """Test successful ETL process."""
    # Mock API response with sample messages
    mock_api_client.get_all_messages.return_value = [
        {
            "id": "123",
            "listingId": "456",
            "listingName": "Beach House",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "content": "Hello, is the house available?",
            "timestamp": datetime.now().isoformat(),
            "isIncoming": True,
            "isAutomated": False
        },
        {
            "id": "124",
            "listingId": "456",
            "listingName": "Beach House",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "content": "Yes, it's available!",
            "timestamp": datetime.now().isoformat(),
            "isIncoming": False,
            "isAutomated": False
        }
    ]
    
    # Mock database operations
    mock_db.insert_message.return_value = True
    
    # Run the ETL process
    result = etl_pipeline.extract_transform_load()
    
    # Verify results
    assert result is True
    assert etl_pipeline.processed_count == 2
    assert etl_pipeline.error_count == 0
    
    # Verify database operations
    assert mock_db.connect.called
    assert mock_db.disconnect.called
    assert mock_db.insert_message.call_count == 2

def test_etl_process_with_latest_timestamp(etl_pipeline, mock_api_client, mock_db):
    """Test ETL process using the latest timestamp from the database."""
    # Mock the latest timestamp
    mock_db.get_latest_message_timestamp.return_value = "2023-01-01T00:00:00"
    
    # Mock API response
    mock_api_client.get_all_messages.return_value = []
    
    # Run the ETL process
    result = etl_pipeline.extract_transform_load()
    
    # Verify the timestamp was used
    mock_api_client.get_all_messages.assert_called_once_with("2023-01-01T00:00:00")
    assert result is True

def test_etl_process_with_db_error(etl_pipeline, mock_api_client, mock_db):
    """Test ETL process with database connection error."""
    # Mock database connection failure
    mock_db.connect.return_value = False
    
    # Run the ETL process
    result = etl_pipeline.extract_transform_load()
    
    # Verify error handling
    assert result is False
    assert mock_db.connect.called
    assert not mock_api_client.get_all_messages.called  # Should not proceed to API calls

def test_process_message_success(etl_pipeline, mock_db):
    """Test successful message processing."""
    # Create a test message
    message_data = {
        "id": "123",
        "listingId": "456",
        "listingName": "Beach House",
        "guestName": "John Doe",
        "guestEmail": "john@example.com",
        "content": "Hello, is the house available?",
        "timestamp": datetime.now().isoformat(),
        "isIncoming": True,
        "isAutomated": False
    }
    
    # Mock transform_message to return a MagicMock with to_dict method
    mock_message = MagicMock()
    mock_message.message_id = "123"
    mock_message.to_dict.return_value = {"message_id": "123"}
    
    with patch.object(etl_pipeline, '_transform_message', return_value=mock_message):
        # Mock database insert
        mock_db.insert_message.return_value = True
        
        # Process the message
        result = etl_pipeline._process_message(message_data)
        
        # Verify the result
        assert result is True
        mock_db.insert_message.assert_called_once_with({"message_id": "123"})

def test_process_message_error(etl_pipeline, mock_db):
    """Test message processing with an error."""
    # Create a test message
    message_data = {
        "id": "123",
        "content": "Test message"
    }
    
    # Mock transform_message to raise an exception
    with patch.object(etl_pipeline, '_transform_message', side_effect=ValueError("Test error")):
        # Process the message
        result = etl_pipeline._process_message(message_data)
        
        # Verify the result
        assert result is False
        assert not mock_db.insert_message.called 