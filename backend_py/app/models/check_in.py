"""
Check-In document model.
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional, Literal
from datetime import datetime


class CheckIn(Document):
    """
    Check-In model for meal access tracking.
    
    Attributes:
        userId: Reference to User
        messId: Reference to Mess
        mealPassId: Reference to MealPass
        mealType: Type of meal (breakfast/lunch/dinner)
        status: Check-in status (success/failed)
        failureReason: Reason for failure if any
    """
    
    userId: PydanticObjectId = Field(..., description="User ID")
    messId: PydanticObjectId = Field(..., description="Mess ID")
    mealPassId: PydanticObjectId = Field(..., description="Meal Pass ID")
    mealType: Literal['breakfast', 'lunch', 'dinner'] = Field(...)
    status: Literal['success', 'failed'] = Field(...)
    failureReason: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "_id": str(self.id),
            "userId": str(self.userId),
            "messId": str(self.messId),
            "mealPassId": str(self.mealPassId),
            "mealType": self.mealType,
            "status": self.status,
            "failureReason": self.failureReason,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    class Settings:
        name = "checkins"
