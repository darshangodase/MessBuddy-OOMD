"""
FastAPI dependencies for dependency injection.
Demonstrates dependency injection OOP pattern.
"""
from fastapi import Depends, Cookie, HTTPException, status
from typing import Optional
from app.services.auth_service import AuthService
from app.models.user import User
from app.exceptions import AuthenticationError


async def get_current_user(
    access_token: Optional[str] = Cookie(None)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    OOP Principle: Dependency Injection
    - Injected into route handlers that require authentication
    
    Args:
        access_token: JWT token from cookie
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        auth_service = AuthService()
        user = await auth_service.verify_token_and_get_user(access_token)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


async def get_current_mess_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to ensure current user is a Mess Owner.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if they are a Mess Owner
        
    Raises:
        HTTPException: If user is not a Mess Owner
    """
    if not current_user.is_mess_owner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Mess Owners can perform this action"
        )
    
    return current_user
