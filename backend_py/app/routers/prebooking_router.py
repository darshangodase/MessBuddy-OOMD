"""
Prebooking router (controller).
Demonstrates CRUD operations for meal prebookings.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.prebooking import Prebooking
from app.models.user import User
from app.models.mess import Mess
from app.dependencies import get_current_user
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from beanie import PydanticObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prebooking", tags=["Prebooking"])


class PrebookingRequest(BaseModel):
    """Prebooking creation request."""
    menuId: str
    messId: str
    userId: str
    date: str
    time: str
    quantity: int = Field(default=1, ge=1)


class UpdateStatusRequest(BaseModel):
    """Update prebooking status request."""
    status: Literal["Pending", "Confirmed", "Cancelled"]


@router.post("/")
async def create_prebooking(payload: PrebookingRequest):
    """
    Create new prebooking.
    
    Args:
        payload: Prebooking data
        
    Returns:
        Created prebooking
    """
    try:
        # Validate references exist
        user = await User.get(PydanticObjectId(payload.userId))
        mess = await Mess.get(PydanticObjectId(payload.messId))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if not mess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mess not found"
            )
        
        # Create prebooking
        prebooking = Prebooking(
            menuId=PydanticObjectId(payload.menuId),
            messId=PydanticObjectId(payload.messId),
            userId=PydanticObjectId(payload.userId),
            date=payload.date,
            time=payload.time,
            quantity=payload.quantity,
            status="Pending"
        )
        await prebooking.insert()
        
        # TODO: Send email notification (optional - requires email configuration)
        
        return {
            "message": "Prebooking created successfully",
            "prebooking": prebooking.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create prebooking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during prebooking"
        )


@router.get("/")
async def get_all_prebookings():
    """
    Get all prebookings (admin endpoint).
    
    Returns:
        List of all prebookings
    """
    try:
        prebookings = await Prebooking.find_all().to_list()
        
        return {
            "prebooking": [p.to_dict() for p in prebookings]
        }
    
    except Exception as e:
        logger.error(f"Get all prebookings error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}")
async def get_user_prebookings(user_id: str):
    """
    Get prebookings for a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of user's prebookings
    """
    try:
        prebookings = await Prebooking.find(
            Prebooking.userId == PydanticObjectId(user_id)
        ).to_list()
        
        # Populate mess and menu details
        result = []
        for prebooking in prebookings:
            pb_dict = prebooking.to_dict()
            
            # Get mess details
            mess = await Mess.get(prebooking.messId)
            if mess:
                pb_dict["messId"] = {
                    "_id": str(mess.id),
                    "Mess_Name": mess.Mess_Name,
                    "Address": mess.Address,
                    "Image": mess.Image
                }
            
            result.append(pb_dict)
        
        return result
    
    except Exception as e:
        logger.error(f"Get user prebookings error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/mess/{mess_id}")
async def get_mess_prebookings(mess_id: str):
    """
    Get prebookings for a specific mess.
    
    Args:
        mess_id: Mess ID
        
    Returns:
        List of mess's prebookings
    """
    try:
        prebookings = await Prebooking.find(
            Prebooking.messId == PydanticObjectId(mess_id)
        ).to_list()
        
        # Populate user details
        result = []
        for prebooking in prebookings:
            pb_dict = prebooking.to_dict()
            
            # Get user details
            user = await User.get(prebooking.userId)
            if user:
                pb_dict["userId"] = {
                    "_id": str(user.id),
                    "username": user.username,
                    "email": user.email
                }
            
            result.append(pb_dict)
        
        return result
    
    except Exception as e:
        logger.error(f"Get mess prebookings error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{prebooking_id}")
async def update_prebooking_status(
    prebooking_id: str,
    payload: UpdateStatusRequest
):
    """
    Update prebooking status.
    
    Args:
        prebooking_id: Prebooking ID
        payload: New status
        
    Returns:
        Updated prebooking
    """
    try:
        prebooking = await Prebooking.get(PydanticObjectId(prebooking_id))
        
        if not prebooking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prebooking not found"
            )
        
        # Update status
        prebooking.status = payload.status
        prebooking.updatedAt = datetime.utcnow()
        await prebooking.save()
        
        # TODO: Send email notification (optional)
        
        return {
            "message": "Prebooking status updated successfully",
            "prebooking": prebooking.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update prebooking status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the prebooking status"
        )


@router.delete("/{booking_id}")
async def delete_prebooking(booking_id: str):
    """
    Delete a prebooking.
    
    Args:
        booking_id: Prebooking ID
        
    Returns:
        Success message
    """
    try:
        prebooking = await Prebooking.get(PydanticObjectId(booking_id))
        
        if not prebooking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prebooking not found"
            )
        
        await prebooking.delete()
        
        return {
            "message": "Prebooking deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete prebooking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting prebooking"
        )
