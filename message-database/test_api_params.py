#!/usr/bin/env python3
"""
Test script for Hostaway API parameters to identify the correct format.
"""
import os
import sys
import time
from datetime import datetime, timedelta
import logging
import requests

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("hostaway_api_test")

# Check for OAuth credentials
if "HOSTAWAY_CLIENT_ID" not in os.environ or "HOSTAWAY_CLIENT_SECRET" not in os.environ:
    logger.error("Please set HOSTAWAY_CLIENT_ID and HOSTAWAY_CLIENT_SECRET environment variables")
    sys.exit(1)

# Set up base URL
base_url = "https://api.hostaway.com/v1"

def get_access_token():
    """Get an access token using OAuth 2.0 client credentials flow."""
    url = f"{base_url}/accessTokens"
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Cache-control": "no-cache"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": os.environ["HOSTAWAY_CLIENT_ID"],
        "client_secret": os.environ["HOSTAWAY_CLIENT_SECRET"],
        "scope": "general"
    }
    
    try:
        logger.info("Requesting access token from Hostaway API")
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 15897600)
        
        logger.info(f"Successfully obtained access token, valid for {expires_in/86400:.1f} days")
        return access_token
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to obtain access token: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)

def test_conversations_params():
    """Test different parameter formats for the Hostaway conversations endpoint."""
    # First get an access token
    token = get_access_token()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Cache-control": "no-cache"
    }
    
    # Get date 5 days ago
    since_date = datetime.now() - timedelta(days=5)
    
    # Different parameter formats to try
    param_formats = [
        {
            "name": "Standard limit/offset only",
            "params": {
                "limit": 20,
                "offset": 0
            }
        },
        {
            "name": "lastConversationActivity with date",
            "params": {
                "limit": 20,
                "offset": 0,
                "lastConversationActivity": since_date.strftime('%Y-%m-%d')
            }
        },
        {
            "name": "arrivalStartDate with date",
            "params": {
                "limit": 20,
                "offset": 0,
                "arrivalStartDate": since_date.strftime('%Y-%m-%d')
            }
        },
        {
            "name": "latestActivity sorting",
            "params": {
                "limit": 20,
                "offset": 0,
                "sortOrder": "latestActivity"
            }
        },
        {
            "name": "Filter with direct bracket notation",
            "params": {
                "limit": 20,
                "offset": 0,
                "filter[timestamp][>=]": since_date.isoformat()
            }
        }
    ]
    
    # Try each parameter format
    for format_info in param_formats:
        logger.info(f"Trying parameter format: {format_info['name']}")
        try:
            url = f"{base_url}/conversations"
            logger.info(f"Requesting: {url} with params: {format_info['params']}")
            
            response = requests.get(
                url, 
                headers=headers, 
                params=format_info['params']
            )
            
            # Check response status
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get("result", []))
                logger.info(f"Success! Retrieved {result_count} conversations")
                logger.info(f"Response preview: {str(data)[:200]}...")
            else:
                logger.error(f"Failed: {response.text}")
            
        except Exception as e:
            logger.error(f"Error with {format_info['name']}: {str(e)}")
        
        # Add delay to avoid rate limiting
        time.sleep(1)
        print("-" * 50)

if __name__ == "__main__":
    test_conversations_params() 