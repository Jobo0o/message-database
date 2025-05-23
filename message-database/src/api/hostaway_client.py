"""
Hostaway API client for the Message Database application.
Handles authentication and requests to the Hostaway API.
"""
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Generator
import json

from ..config import HOSTAWAY_CLIENT_ID, HOSTAWAY_CLIENT_SECRET, HOSTAWAY_BASE_URL, API_REQUEST_DELAY, ENABLE_DRY_RUN
from ..utils.logger import logger

class HostawayAPIError(Exception):
    """Exception raised for errors in the Hostaway API."""
    pass

class HostawayClient:
    """Client for interacting with the Hostaway API."""
    
    def __init__(self):
        """Initialize the Hostaway API client."""
        self.base_url = HOSTAWAY_BASE_URL
        self.client_id = HOSTAWAY_CLIENT_ID
        self.client_secret = HOSTAWAY_CLIENT_SECRET
        self.access_token = None
        self.token_expires_at = None
        
        # Request delay to avoid rate limiting
        self.request_delay = API_REQUEST_DELAY
        
        # Dry run mode
        self.dry_run = ENABLE_DRY_RUN
    
    def _get_access_token(self) -> str:
        """
        Get a valid access token using OAuth 2.0 client credentials flow.
        Will fetch a new token if none exists or the current one is expired.
        
        Returns:
            str: Access token
        """
        # Check if we already have a valid token
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        if self.dry_run:
            logger.info("DRY RUN: Would get access token from Hostaway API")
            self.access_token = "dry_run_token"
            self.token_expires_at = datetime.now() + timedelta(days=30)
            return self.access_token
            
        # Request a new token
        url = f"{self.base_url}/accessTokens"
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Cache-control": "no-cache"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "general"
        }
        
        try:
            logger.info("Requesting new access token from Hostaway API")
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            # Calculate expiration time (token lasts 24 months but we'll refresh earlier)
            expires_in = token_data.get("expires_in", 15897600)  # Default to 6 months in seconds
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in * 0.9)  # Refresh at 90% of lifetime
            
            logger.info(f"Successfully obtained access token, valid until {self.token_expires_at.isoformat()}")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain access token: {str(e)}")
            raise HostawayAPIError(f"Authentication failed: {str(e)}")
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """
        Make a request to the Hostaway API with built-in retry and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Dict: API response data
            
        Raises:
            HostawayAPIError: If the API request fails after retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would {method} {url}")
            if params:
                logger.info(f"DRY RUN: With params: {params}")
            if data:
                logger.info(f"DRY RUN: With data: {json.dumps(data)}")
            return {"status": "success", "result": [], "dry_run": True}
        
        # Get valid token and set headers
        token = self._get_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "Cache-control": "no-cache"
        }
        
        max_retries = 3
        retry_delay = 2  # Starting delay, will increase with each retry
        
        for attempt in range(max_retries):
            try:
                # Add delay between requests to avoid rate limiting
                if attempt > 0:
                    time.sleep(retry_delay * attempt)
                else:
                    time.sleep(self.request_delay)
                
                logger.debug(f"Making {method} request to {url}")
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data
                )
                
                # Check for auth errors and refresh token if needed
                if response.status_code == 401 or response.status_code == 403:
                    if attempt < max_retries - 1:
                        logger.warning("Authentication error. Refreshing token and retrying...")
                        # Reset token to force refresh
                        self.access_token = None
                        token = self._get_access_token()
                        headers["Authorization"] = f"Bearer {token}"
                        continue
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Parse response JSON
                response_data = response.json()
                
                # Check for API-level errors
                if response_data.get("status") != "success":
                    error_message = response_data.get("message", "Unknown API error")
                    logger.error(f"Hostaway API error: {error_message}")
                    raise HostawayAPIError(error_message)
                
                return response_data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise HostawayAPIError(f"Failed after {max_retries} attempts: {str(e)}")
    
    def get_messages(self, 
                     since_timestamp: Optional[str] = None, 
                     limit: int = 100, 
                     offset: int = 0) -> Dict[str, Any]:
        """
        Get messages from the Hostaway API.
        
        Args:
            since_timestamp: Only get messages after this timestamp (ISO format)
            limit: Maximum number of messages to retrieve per request
            offset: Offset for pagination
            
        Returns:
            Dict: API response containing messages
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # Add filter for timestamp if provided
        if since_timestamp:
            # Using a different format based on Hostaway API standards
            # Format should be: arrivalStartDate or similar for date-based filtering
            # instead of filter[timestamp][>=]
            date_obj = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%Y-%m-%d')
            params["arrivalStartDate"] = formatted_date
        
        return self._make_request("GET", "/conversations", params=params)
    
    def get_all_messages(self, since_timestamp: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Get all messages from the Hostaway API using pagination.
        
        Args:
            since_timestamp: Only get messages after this timestamp (ISO format)
            
        Yields:
            Dict: Each message from the API
        """
        offset = 0
        limit = 100
        total_retrieved = 0
        
        while True:
            response = self.get_messages(since_timestamp, limit, offset)
            
            # Extract messages from response
            messages = response.get("result", [])
            
            # Break if no messages returned
            if not messages:
                logger.info(f"Retrieved a total of {total_retrieved} messages")
                break
            
            # Yield each message
            for message in messages:
                total_retrieved += 1
                yield message
            
            # Update offset for next page
            offset += limit
            
            logger.info(f"Retrieved {len(messages)} messages. Total so far: {total_retrieved}")
            
            # If fewer messages than the limit, we've reached the end
            if len(messages) < limit:
                logger.info(f"Completed retrieval with a total of {total_retrieved} messages")
                break
    
    def get_property_details(self, property_id: str) -> Dict[str, Any]:
        """
        Get details for a specific property.
        
        Args:
            property_id: The Hostaway property ID
            
        Returns:
            Dict: Property details
        """
        response = self._make_request("GET", f"/listings/{property_id}")
        return response.get("result", {})
    
    def get_reservation_details(self, reservation_id: str) -> Dict[str, Any]:
        """
        Get details for a specific reservation.
        
        Args:
            reservation_id: The Hostaway reservation ID
            
        Returns:
            Dict: Reservation details
        """
        response = self._make_request("GET", f"/reservations/{reservation_id}")
        return response.get("result", {})

    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a specific conversation.
        Args:
            conversation_id: The Hostaway conversation ID
        Returns:
            List of message objects (each with content and metadata)
        """
        endpoint = f"/conversations/{conversation_id}/messages"
        response = self._make_request("GET", endpoint)
        return response.get("result", [])

# Create a singleton instance
api_client = HostawayClient() 