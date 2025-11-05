"""
User Feedback Document Model.
Demonstrates OOP with Beanie Document.
"""
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId


class Feedback(Document):
    """
    Feedback document model.
    
    OOP Principle: Encapsulation
    - Encapsulates feedback data and behavior
    """
    
    userID: PydanticObjectId
    comments: str = Field(..., max_length=500)
    rating: int = Field(..., ge=1, le=5)
    submittedAt: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "userfeedbacks"  # MongoDB collection name
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "userID": str(self.userID),
            "comments": self.comments,
            "rating": self.rating,
            "submittedAt": self.submittedAt.isoformat()
        }
