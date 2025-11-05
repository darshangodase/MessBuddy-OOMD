"""
Meal Pass document model.
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional
from datetime import datetime


class MealPass(Document):
    """
    Meal Pass model for QR-based meal access.
    
    Attributes:
        userId: Reference to User
        subscriptionId: Reference to UserSubscription
        messId: Reference to Mess owner
        qrCode: Unique QR code hash
        isActive: Whether pass is active
        isBlocked: Whether pass is blocked
        blockReason: Reason for blocking if any
        validFrom: Pass validity start date
        validTill: Pass validity end date
    """
    
    userId: PydanticObjectId = Field(..., description="User ID")
    subscriptionId: PydanticObjectId = Field(..., description="Subscription ID")
    messId: PydanticObjectId = Field(..., description="Mess owner ID")
    qrCode: str = Field(..., min_length=1, max_length=500, unique=True)
    isActive: bool = Field(default=True)
    isBlocked: bool = Field(default=False)
    blockReason: Optional[str] = None
    validFrom: Optional[datetime] = None
    validTill: Optional[datetime] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "_id": str(self.id),
            "userId": str(self.userId),
            "subscriptionId": str(self.subscriptionId),
            "messId": str(self.messId),
            "qrCode": self.qrCode,
            "isActive": self.isActive,
            "isBlocked": self.isBlocked,
            "blockReason": self.blockReason,
            "validFrom": self.validFrom.isoformat() if self.validFrom else None,
            "validTill": self.validTill.isoformat() if self.validTill else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    class Settings:
        name = "mealpasses"
