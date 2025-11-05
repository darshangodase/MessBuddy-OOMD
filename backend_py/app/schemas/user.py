"""
User-related schemas.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserResponse(BaseModel):
    """User profile response schema."""
    id: str
    username: str
    email: EmailStr
    Login_Role: str
    UserID: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john@example.com",
                "Login_Role": "User",
                "UserID": 1699123456
            }
        }


class UpdateUserRequest(BaseModel):
    """Request schema for updating user profile."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_updated",
                "email": "john.new@example.com"
            }
        }
