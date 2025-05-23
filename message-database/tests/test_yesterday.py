#!/usr/bin/env python3
"""
Test script for retrieving Hostaway messages from yesterday.
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

def test_yesterday_messages():
    """Test retrieving messages from yesterday."""
    client = HostawayClient()
    
    # Get yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    yesterday_iso = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    logger.info(f"Testing API connection to retrieve messages from yesterday ({yesterday_str})")
    
    # Try different parameter formats for yesterday
    param_formats = [
        {
            "name": "Using arrivalStartDate",
            "params": {
                "limit": 100,
                "offset": 0,
                "arrivalStartDate": yesterday_str
            }
        },
        {
            "name": "Using lastConversationActivity",
            "params": {
                "limit": 100,
                "offset": 0,
                "lastConversationActivity": yesterday_str
            }
        },
        {
            "name": "Using filter[timestamp]",
            "params": {
                "limit": 100,
                "offset": 0,
                "filter[timestamp][>=]": yesterday_iso
            }
        },
        {
            "name": "Using latestActivity sort",
            "params": {
                "limit": 100,
                "offset": 0,
                "sortOrder": "latestActivity"
            }
        }
    ]
    
    # Test each parameter format
    success = False
    for format_info in param_formats:
        try:
            logger.info(f"Trying {format_info['name']}")
            response = client._make_request("GET", "/conversations", params=format_info['params'])
            
            # Check if we got any results
            messages = response.get("result", [])
            count = len(messages)
            logger.info(f"Retrieved {count} messages using {format_info['name']}")
            
            if count > 0:
                logger.info(f"First message preview: {str(messages[0])[:200]}...")
                success = True
            
            # Short pause between requests
            import time
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error with {format_info['name']}: {str(e)}")
    
    # Try the standard get_messages method too
    try:
        logger.info("Trying standard get_messages method with yesterday's date")
        response = client.get_messages(since_timestamp=yesterday_iso)
        messages = response.get("result", [])
        count = len(messages)
        logger.info(f"Retrieved {count} messages using standard get_messages method")
        
        if count > 0:
            logger.info(f"First message preview: {str(messages[0])[:200]}...")
            success = True
        
    except Exception as e:
        logger.error(f"Error with standard get_messages method: {str(e)}")
    
    return success

if __name__ == "__main__":
    if test_yesterday_messages():
        logger.info("Successfully retrieved messages from yesterday!")
        sys.exit(0)
    else:
        logger.error("Failed to retrieve any messages from yesterday.")
        sys.exit(1) 