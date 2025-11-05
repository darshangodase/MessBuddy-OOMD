"""
Prebooking Document Model.
Demonstrates OOP with Beanie Document.
"""
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Literal
from beanie import PydanticObjectId


class Prebooking(Document):
    """
    Prebooking document model.
    
    OOP Principle: Encapsulation
    - Encapsulates prebooking data and behavior
    """
    
    menuId: PydanticObjectId
    messId: PydanticObjectId
    userId: PydanticObjectId
    date: str
    time: str
    quantity: int = Field(default=1, ge=1)
    status: Literal["Pending", "Confirmed", "Cancelled"] = "Pending"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "prebookings"  # MongoDB collection name
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "_id": str(self.id),
            "menuId": str(self.menuId),
            "messId": str(self.messId),
            "userId": str(self.userId),
            "date": self.date,
            "time": self.time,
            "quantity": self.quantity,
            "status": self.status,
            "createdAt": self.createdAt.isoformat(),
            "updatedAt": self.updatedAt.isoformat()
        }
