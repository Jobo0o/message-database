"""
Configuration module for the Hostaway Message Database application.
Loads environment variables and provides configuration settings.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Hostaway API Configuration
# For OAuth 2.0 client credentials flow
HOSTAWAY_CLIENT_ID = os.getenv("HOSTAWAY_CLIENT_ID")
HOSTAWAY_CLIENT_SECRET = os.getenv("HOSTAWAY_CLIENT_SECRET")
HOSTAWAY_BASE_URL = os.getenv("HOSTAWAY_BASE_URL", "https://api.hostaway.com/v1")

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "hostaway_messages")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "messages")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "./logs")

# Application Settings
API_REQUEST_DELAY = float(os.getenv("API_REQUEST_DELAY", "1.0"))
ENABLE_DRY_RUN = os.getenv("ENABLE_DRY_RUN", "False").lower() == "true"
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")

# Ensure required configuration is available
def validate_config():
    """Validate that all required configuration values are available."""
    required_vars = [
        ("HOSTAWAY_CLIENT_ID", HOSTAWAY_CLIENT_ID),
        ("HOSTAWAY_CLIENT_SECRET", HOSTAWAY_CLIENT_SECRET),
        ("MONGODB_URI", MONGODB_URI),
    ]
    
    missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
    
    if missing_vars:
        error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
        logging.error(error_message)
        raise ValueError(error_message)

# Numeric log levels
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

NUMERIC_LOG_LEVEL = LOG_LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO) 