"""
Mess document model.
Demonstrates OOP data modeling with relationships.
"""
from beanie import Document, Link, PydanticObjectId
from pydantic import Field, HttpUrl
from typing import Optional, List, Union, Any
from datetime import datetime


class Mess(Document):
    """
    Mess (dining establishment) document model.
    
    OOP Principles:
    - Inheritance: Inherits from Beanie Document
    - Composition: Contains ratings and references to users
    - Encapsulation: Business logic for ratings
    
    Attributes:
        Mess_ID: Unique numeric identifier
        Mess_Name: Name of the mess
        Mobile_No: Contact phone number
        Capacity: Maximum capacity
        Address: Physical address
        Owner_ID: Reference to User who owns this mess
        Description: Mess description
        Ratings: List of rating values
        RatedBy: List of user IDs who rated
        UserID: Numeric user identifier (legacy)
        Image: URL to mess image
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    Mess_ID: int = Field(..., unique=True)
    Mess_Name: str = Field(..., min_length=1, max_length=100)
    Mobile_No: Optional[str] = Field(None, max_length=15)
    Capacity: Optional[int] = Field(None, ge=0)
    Address: Optional[str] = Field(None, max_length=500)
    Owner_ID: PydanticObjectId = Field(...)
    Description: Optional[str] = Field(default="", max_length=1000)
    Ratings: List[Any] = Field(default_factory=list)  # Flexible to handle int or str (mixed data)
    RatedBy: List[Any] = Field(default_factory=list)  # Flexible to handle ObjectId, str, or int
    UserID: int = Field(...)
    Image: Optional[str] = Field(
        default="http://res.cloudinary.com/dq3ro4o3c/image/upload/v1734445757/gngcgm82wwo5t0desu0w.jpg"
    )
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "messes"
        indexes = [
            "Mess_ID",
            "Owner_ID",
        ]
    
    def calculate_average_rating(self) -> float:
        """
        Calculate average rating for the mess.
        Handles mixed data types (int or str) in Ratings list for legacy data.
        
        OOP Principle: Encapsulation
        - Business logic encapsulated in the model
        
        Returns:
            Average rating (0.0 if no ratings)
        """
        if not self.Ratings:
            return 0.0
        
        # Filter and convert to numbers, handling mixed data types
        valid_ratings = []
        for rating in self.Ratings:
            try:
                if isinstance(rating, (int, float)):
                    valid_ratings.append(rating)
                elif isinstance(rating, str) and rating.replace('.', '', 1).isdigit():
                    valid_ratings.append(float(rating))
            except:
                continue
        
        if not valid_ratings:
            return 0.0
            
        return sum(valid_ratings) / len(valid_ratings)
    
    def add_rating(self, user_id: str, rating: int) -> bool:
        """
        Add a rating from a user.
        
        Args:
            user_id: ID of user submitting rating (string)
            rating: Rating value (1-5)
            
        Returns:
            True if rating was added, False if user already rated
        """
        if user_id in [str(uid) for uid in self.RatedBy]:
            return False
        
        self.Ratings.append(rating)
        self.RatedBy.append(PydanticObjectId(user_id))
        return True
    
    def has_user_rated(self, user_id: str) -> bool:
        """
        Check if user has already rated this mess.
        
        Args:
            user_id: User ID to check (string)
            
        Returns:
            True if user has rated
        """
        return user_id in [str(uid) for uid in self.RatedBy]
    
    def to_dict(self) -> dict:
        """
        Convert mess to dictionary representation.
        
        Returns:
            Dictionary with all mess fields including calculated average rating
        """
        # Handle RatedBy conversion - support both ObjectId and string formats
        rated_by_list = []
        for user_id in self.RatedBy:
            try:
                rated_by_list.append(str(user_id))
            except:
                # If conversion fails, skip it
                continue
                
        return {
            "id": str(self.id),
            "_id": str(self.id),  # For frontend compatibility
            "Mess_ID": self.Mess_ID,
            "Mess_Name": self.Mess_Name,
            "Mobile_No": self.Mobile_No,
            "Capacity": self.Capacity,
            "Address": self.Address,
            "Owner_ID": str(self.Owner_ID),
            "Description": self.Description,
            "average_rating": self.calculate_average_rating(),
            "total_ratings": len(self.Ratings),
            "Image": self.Image,
            "Ratings": self.Ratings,
            "RatedBy": rated_by_list,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "Mess_ID": 1699123456,
                "Mess_Name": "Golden Mess",
                "Mobile_No": "+919876543210",
                "Capacity": 100,
                "Address": "123 Campus Road, University Area",
                "Owner_ID": "507f1f77bcf86cd799439011",
                "Description": "Best mess in town with home-style cooking",
                "UserID": 1699123456,
                "Image": "https://example.com/mess.jpg"
            }
        }
