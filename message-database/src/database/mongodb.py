"""
MongoDB connection and operations for the Hostaway Message Database application.
"""
import time
from typing import Dict, Any, List, Optional
from pymongo import MongoClient, IndexModel, ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, PyMongoError

from ..config import MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION, ENABLE_DRY_RUN
from ..utils.logger import logger

class MongoDB:
    """MongoDB database manager for the Hostaway Message Database."""
    
    def __init__(self):
        """Initialize the MongoDB connection."""
        self.client = None
        self.db = None
        self.collection = None
        self.connected = False
    
    def connect(self, max_retries: int = 3, retry_delay: int = 5) -> bool:
        """
        Connect to MongoDB with retry mechanism.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Seconds to wait between retries
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        # If in dry run mode, skip actual connection
        if ENABLE_DRY_RUN:
            logger.info("DRY RUN: Skipping MongoDB connection")
            self.connected = True
            return True
            
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MongoDB (attempt {attempt + 1}/{max_retries})...")
                # Updated MongoDB client configuration with more permissive SSL settings
                self.client = MongoClient(
                    MONGODB_URI,
                    tls=True,
                    tlsAllowInvalidCertificates=True,  # More permissive SSL setting
                    serverSelectionTimeoutMS=30000,    # Increased timeout
                    connectTimeoutMS=30000,            # Increased timeout
                    socketTimeoutMS=30000,             # Increased timeout
                    retryWrites=True,
                    w='majority'
                )
                
                # Force connection to verify it works
                self.client.admin.command('ping')
                
                self.db = self.client[MONGODB_DATABASE]
                self.collection = self.db[MONGODB_COLLECTION]
                
                logger.info("Successfully connected to MongoDB")
                self.connected = True
                
                # Set up indexes if they don't exist
                self._create_indexes()
                
                return True
                
            except ConnectionFailure as e:
                logger.error(f"MongoDB connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Could not connect to MongoDB.")
        
        return False
    
    def _create_indexes(self):
        """Create required indexes on the collection if they don't exist."""
        if ENABLE_DRY_RUN:
            logger.info("DRY RUN: Would create MongoDB indexes")
            return
            
        try:
            # Define the indexes
            indexes = [
                # Text index on content field
                IndexModel([("content", TEXT)], name="content_text"),
                
                # Compound index on property.id and timestamp
                IndexModel([
                    ("property.id", ASCENDING), 
                    ("timestamp", ASCENDING)
                ], name="property_timestamp"),
                
                # Compound index on guest.nationality and timestamp
                IndexModel([
                    ("guest.nationality", ASCENDING), 
                    ("timestamp", ASCENDING)
                ], name="nationality_timestamp"),
                
                # Unique index on message_id
                IndexModel([("message_id", ASCENDING)], unique=True, name="message_id_unique")
            ]
            
            # Create the indexes
            self.collection.create_indexes(indexes)
            logger.info("MongoDB indexes created or already exist")
            
        except PyMongoError as e:
            logger.error(f"Failed to create MongoDB indexes: {str(e)}")
    
    def disconnect(self):
        """Close the MongoDB connection."""
        if ENABLE_DRY_RUN:
            logger.info("DRY RUN: Would disconnect from MongoDB")
            self.connected = False
            return
            
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None
            self.connected = False
            logger.info("Disconnected from MongoDB")
    
    def insert_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Insert a message into the collection with upsert (update if exists).
        
        Args:
            message_data: Dictionary representation of a message
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Cannot insert message: Not connected to MongoDB")
            return False
            
        if ENABLE_DRY_RUN:
            logger.info(f"DRY RUN: Would insert message with ID: {message_data.get('message_id', 'unknown')}")
            return True
        
        try:
            # Use update_one with upsert to avoid duplicates
            result = self.collection.update_one(
                {"message_id": message_data["message_id"]},
                {"$set": message_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug(f"Inserted new message with ID: {message_data['message_id']}")
            elif result.modified_count > 0:
                logger.debug(f"Updated existing message with ID: {message_data['message_id']}")
            
            return True
            
        except PyMongoError as e:
            logger.error(f"Failed to insert message: {str(e)}")
            return False
    
    def get_latest_message_timestamp(self) -> Optional[str]:
        """
        Get the timestamp of the latest message in the database.
        
        Returns:
            Optional[str]: ISO format timestamp string or None if no messages found
        """
        if not self.connected:
            logger.error("Cannot get latest timestamp: Not connected to MongoDB")
            return None
            
        if ENABLE_DRY_RUN:
            logger.info("DRY RUN: Would get latest message timestamp")
            return None
        
        try:
            # Find the most recent message
            latest_message = self.collection.find_one(
                sort=[("timestamp", -1)]  # Sort by timestamp descending
            )
            
            if latest_message and "timestamp" in latest_message:
                # Return timestamp in ISO format
                return latest_message["timestamp"].isoformat()
            
            return None
            
        except PyMongoError as e:
            logger.error(f"Failed to get latest message timestamp: {str(e)}")
            return None
    
    def count_messages(self) -> int:
        """
        Count the total number of messages in the collection.
        
        Returns:
            int: Number of messages or 0 if error
        """
        if not self.connected:
            logger.error("Cannot count messages: Not connected to MongoDB")
            return 0
            
        if ENABLE_DRY_RUN:
            logger.info("DRY RUN: Would count messages")
            return 0
        
        try:
            return self.collection.count_documents({})
        except PyMongoError as e:
            logger.error(f"Failed to count messages: {str(e)}")
            return 0

# Create a singleton instance
db = MongoDB() 