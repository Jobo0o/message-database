"""
Pydantic models for the Hostaway Message Database application.
Defines the data structures for messages and related entities.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal

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
        """Convert the model to a dictionary suitable for MongoDB."""
        return self.model_dump(by_alias=True)
    
    @classmethod
    def from_api_response(cls, api_data: Dict[str, Any]) -> 'Message':
        """
        Create a Message instance from Hostaway API response data.
        
        Args:
            api_data: Raw data from the Hostaway API
            
        Returns:
            Message: A processed Message instance
        """
        # This is a placeholder. The actual implementation will depend
        # on the Hostaway API response format, which will need to be
        # mapped to our model structure.
        return cls(
            message_id=str(api_data.get("id", "")),
            property=Property(
                id=str(api_data.get("propertyId", "")),
                name=api_data.get("propertyName", "")
            ),
            guest=Guest(
                name=api_data.get("guestName", ""),
                email=api_data.get("guestEmail", None),
                phone=api_data.get("guestPhone", None),
                nationality=api_data.get("guestNationality", None)
            ),
            content=api_data.get("content", ""),
            timestamp=datetime.fromisoformat(api_data.get("timestamp", datetime.now().isoformat())),
            direction="incoming" if api_data.get("isIncoming", False) else "outgoing",
            reservation=Reservation(
                id=str(api_data.get("reservationId", "")),
                price=Decimal(str(api_data.get("reservationPrice", 0)))
            ) if api_data.get("reservationId") else None,
            message_type="automated" if api_data.get("isAutomated", False) else "manual",
        ) 