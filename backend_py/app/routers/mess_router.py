"""
Mess router (controller).
Demonstrates CRUD operations with authorization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.mess_service import MessService
from app.models.user import User
from app.models.mess import Mess
from app.dependencies import get_current_user, get_current_mess_owner
from app.exceptions import MessBuddyException, convert_exception_to_http
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mess", tags=["Mess"])


class MessResponse(BaseModel):
    """Mess response schema."""
    id: str
    underscore_id: str = Field(..., alias='_id')  # For frontend compatibility
    Mess_ID: int
    Mess_Name: str
    Mobile_No: Optional[str]
    Capacity: Optional[int]
    Address: Optional[str]
    Owner_ID: str
    Description: str
    average_rating: float
    total_ratings: int
    Image: str
    Ratings: List[int] = []
    RatedBy: List[str] = []
    
    class Config:
        populate_by_name = True  # Allow population by field name or alias
        json_schema_extra = {"by_alias": True}  # Serialize using aliases


class UpdateMessRequest(BaseModel):
    """Update mess request schema."""
    Mess_Name: Optional[str] = None
    Mobile_No: Optional[str] = None
    Capacity: Optional[int] = None
    Address: Optional[str] = None
    Description: Optional[str] = None
    Image: Optional[str] = None


class CreateMessRequest(BaseModel):
    """Create mess request schema."""
    Mess_Name: str
    Mobile_No: Optional[str] = ""
    Capacity: Optional[int] = 0
    Address: Optional[str] = ""
    Description: Optional[str] = ""
    Image: Optional[str] = "http://res.cloudinary.com/dq3ro4o3c/image/upload/v1734445757/gngcgm82wwo5t0desu0w.jpg"


@router.get("/")
async def get_all_messes():
    """
    Get all messes (public endpoint).
    
    Returns:
        List of all messes with overall statistics
    """
    try:
        mess_service = MessService()
        messes = await mess_service.get_all_messes()
        
        # Calculate overall average rating from all messes
        if messes:
            total_rating = sum(mess.calculate_average_rating() for mess in messes)
            overall_avg_rating = total_rating / len(messes)
        else:
            overall_avg_rating = 0.0
        
        # Return raw dicts to preserve _id field
        return {
            "success": True,
            "messes": [mess.to_dict() for mess in messes] if messes else [],
            "avgRating": round(overall_avg_rating, 1)  # Overall average rating
        }
    
    except Exception as e:
        logger.error(f"Get all messes error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/create/{owner_id}")
async def create_mess(owner_id: str, payload: CreateMessRequest):
    """
    Create new mess for owner (public endpoint - matches Node.js).
    
    Args:
        owner_id: Owner's user ID (MongoDB _id)
        payload: Mess creation data
        
    Returns:
        Created mess data
    """
    try:
        from beanie import PydanticObjectId
        from datetime import datetime
        
        # Verify owner exists
        user = await User.get(PydanticObjectId(owner_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create mess
        mess = Mess(
            Mess_ID=int(datetime.utcnow().timestamp() * 1000),
            Mess_Name=payload.Mess_Name,
            Mobile_No=payload.Mobile_No or "",
            Capacity=payload.Capacity or 0,
            Address=payload.Address or "",
            Owner_ID=PydanticObjectId(owner_id),
            Description=payload.Description or "",
            Image=payload.Image or "http://res.cloudinary.com/dq3ro4o3c/image/upload/v1734445757/gngcgm82wwo5t0desu0w.jpg",
            Ratings=[],
            RatedBy=[]
        )
        await mess.insert()
        
        return {
            "success": True,
            "message": "Mess created successfully",
            "mess": mess.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.get("/{owner_id}")
async def get_mess_by_owner(owner_id: str):
    """
    Get mess by Owner_ID (matches Node.js getMess).
    Note: This gets mess by OWNER ID, not mess ID.
    
    Args:
        owner_id: Owner's user ID
        
    Returns:
        Mess data
    """
    try:
        from beanie import PydanticObjectId
        
        # Find mess by Owner_ID
        mess = await Mess.find_one({"Owner_ID": PydanticObjectId(owner_id)})
        
        if not mess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mess not found"
            )
        
        return {
            "success": True,
            "mess": mess.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get mess by owner error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.put("/update/{owner_id}")
async def update_mess_by_owner(owner_id: str, payload: UpdateMessRequest):
    """
    Update mess by Owner_ID (matches Node.js updateMess).
    
    Args:
        owner_id: Owner's user ID
        payload: Update data
        
    Returns:
        Updated mess data
    """
    try:
        from beanie import PydanticObjectId
        
        # Find and update mess by Owner_ID
        mess = await Mess.find_one({"Owner_ID": PydanticObjectId(owner_id)})
        
        if not mess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mess not found"
            )
        
        # Update fields
        update_data = payload.dict(exclude_none=True)
        for key, value in update_data.items():
            setattr(mess, key, value)
        
        await mess.save()
        
        return {
            "success": True,
            "message": "Mess updated successfully",
            "mess": mess.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.delete("/delete/{owner_id}")
async def delete_mess_by_owner(owner_id: str):
    """
    Delete mess by Owner_ID (matches Node.js deleteMess).
    
    Args:
        owner_id: Owner's user ID
        
    Returns:
        Success message
    """
    try:
        from beanie import PydanticObjectId
        
        # Find and delete mess by Owner_ID
        mess = await Mess.find_one({"Owner_ID": PydanticObjectId(owner_id)})
        
        if not mess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mess not found"
            )
        
        await mess.delete()
        
        return {
            "success": True,
            "message": "Mess deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.get("/my-mess")
async def get_my_mess(current_user: User = Depends(get_current_mess_owner)):
    """
    Get mess owned by current user (Mess Owner only).
    
    OOP Principle: Authorization via dependency injection
    
    Args:
        current_user: Injected mess owner user
        
    Returns:
        Mess owned by current user
    """
    try:
        mess_service = MessService()
        mess = await mess_service.get_mess_by_owner(str(current_user.id))
        
        if not mess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mess not found"
            )
        
        return mess.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get my mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{mess_id}")
async def get_mess(mess_id: str):
    """
    Get mess by ID (public endpoint).
    
    Args:
        mess_id: Mess database ID
        
    Returns:
        Mess data
    """
    try:
        mess_service = MessService()
        mess = await mess_service.get_mess_by_id(mess_id)
        
        return mess.to_dict()
    
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Get mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{mess_id}")
async def update_mess(
    mess_id: str,
    payload: UpdateMessRequest,
    current_user: User = Depends(get_current_mess_owner)
):
    """
    Update mess (Mess Owner only, must own the mess).
    
    Args:
        mess_id: Mess database ID
        payload: Update request data
        current_user: Injected mess owner user
        
    Returns:
        Updated mess data
    """
    try:
        mess_service = MessService()
        
        # Convert payload to dict, excluding None values
        update_data = payload.dict(exclude_none=True)
        
        updated_mess = await mess_service.update_mess(
            mess_id=mess_id,
            owner_id=str(current_user.id),
            **update_data
        )
        
        return updated_mess.to_dict()
    
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Update mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/read/{mess_id}")
async def read_mess(mess_id: str):
    """
    Get mess by ID (public endpoint - alias for compatibility).
    
    Args:
        mess_id: Mess database ID
        
    Returns:
        Mess data wrapped in success response
    """
    try:
        mess_service = MessService()
        mess = await mess_service.get_mess_by_id(mess_id)
        
        return {
            "success": True,
            "mess": mess.to_dict()
        }
    
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Read mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/rating/{mess_id}")
async def get_rating(mess_id: str):
    """
    Get average rating for a mess (public endpoint).
    
    Args:
        mess_id: Mess database ID
        
    Returns:
        Average rating and total ratings count
    """
    try:
        mess_service = MessService()
        mess = await mess_service.get_mess_by_id(mess_id)
        
        return {
            "success": True,
            "rating": mess.calculate_average_rating(),
            "total_ratings": len(mess.Ratings)
        }
    
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Get rating error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


class RatingRequest(BaseModel):
    """Rating request schema."""
    rating: int


@router.put("/rating/{mess_id}/{user_id}")
async def update_rating(
    mess_id: str,
    user_id: str,
    payload: RatingRequest
):
    """
    Add or update rating for a mess (public endpoint for compatibility).
    
    Args:
        mess_id: Mess database ID
        user_id: User ID providing the rating
        payload: Rating value (1-5)
        
    Returns:
        Success message with updated average rating
    """
    try:
        # Validate rating value
        if payload.rating < 1 or payload.rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )
        
        mess_service = MessService()
        mess = await mess_service.get_mess_by_id(mess_id)
        
        # Check if user has already rated
        if mess.has_user_rated(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already rated this mess"
            )
        
        # Add rating
        mess.add_rating(user_id, payload.rating)
        await mess.save()
        
        return {
            "success": True,
            "message": "Rating submitted successfully",
            "rating": mess.calculate_average_rating(),
            "total_ratings": len(mess.Ratings)
        }
    
    except HTTPException:
        raise
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Update rating error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/hasrated/{mess_id}/{user_id}")
async def has_user_rated(mess_id: str, user_id: str):
    """
    Check if a user has rated a mess (public endpoint).
    
    Args:
        mess_id: Mess database ID
        user_id: User ID to check
        
    Returns:
        Whether user has rated and their rating value if they have
    """
    try:
        mess_service = MessService()
        mess = await mess_service.get_mess_by_id(mess_id)
        
        has_rated = mess.has_user_rated(user_id)
        user_rating = 0
        
        if has_rated:
            # Find the user's rating
            try:
                user_index = mess.RatedBy.index(user_id)
                user_rating = mess.Ratings[user_index]
            except (ValueError, IndexError):
                user_rating = 0
        
        return {
            "success": True,
            "hasRated": has_rated,
            "rating": user_rating
        }
    
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Has user rated error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{mess_id}")
async def delete_mess(
    mess_id: str,
    current_user: User = Depends(get_current_mess_owner)
):
    """
    Delete mess (Mess Owner only, must own the mess).
    
    Args:
        mess_id: Mess database ID
        current_user: Injected mess owner user
        
    Returns:
        Success message
    """
    try:
        mess_service = MessService()
        await mess_service.delete_mess(mess_id, str(current_user.id))
        
        return {
            "success": True,
            "message": "Mess deleted successfully"
        }
    
    except MessBuddyException as e:
        raise convert_exception_to_http(e)
    except Exception as e:
        logger.error(f"Delete mess error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
