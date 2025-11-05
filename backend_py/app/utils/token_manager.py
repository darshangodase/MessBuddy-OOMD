"""
JWT Token management utility.
Demonstrates encapsulation and single responsibility principle.
"""
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import settings
from app.exceptions import AuthenticationError
from typing import Dict, Any


class TokenManager:
    """
    Handles JWT token creation and validation.
    
    OOP Principles:
    - Encapsulation: Token logic hidden behind clean interface
    - Single Responsibility: Only handles token operations
    """
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS
    
    def create_token(self, user_id: str, role: str) -> str:
        """
        Create JWT access token for authenticated user.
        
        Args:
            user_id: User's database ID
            role: User's role (User, Mess Owner)
            
        Returns:
            Encoded JWT token string
        """
        payload = {
            "id": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dictionary
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    def decode_token_without_verification(self, token: str) -> Dict[str, Any]:
        """
        Decode token without verification (for debugging).
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except JWTError:
            return {}
