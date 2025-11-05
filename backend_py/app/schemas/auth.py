"""
Authentication request/response schemas.
Demonstrates data validation with Pydantic.
"""
from pydantic import BaseModel, EmailStr, Field
from app.models.user import LoginRole


class SignupRequest(BaseModel):
    """
    Signup request schema.
    
    OOP Principle: Encapsulation
    - Validates input data before processing
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    login_role: LoginRole
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepass123",
                "login_role": "User"
            }
        }


class SigninRequest(BaseModel):
    """Signin request schema."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    login_role: LoginRole
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "securepass123",
                "login_role": "User"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response schema."""
    success: bool
    message: str
    user: dict
    token: str = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "Login_Role": "User"
                },
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
