"""
Tests for the Hostaway API client.
"""
import pytest
import requests
from unittest.mock import MagicMock, patch

from src.api.hostaway_client import HostawayClient, HostawayAPIError

@pytest.fixture
def api_client():
    """Create a HostawayClient with mocked configuration."""
    with patch('src.api.hostaway_client.HOSTAWAY_API_KEY', 'test_api_key'), \
         patch('src.api.hostaway_client.HOSTAWAY_BASE_URL', 'https://api.test.com/v1'), \
         patch('src.api.hostaway_client.API_REQUEST_DELAY', 0.001), \
         patch('src.api.hostaway_client.ENABLE_DRY_RUN', False):
        client = HostawayClient()
        yield client

@pytest.fixture
def mock_requests():
    """Mock the requests library."""
    with patch('src.api.hostaway_client.requests.request') as mock_request:
        # Set up a successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "result": [{"id": "123", "content": "Test message"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response
        
        yield mock_request

def test_make_request_success(api_client, mock_requests):
    """Test successful API request."""
    response = api_client._make_request("GET", "/endpoint")
    
    # Verify request was made with correct parameters
    mock_requests.assert_called_once_with(
        method="GET",
        url="https://api.test.com/v1/endpoint",
        headers=api_client.headers,
        params=None,
        json=None
    )
    
    # Verify response processing
    assert response["status"] == "success"
    assert response["result"] == [{"id": "123", "content": "Test message"}]

def test_make_request_http_error(api_client, mock_requests):
    """Test API request with HTTP error."""
    # Make raise_for_status raise an exception
    mock_requests.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
    
    with pytest.raises(HostawayAPIError):
        api_client._make_request("GET", "/endpoint")

def test_make_request_api_error(api_client, mock_requests):
    """Test API request with API-level error."""
    # Return an error response
    mock_requests.return_value.json.return_value = {
        "status": "error",
        "message": "API Error"
    }
    
    with pytest.raises(HostawayAPIError, match="API Error"):
        api_client._make_request("GET", "/endpoint")

def test_get_messages(api_client):
    """Test get_messages method."""
    with patch.object(api_client, '_make_request') as mock_request:
        mock_request.return_value = {"status": "success", "result": []}
        
        # Call without timestamp
        api_client.get_messages(limit=50, offset=10)
        mock_request.assert_called_once_with(
            "GET", 
            "/messages", 
            params={"limit": 50, "offset": 10}
        )
        
        # Reset mock and call with timestamp
        mock_request.reset_mock()
        api_client.get_messages(since_timestamp="2023-01-01T00:00:00", limit=50, offset=10)
        mock_request.assert_called_once_with(
            "GET", 
            "/messages", 
            params={
                "limit": 50, 
                "offset": 10,
                "filter[timestamp][>=]": "2023-01-01T00:00:00"
            }
        )

def test_get_all_messages(api_client):
    """Test get_all_messages method."""
    with patch.object(api_client, 'get_messages') as mock_get_messages:
        # Setup first response with messages
        mock_get_messages.side_effect = [
            {"status": "success", "result": [{"id": "1"}, {"id": "2"}]},
            {"status": "success", "result": [{"id": "3"}]},
            {"status": "success", "result": []}
        ]
        
        # Call get_all_messages and collect results
        messages = list(api_client.get_all_messages())
        
        # Verify correct calls were made
        assert mock_get_messages.call_count == 3
        assert len(messages) == 3
        assert [msg["id"] for msg in messages] == ["1", "2", "3"] 