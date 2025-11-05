"""
Feedback router (controller).
Demonstrates CRUD operations for user feedback.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.feedback import Feedback
from app.models.user import User
from app.dependencies import get_current_user
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    """Feedback submission request."""
    userID: str
    comments: str = Field(..., max_length=500)
    rating: int = Field(..., ge=1, le=5)


class FeedbackResponse(BaseModel):
    """Feedback response schema."""
    id: str
    userID: str
    comments: str
    rating: int
    submittedAt: str
    username: Optional[str] = None


@router.post("/")
async def create_feedback(payload: FeedbackRequest):
    """
    Create new feedback (public endpoint).
    
    Args:
        payload: Feedback data
        
    Returns:
        Created feedback
    """
    try:
        # Validate user exists
        from beanie import PydanticObjectId
        user = await User.get(PydanticObjectId(payload.userID))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create feedback
        feedback = Feedback(
            userID=PydanticObjectId(payload.userID),
            comments=payload.comments,
            rating=payload.rating
        )
        await feedback.insert()
        
        feedback_dict = feedback.to_dict()
        feedback_dict["username"] = user.username
        
        return {
            "message": "Feedback submitted successfully",
            "feedback": feedback_dict
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create feedback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feedback"
        )


@router.get("/")
async def get_all_feedbacks():
    """
    Get all feedbacks (public endpoint).
    
    Returns:
        List of all feedbacks with user details
    """
    try:
        feedbacks = await Feedback.find_all().sort("-submittedAt").to_list()
        
        # Populate user details
        feedback_list = []
        for feedback in feedbacks:
            user = await User.get(feedback.userID)
            feedback_dict = feedback.to_dict()
            feedback_dict["username"] = user.username if user else "Unknown"
            feedback_list.append(feedback_dict)
        
        return {
            "feedbacks": feedback_list
        }
    
    except Exception as e:
        logger.error(f"Get feedbacks error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedbacks"
        )
