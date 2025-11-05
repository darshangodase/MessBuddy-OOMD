"""
Subscription Plan document model.
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional, Literal
from datetime import datetime


class SubscriptionPlan(Document):
    """
    Subscription Plan model for mess meal subscriptions.
    
    Attributes:
        messId: Reference to Mess owner
        planName: Name of the subscription plan
        duration: Plan duration (Daily/Weekly/Monthly)
        mealType: Type of meal (Veg/Non-Veg/Jain)
        price: Plan price
        description: Plan description
        isActive: Whether plan is currently active
    """
    
    messId: PydanticObjectId = Field(..., description="Mess owner ID")
    planName: str = Field(..., min_length=1, max_length=200)
    duration: Literal['Daily', 'Weekly', 'Monthly'] = Field(...)
    mealType: Literal['Veg', 'Non-Veg', 'Jain'] = Field(...)
    price: float = Field(..., ge=0)
    description: str = Field(..., min_length=1, max_length=1000)
    isActive: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "_id": str(self.id),
            "messId": str(self.messId),
            "planName": self.planName,
            "duration": self.duration,
            "mealType": self.mealType,
            "price": self.price,
            "description": self.description,
            "isActive": self.isActive,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    class Settings:
        name = "subscriptionplans"
