"""
Extract, Transform, Load (ETL) pipeline for the Hostaway Message Database application.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback

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
        Process a single message by transforming it and loading into the database.
        
        Args:
            message_data: Raw message data from the API
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Transform the message data
            message = self._transform_message(message_data)
            
            # Convert to dictionary for MongoDB
            message_dict = message.to_dict()
            
            # Load into MongoDB
            success = db.insert_message(message_dict)
            
            if not success:
                logger.error(f"Failed to insert message with ID: {message.message_id}")
                return False
            
            return True
            
        except Exception as e:
            message_id = message_data.get("id", "unknown")
            logger.error(f"Error processing message {message_id}: {str(e)}")
            return False
    
    def _transform_message(self, message_data: Dict[str, Any]) -> Message:
        """
        Transform raw API message data into a Message object.
        Enriches the message with property and reservation details if needed.
        
        Args:
            message_data: Raw message data from the API
            
        Returns:
            Message: A processed Message instance
        """
        # Extract property details
        property_id = str(message_data.get("listingId", ""))
        property_name = message_data.get("listingName", "")
        
        # If we have a property ID but no name, fetch property details
        if property_id and not property_name:
            try:
                property_details = api_client.get_property_details(property_id)
                property_name = property_details.get("name", "")
            except HostawayAPIError as e:
                logger.warning(f"Could not fetch property details for ID {property_id}: {str(e)}")
        
        # Extract reservation details
        reservation_id = str(message_data.get("reservationId", ""))
        reservation_price = None
        
        # If we have a reservation ID, fetch its details
        if reservation_id:
            try:
                reservation_details = api_client.get_reservation_details(reservation_id)
                reservation_price = reservation_details.get("totalPrice")
            except HostawayAPIError as e:
                logger.warning(f"Could not fetch reservation details for ID {reservation_id}: {str(e)}")
        
        # Create and return a Message object
        return Message(
            message_id=str(message_data.get("id", "")),
            property=Property(
                id=property_id,
                name=property_name
            ),
            guest=Guest(
                name=message_data.get("guestName", ""),
                email=message_data.get("guestEmail", None),
                phone=message_data.get("guestPhoneNumber", None),
                nationality=message_data.get("guestNationality", None)
            ),
            content=message_data.get("content", ""),
            timestamp=datetime.fromisoformat(message_data.get("timestamp", datetime.now().isoformat())),
            direction="incoming" if message_data.get("isIncoming", False) else "outgoing",
            reservation=Reservation(
                id=reservation_id,
                price=float(reservation_price) if reservation_price is not None else None
            ) if reservation_id else None,
            message_type="automated" if message_data.get("isAutomated", False) else "manual",
        )

# Create a singleton instance
pipeline = ETLPipeline() 