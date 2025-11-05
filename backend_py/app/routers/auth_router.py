"""
Authentication router (controller).
Demonstrates thin controller layer with service delegation.
"""
from fastapi import APIRouter, Response, HTTPException, status
from app.schemas.auth import SignupRequest, SigninRequest, AuthResponse
from app.services.auth_service import AuthService
from app.services.mess_service import MessService
from app.exceptions import MessBuddyException, convert_exception_to_http
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, response: Response):
    """
    Register a new user account.
    
    OOP Flow:
    1. Router validates request (Pydantic schema)
    2. Delegates to AuthService (business logic)
    3. If Mess Owner, delegates to MessService
    4. Returns response and sets cookie
    
    Args:
        payload: Signup request data
        response: FastAPI response object
        
    Returns:
        Authentication response with user data and token
    """
    try:
        # Delegate to service layer
        auth_service = AuthService()
        
        # Debug logging
        logger.info(f"Signup attempt for user: {payload.username}, password length: {len(payload.password)}")
        
        user, token = await auth_service.signup(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            login_role=payload.login_role
        )
        
        # Create mess if user is Mess Owner
        if user.is_mess_owner():
            mess_service = MessService()
            await mess_service.create_mess_for_owner(
                owner_id=str(user.id),
                owner=user
            )
            logger.info(f"Created mess for owner: {user.username}")
        
        # Set httpOnly cookie
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,  # Set to False for local HTTP testing
            samesite="none",
            max_age=86400  # 24 hours
        )
        
        return AuthResponse(
            success=True,
            message="User created successfully",
            user=user.to_public_dict(),
            token=token
        )
    
    except MessBuddyException as e:
        logger.error(f"Signup error: {e.message}")
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Unexpected signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: SigninRequest, response: Response):
    """
    Authenticate existing user.
    
    OOP Flow:
    1. Router validates request
    2. Delegates to AuthService for authentication
    3. Returns response and sets cookie
    
    Args:
        payload: Signin request data
        response: FastAPI response object
        
    Returns:
        Authentication response with user data and token
    """
    try:
        # Delegate to service layer
        auth_service = AuthService()
        user, token = await auth_service.signin(
            username=payload.username,
            password=payload.password,
            login_role=payload.login_role
        )
        
        # Set httpOnly cookie
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=86400
        )
        
        return AuthResponse(
            success=True,
            message="Authentication successful",
            user=user.to_public_dict(),
            token=token
        )
    
    except MessBuddyException as e:
        logger.error(f"Signin error: {e.message}")
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Unexpected signin error: {str(e)}")
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
    response.delete_cookie(
        key="access_token",
        secure=True,
        samesite="none"
    )
    
    return {
        "success": True,
        "message": "Signed out successfully"
    }
