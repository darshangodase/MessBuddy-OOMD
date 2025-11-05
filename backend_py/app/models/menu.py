"""
Menu Document Model.
Demonstrates OOP with Beanie Document.
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import datetime
from typing import Optional, Literal


class Menu(Document):
    """
    Menu document model.
    
    OOP Principle: Encapsulation
    - Encapsulates menu item data and behavior
    """
    
    Menu_Name: str = Field(..., min_length=1)
    Description: str
    Price: float = Field(..., gt=0)
    Owner_ID: PydanticObjectId
    Availability: Literal["Yes", "No"] = "Yes"
    Food_Type: Literal["Veg", "Non-Veg"] = "Veg"
    Date: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "menus"  # MongoDB collection name
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "_id": str(self.id),
            "Menu_Name": self.Menu_Name,
            "Description": self.Description,
            "Price": self.Price,
            "Owner_ID": str(self.Owner_ID),
            "Availability": self.Availability,
            "Food_Type": self.Food_Type,
            "Date": self.Date.isoformat()
        }
