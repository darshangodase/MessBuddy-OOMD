"""
User router (controller).
Demonstrates protected routes with dependency injection.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from app.schemas.user import UserResponse, UpdateUserRequest
from app.services.user_service import UserService
from app.models.user import User
from app.dependencies import get_current_user
from app.exceptions import MessBuddyException, convert_exception_to_http
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["User"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile.
    
    OOP Principle: Dependency Injection
    - get_current_user dependency automatically injects authenticated user
    
    Args:
        current_user: Injected authenticated user
        
    Returns:
        User profile data
    """
    return UserResponse(**current_user.to_public_dict())


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    payload: UpdateUserRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile.
    
    Args:
        payload: Update request data
        current_user: Injected authenticated user
        
    Returns:
        Updated user profile
    """
    try:
        user_service = UserService()
        updated_user = await user_service.update_user(
            user_id=str(current_user.id),
            username=payload.username,
            email=payload.email
        )
        
        return UserResponse(**updated_user.to_public_dict())
    
    except MessBuddyException as e:
        logger.error(f"Profile update error: {e.message}")
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Unexpected profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID (MongoDB _id or numeric UserID).
    
    Args:
        user_id: User database ID (MongoDB ObjectId) or numeric UserID
        current_user: Injected authenticated user
        
    Returns:
        User profile data
    """
    try:
        user_service = UserService()
        
        # Try to parse as integer (UserID) first
        try:
            numeric_user_id = int(user_id)
            # Search by UserID field
            user = await User.find_one({"UserID": numeric_user_id})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        except ValueError:
            # If not a number, treat as MongoDB ObjectId
            user = await user_service.get_user_by_id(user_id)
        
        return UserResponse(**user.to_public_dict())
    
    except HTTPException:
        raise
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/signout")
async def signout(response: Response):
    """
    Sign out current user by clearing auth cookie.
    
    Returns:
        Success message
    """
    # Clear the access_token cookie with exact same parameters as set
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="none"
    )
    
    return {
        "success": True,
        "message": "User has been signed out"
    }
