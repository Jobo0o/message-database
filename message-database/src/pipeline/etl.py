"""
Extract, Transform, Load (ETL) pipeline for the Hostaway Message Database application.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
import sys

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
        
        print(f"Starting ETL process at {self.start_time.isoformat()}")
        logger.info(f"Starting ETL process at {self.start_time.isoformat()}")
        
        try:
            # Validate configuration
            print("Validating configuration...")
            validate_config()
            
            # Connect to MongoDB
            print("Connecting to MongoDB...")
            if not db.connect():
                error_msg = "ETL process failed: Could not connect to MongoDB"
                print(error_msg)
                logger.error(error_msg)
                send_error_notification(
                    "Hostaway Message ETL Failed",
                    "ETL process failed due to MongoDB connection error."
                )
                return False
            
            # If no since_timestamp is provided, get the latest from the database
            if not since_timestamp:
                since_timestamp = db.get_latest_message_timestamp()
                if since_timestamp:
                    print(f"Processing messages since: {since_timestamp}")
                    logger.info(f"Processing messages since: {since_timestamp}")
            
            # Process each conversation from the API
            print("Fetching conversations from Hostaway API...")
            conversations = api_client.get_all_messages(since_timestamp)
            print(f"Found conversations to process")
            
            for conversation_data in conversations:
                conversation_id = conversation_data.get("id")
                if not conversation_id:
                    print("No conversation ID found, skipping...")
                    continue
                print(f"\nFetching messages for conversation ID: {conversation_id}")
                try:
                    conversation_messages = api_client.get_conversation_messages(str(conversation_id))
                except HostawayAPIError as e:
                    logger.warning(f"Could not fetch messages for conversation ID {conversation_id}: {str(e)}")
                    continue
                if not conversation_messages:
                    print(f"No messages found for conversation ID {conversation_id}")
                    continue
                for msg in conversation_messages:
                    # Merge conversation metadata into each message for context
                    message_data = dict(conversation_data)
                    message_data.update(msg)
                    print(f"Processing message ID: {msg.get('id', 'unknown')}")
                    success = self._process_message(message_data)
                    if success:
                        self.processed_count += 1
                        print(f"Successfully processed message {self.processed_count}")
                    else:
                        self.error_count += 1
                        print(f"Failed to process message. Error count: {self.error_count}")
            
            # Log completion information
            duration = datetime.now() - self.start_time
            completion_msg = f"ETL process completed in {duration.total_seconds():.2f} seconds. Processed {self.processed_count} messages with {self.error_count} errors"
            print(completion_msg)
            logger.info(completion_msg)
            
            return self.error_count == 0
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_msg = f"ETL process failed with an unhandled exception: {str(e)}"
            print(error_msg)
            print(f"Traceback: {error_traceback}")
            logger.error(error_msg)
            logger.debug(f"Traceback: {error_traceback}")
            
            # Send notification about the failure
            send_error_notification(
                "Hostaway Message ETL Failed",
                f"ETL process failed with error: {str(e)}\n\n{error_traceback}"
            )
            
            return False
            
        finally:
            # Ensure we disconnect from MongoDB
            print("Disconnecting from MongoDB...")
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
            print("Transforming message data...")
            message = self._transform_message(message_data)
            print(f"Transformed message: {message.model_dump()}")
            
            # Convert to dictionary for MongoDB
            message_dict = message.to_dict()
            print(f"Converted to dict: {message_dict}")
            
            # Final conversion to ensure no Decimal remains
            def convert(obj):
                from decimal import Decimal
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert(i) for i in obj]
                else:
                    return obj
            message_dict = convert(message_dict)
            
            # Load into MongoDB
            print("Inserting into MongoDB...")
            success = db.insert_message(message_dict)
            
            if not success:
                error_msg = f"Failed to insert message with ID: {message.message_id}"
                print(error_msg)
                logger.error(error_msg)
                return False
            
            print("Successfully inserted message into MongoDB")
            return True
            
        except Exception as e:
            message_id = message_data.get("id", "unknown")
            error_msg = f"Error processing message {message_id}: {str(e)}"
            print(error_msg)
            print(f"Traceback: {traceback.format_exc()}")
            logger.error(error_msg)
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
        # Extract property details from the conversation data
        property_id = str(message_data.get("listingMapId", ""))
        property_name = message_data.get("listingName", "")
        if property_id and not property_name:
            try:
                property_details = api_client.get_property_details(property_id)
                property_name = property_details.get("name", "")
            except HostawayAPIError as e:
                logger.warning(f"Could not fetch property details for ID {property_id}: {str(e)}")

        # Extract reservation details and guest info from reservation
        reservation_id = str(message_data.get("reservationId", ""))
        reservation_price = None
        guest_name = ""
        guest_email = None
        guest_phone = None
        guest_nationality = None
        if reservation_id:
            try:
                reservation_details = api_client.get_reservation_details(reservation_id)
                reservation_price = reservation_details.get("totalPrice")
                guest_name = reservation_details.get("guestName", "")
                guest_email = reservation_details.get("guestEmail")
                guest_phone = reservation_details.get("phone")
                guest_nationality = reservation_details.get("guestCountry")
            except HostawayAPIError as e:
                logger.warning(f"Could not fetch reservation details for ID {reservation_id}: {str(e)}")
        else:
            guest_name = message_data.get("guestName", "")
            guest_email = message_data.get("guestEmail")
            guest_phone = message_data.get("guestPhone")
            guest_nationality = message_data.get("guestCountry")

        # Determine direction based on isIncoming field if present, else fallback to type
        direction = "outgoing"
        if "isIncoming" in message_data:
            direction = "incoming" if message_data["isIncoming"] else "outgoing"
        else:
            conversation_type = message_data.get("type", "")
            if conversation_type == "guest-host-email":
                direction = "incoming"
            elif conversation_type == "host-guest-email":
                direction = "outgoing"

        # Get message content from the 'body' field
        content = message_data.get("body", "")
        if not content:
            logger.warning(f"No content found for message ID {message_data.get('id', 'unknown')}. Content will be empty.")

        # Get timestamp from the message
        timestamp = datetime.now()
        message_time = message_data.get("insertedOn") or message_data.get("updatedOn") or message_data.get("messageSentOn") or message_data.get("messageReceivedOn")
        if message_time:
            try:
                timestamp = datetime.strptime(message_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.warning(f"Could not parse timestamp: {message_time}")

        return Message(
            message_id=str(message_data.get("id", "")),
            property=Property(
                id=property_id,
                name=property_name
            ),
            guest=Guest(
                name=guest_name,
                email=guest_email,
                phone=guest_phone,
                nationality=guest_nationality
            ),
            content=content,
            timestamp=timestamp,
            direction=direction,
            reservation=Reservation(
                id=reservation_id,
                price=float(reservation_price) if reservation_price is not None else None
            ) if reservation_id else None,
            message_type="manual"  # Default to manual since we can't determine this from the API
        )

# Create a singleton instance
pipeline = ETLPipeline()

if __name__ == "__main__":
    print("Starting ETL pipeline...")
    success = pipeline.extract_transform_load()
    sys.exit(0 if success else 1) 