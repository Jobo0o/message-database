"""
Extract, Transform, Load (ETL) pipeline for the Hostaway Message Database application.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
from decimal import Decimal

from ..api.hostaway_client import api_client, HostawayAPIError
from ..database.mongodb import db
from ..models.message import Message, Property, Guest, Reservation
from ..utils.logger import logger, send_error_notification
from ..config import validate_config

class ETLPipeline:
    """ETL Pipeline for processing Hostaway messages into MongoDB."""
    
    def __init__(self):
        """Initialize the ETL pipeline."""
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
    
    def extract_transform_load(self, since_timestamp: Optional[str] = None) -> bool:
        """
        Run the complete ETL process to extract messages from the API,
        transform them into the target format, and load them into MongoDB.
        
        Args:
            since_timestamp: Only process messages after this timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.start_time = datetime.now()
        self.processed_count = 0
        self.error_count = 0
        
        logger.info(f"Starting ETL process at {self.start_time.isoformat()}")
        
        try:
            # Validate configuration
            validate_config()
            
            # Connect to MongoDB
            if not db.connect():
                logger.error("ETL process failed: Could not connect to MongoDB")
                send_error_notification(
                    "Hostaway Message ETL Failed",
                    "ETL process failed due to MongoDB connection error."
                )
                return False
            
            # If no since_timestamp is provided, get the latest from the database
            if not since_timestamp:
                since_timestamp = db.get_latest_message_timestamp()
                if since_timestamp:
                    logger.info(f"Processing messages since: {since_timestamp}")
            
            # Process each message from the API
            for message_data in api_client.get_all_messages(since_timestamp):
                success = self._process_message(message_data)
                
                if success:
                    self.processed_count += 1
                else:
                    self.error_count += 1
            
            # Log completion information
            duration = datetime.now() - self.start_time
            logger.info(f"ETL process completed in {duration.total_seconds():.2f} seconds")
            logger.info(f"Processed {self.processed_count} messages with {self.error_count} errors")
            
            return self.error_count == 0
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"ETL process failed with an unhandled exception: {str(e)}")
            logger.debug(f"Traceback: {error_traceback}")
            
            # Send notification about the failure
            send_error_notification(
                "Hostaway Message ETL Failed",
                f"ETL process failed with error: {str(e)}\n\n{error_traceback}"
            )
            
            return False
            
        finally:
            # Ensure we disconnect from MongoDB
            db.disconnect()
    
    def _process_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Process a single message: transform and load into the database.
        
        Args:
            message_data: Raw message data from the API
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # Transform the message data
            transformed_data = self._transform_message(message_data)
            
            # Create a Message instance from the transformed data
            message = Message(**transformed_data)
            
            # Convert all Decimal values to float recursively
            def convert_decimals(obj):
                if isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(i) for i in obj]
                elif isinstance(obj, Decimal):
                    return float(obj)
                else:
                    return obj

            message_dict = convert_decimals(message.dict())

            # Load into database
            db.insert_message(message_dict)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _transform_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw message data into a structured format.
        
        Args:
            message_data: Raw message data from the API
            
        Returns:
            Dict: Transformed message data
        """
        logger.info(f"Processing message data: {message_data}")
        
        # Get conversation messages
        conversation_id = str(message_data.get("id"))
        conversation_messages = api_client.get_conversation_messages(conversation_id)
        
        # Extract message content from the first message if available
        content = ""
        if conversation_messages and len(conversation_messages) > 0:
            first_message = conversation_messages[0]
            content = first_message.get("body", "")
        
        # Extract property details
        property_id = str(message_data.get("listingMapId", ""))
        property_details = api_client.get_property_details(property_id)
        
        # Extract reservation details if available
        reservation_id = str(message_data.get("reservationId", ""))
        reservation_details = None
        if reservation_id:
            reservation_details = api_client.get_reservation_details(reservation_id)
        
        # Create transformed message data
        transformed_data = {
            "message_id": conversation_id,
            "property": {
                "id": property_id,
                "name": property_details.get("name", "")
            },
            "guest": {
                "name": message_data.get("recipientName", ""),
                "email": message_data.get("recipientEmail"),
                "phone": message_data.get("phone"),
                "nationality": None  # Not available in API response
            },
            "content": content,
            "timestamp": datetime.fromisoformat(message_data.get("messageSentOn", datetime.now().isoformat())),
            "direction": "incoming" if message_data.get("type", "").startswith("guest") else "outgoing",
            "reservation": {
                "id": reservation_id,
                "price": Decimal(str(reservation_details.get("totalPrice", 0))) if reservation_details else Decimal("0")
            } if reservation_id else None,
            "message_type": "automated" if message_data.get("type", "").startswith("automated") else "manual"
        }
        
        logger.info(f"Transformed message data: {transformed_data}")
        return transformed_data

# Create a singleton instance
pipeline = ETLPipeline() 