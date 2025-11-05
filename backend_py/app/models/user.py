"""
User document model.
Demonstrates OOP data modeling with Beanie ODM.
"""
from beanie import Document
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class LoginRole(str, Enum):
    """
    User role enumeration.
    
    OOP Principle: Encapsulation
    - Restricts role values to valid options
    """
    USER = "User"
    MESS_OWNER = "Mess Owner"


class User(Document):
    """
    User document model representing a user account.
    
    OOP Principles:
    - Inheritance: Inherits from Beanie Document
    - Encapsulation: Data validation and business methods
    - Abstraction: Hides MongoDB implementation details
    
    Attributes:
        username: Unique username
        email: Unique email address
        password: Hashed password
        Login_Role: User role (User or Mess Owner)
        UserID: Numeric user identifier
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6)
    Login_Role: LoginRole = Field(...)
    UserID: int = Field(...)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Settings:
        """Beanie document settings."""
        name = "users"
        indexes = [
            "email",
            "username",
        ]
    
    def to_public_dict(self) -> dict:
        """
        Convert user to public dictionary (excludes password).
        
        OOP Principle: Encapsulation
        - Controls what data is exposed externally
        
        Returns:
            Dictionary with public user fields
        """
        return {
            "id": str(self.id),
            "_id": str(self.id),  # For frontend compatibility
            "username": self.username,
            "email": self.email,
            "Login_Role": self.Login_Role.value,
            "UserID": self.UserID,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def is_mess_owner(self) -> bool:
        """
        Check if user is a mess owner.
        
        Returns:
            True if user role is Mess Owner
        """
        return self.Login_Role == LoginRole.MESS_OWNER
    
    def is_regular_user(self) -> bool:
        """
        Check if user is a regular user.
        
        Returns:
            True if user role is User
        """
        return self.Login_Role == LoginRole.USER
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "Login_Role": "User",
                "UserID": 1699123456
            }
        }
