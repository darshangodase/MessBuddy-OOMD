"""
User Subscription document model.
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional, Literal
from datetime import datetime


class UserSubscription(Document):
    """
    User Subscription model linking users to subscription plans.
    
    Attributes:
        userId: Reference to User
        planId: Reference to SubscriptionPlan
        startDate: Subscription start date
        endDate: Subscription end date
        status: Subscription status
        paymentId: Payment transaction ID
        paymentStatus: Payment status
        cancellationReason: Reason for cancellation if any
    """
    
    userId: PydanticObjectId = Field(..., description="User ID")
    planId: PydanticObjectId = Field(..., description="Subscription Plan ID")
    startDate: datetime = Field(...)
    endDate: datetime = Field(...)
    status: Literal['Active', 'Expired', 'Cancelled', 'Pending', 'Plan Removed'] = Field(default='Pending')
    paymentId: Optional[str] = None
    paymentStatus: Literal['Pending', 'Completed', 'Failed'] = Field(default='Pending')
    cancellationReason: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "_id": str(self.id),
            "userId": str(self.userId),
            "planId": str(self.planId),
            "startDate": self.startDate.isoformat() if self.startDate else None,
            "endDate": self.endDate.isoformat() if self.endDate else None,
            "status": self.status,
            "paymentId": self.paymentId,
            "paymentStatus": self.paymentStatus,
            "cancellationReason": self.cancellationReason,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
    
    class Settings:
        name = "usersubscriptions"
        indexes = [
            [("userId", 1), ("planId", 1), ("status", 1)]
        ]
