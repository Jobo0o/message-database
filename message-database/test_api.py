#!/usr/bin/env python3
"""
Test script for the Hostaway API client connection.
"""
import os
import sys
from datetime import datetime, timedelta
import logging

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("hostaway_api_test")

# Set environment variables for testing
os.environ["ENABLE_DRY_RUN"] = "False"
os.environ["HOSTAWAY_BASE_URL"] = "https://api.hostaway.com/v1"

# Check for OAuth credentials
if "HOSTAWAY_CLIENT_ID" not in os.environ or "HOSTAWAY_CLIENT_SECRET" not in os.environ:
    logger.error("Please set HOSTAWAY_CLIENT_ID and HOSTAWAY_CLIENT_SECRET environment variables")
    sys.exit(1)

# Import after setting environment variables
from src.api.hostaway_client import HostawayClient

def test_api_connection():
    """Test connecting to the Hostaway API and retrieving messages."""
    client = HostawayClient()
    
    # Get messages from the last 5 days
    since_date = datetime.now() - timedelta(days=5)
    since_timestamp = since_date.isoformat()
    
    logger.info(f"Testing API connection to retrieve messages since {since_timestamp}")
    
    try:
        # First, try with the updated arrivalStartDate parameter
        response = client.get_messages(since_timestamp=since_timestamp)
        logger.info(f"API Response: {response}")
        
        # Check if we got any results
        messages = response.get("result", [])
        logger.info(f"Retrieved {len(messages)} messages")
        
        # If successful, return
        return True
    except Exception as e:
        logger.error(f"Error retrieving messages with updated params: {str(e)}")
        
        # Try with direct timestamp format as fallback
        try:
            # Manual override of parameters
            params = {
                "limit": 100,
                "offset": 0,
                "lastConversationActivity": since_date.strftime('%Y-%m-%d')
            }
            
            response = client._make_request("GET", "/conversations", params=params)
            logger.info(f"Fallback API Response: {response}")
            
            # Check if we got any results
            messages = response.get("result", [])
            logger.info(f"Retrieved {len(messages)} messages with fallback approach")
            
            return True
        except Exception as e2:
            logger.error(f"Fallback also failed: {str(e2)}")
            return False

if __name__ == "__main__":
    test_api_connection() 