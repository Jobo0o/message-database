"""
Pydantic models for the Hostaway Message Database application.
Defines the data structures for messages and related entities.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Property(BaseModel):
    """Property model representing a vacation rental property."""
    id: str
    name: str

class Guest(BaseModel):
    """Guest model representing a booking guest."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nationality: Optional[str] = None

class Reservation(BaseModel):
    """Reservation model representing a booking."""
    id: str
    price: Optional[Decimal] = None

    @validator('price', pre=True, always=True)
    def convert_price_to_float(cls, v):
        if v is not None:
            return float(v)
        return v

class Message(BaseModel):
    """Message model representing a communication between host and guest."""
    message_id: str
    property: Property
    guest: Guest
    content: str
    timestamp: datetime
    direction: str  # "incoming" or "outgoing"
    reservation: Optional[Reservation] = None
    message_type: str  # "automated" or "manual"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('direction')
    def validate_direction(cls, v):
        """Validate that direction is either 'incoming' or 'outgoing'."""
        if v not in ["incoming", "outgoing"]:
            raise ValueError("Direction must be 'incoming' or 'outgoing'")
        return v
    
    @validator('message_type')
    def validate_message_type(cls, v):
        """Validate that message_type is either 'automated' or 'manual'."""
        if v not in ["automated", "manual"]:
            raise ValueError("Message type must be 'automated' or 'manual'")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary suitable for MongoDB, converting Decimals to float and handling nested models."""
        from pydantic import BaseModel
        def convert(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, BaseModel):
                return convert(obj.model_dump(by_alias=True))
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            else:
                return obj
        return convert(self)
    
    @classmethod
    def from_api_response(cls, api_data: Dict[str, Any]) -> "Message":
        """Create a Message instance from API response data."""
        # Log the raw API response for debugging
        logger.info("Raw API response data: %s", api_data)
        
        # Extract message content from conversationMessages array
        content = ""
        if "conversationMessages" in api_data:
            logger.info("Found conversationMessages: %s", api_data["conversationMessages"])
            if isinstance(api_data["conversationMessages"], list) and len(api_data["conversationMessages"]) > 0:
                first_message = api_data["conversationMessages"][0]
                logger.info("First message in conversation: %s", first_message)
                if isinstance(first_message, dict):
                    content = first_message.get("body", "")
                    logger.info("Extracted content: %s", content)

        # Extract property information
        property_data = {
            "id": str(api_data.get("listingMapId", "")),
            "name": api_data.get("listingName", "")
        }
        logger.info("Extracted property data: %s", property_data)

        # Extract guest information
        guest_data = {
            "name": api_data.get("recipientName", ""),
            "email": api_data.get("recipientEmail", ""),
            "phone": api_data.get("phone"),
            "nationality": None  # Not available in API response
        }
        logger.info("Extracted guest data: %s", guest_data)

        # Extract reservation information
        reservation_data = None
        if "Reservation" in api_data:
            reservation = api_data["Reservation"]
            logger.info("Found reservation data: %s", reservation)
            reservation_data = {
                "id": str(reservation.get("reservationId", "")),
                "price": float(reservation.get("totalPrice", 0.0))
            }
            logger.info("Extracted reservation data: %s", reservation_data)

        # Determine message type
        message_type = "manual"
        if api_data.get("type", "").startswith("automated"):
            message_type = "automated"
        logger.info("Determined message type: %s", message_type)

        # Create and return the message instance
        message = cls(
            message_id=str(api_data.get("id", "")),
            property=property_data,
            guest=guest_data,
            content=content,
            timestamp=api_data.get("messageSentOn"),
            direction="incoming" if api_data.get("isIncoming", False) else "outgoing",
            reservation=reservation_data,
            message_type=message_type
        )
        logger.info("Created message instance: %s", message.model_dump())
        return message 