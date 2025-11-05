"""
Check-in router for meal access tracking.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.check_in import CheckIn
from app.models.meal_pass import MealPass
from app.models.user_subscription import UserSubscription
from beanie import PydanticObjectId
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/checkin", tags=["Check-In"])


class CreateCheckInRequest(BaseModel):
    mealPassId: str
    mealType: Literal['breakfast', 'lunch', 'dinner']


# Create check-in
@router.post("/{mess_id}", status_code=status.HTTP_201_CREATED)
async def create_checkin(mess_id: str, payload: CreateCheckInRequest):
    """Create a new check-in."""
    try:
        logger.info(f"Creating check-in for meal pass: {payload.mealPassId}")
        
        # Get meal pass
        meal_pass = await MealPass.get(PydanticObjectId(payload.mealPassId))
        if not meal_pass:
            logger.error(f"Meal pass not found: {payload.mealPassId}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Meal pass not found"}
            )
        
        logger.info(f"Meal pass found. Active: {meal_pass.isActive}, Blocked: {meal_pass.isBlocked}")
        
        # Check if meal pass is active and not blocked
        if not meal_pass.isActive or meal_pass.isBlocked:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"message": "Meal pass is inactive or blocked"}
            )
        
        # Get subscription and check if active
        subscription = await UserSubscription.get(meal_pass.subscriptionId)
        if not subscription:
            logger.error(f"Subscription not found: {meal_pass.subscriptionId}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Subscription not found"}
            )
        
        logger.info(f"Subscription status: {subscription.status}")
        
        if subscription.status != 'Active':
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"message": f"Subscription is not active. Current status: {subscription.status}"}
            )
        
        # Check if already checked in for this meal today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        logger.info(f"Checking for existing check-in between {today_start} and {today_end}")
        
        existing_checkin = await CheckIn.find_one(
            CheckIn.mealPassId == meal_pass.id,
            CheckIn.mealType == payload.mealType.lower(),
            CheckIn.created_at >= today_start,
            CheckIn.created_at < today_end
        )
        
        if existing_checkin:
            logger.warning(f"Duplicate check-in attempt for meal pass {payload.mealPassId}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Already checked in for this meal today"}
            )
        
        # Create check-in
        checkin = CheckIn(
            userId=meal_pass.userId,
            messId=meal_pass.messId,
            mealPassId=meal_pass.id,
            mealType=payload.mealType.lower(),
            status='success'
        )
        
        await checkin.insert()
        logger.info(f"Check-in created successfully: {checkin.id}")
        
        return checkin.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create check-in error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Get check-ins with filters
@router.get("/{mess_id}")
async def get_checkins(
    mess_id: str,
    userId: Optional[str] = None,
    date: Optional[str] = None,
    mealType: Optional[str] = None
):
    """Get check-ins with optional filters."""
    try:
        query = {"messId": PydanticObjectId(mess_id)}
        
        if userId:
            query["userId"] = PydanticObjectId(userId)
        if mealType:
            query["mealType"] = mealType.lower()
        if date:
            search_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            date_start = search_date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            query["created_at"] = {"$gte": date_start, "$lt": date_end}
        
        checkins = await CheckIn.find(query).sort("-created_at").to_list()
        
        # Populate user and meal pass details
        from app.models.user import User
        
        result = []
        for checkin in checkins:
            checkin_dict = checkin.to_dict()
            
            # Populate user info
            user = await User.get(checkin.userId)
            if user:
                checkin_dict["userId"] = {
                    "_id": str(user.id),
                    "username": user.username,
                    "email": user.email
                }
            
            # Populate meal pass info
            meal_pass = await MealPass.get(checkin.mealPassId)
            if meal_pass:
                subscription = await UserSubscription.get(meal_pass.subscriptionId)
                if subscription:
                    from app.models.subscription_plan import SubscriptionPlan
                    plan = await SubscriptionPlan.get(subscription.planId)
                    if plan:
                        checkin_dict["mealPassId"] = {
                            "_id": str(meal_pass.id),
                            "subscriptionId": {
                                "_id": str(subscription.id),
                                "planId": {
                                    "_id": str(plan.id),
                                    "planName": plan.planName
                                }
                            }
                        }
            
            result.append(checkin_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Get check-ins error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Get today's stats for a mess
@router.get("/today-stats/{mess_id}")
async def get_today_stats(mess_id: str):
    """Get today's check-in statistics for a mess."""
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Get all today's check-ins for this mess
        checkins = await CheckIn.find(
            CheckIn.messId == PydanticObjectId(mess_id),
            CheckIn.created_at >= today_start,
            CheckIn.created_at < today_end,
            CheckIn.status == 'success'
        ).to_list()
        
        # Count by meal type
        stats = {
            'breakfast': 0,
            'lunch': 0,
            'dinner': 0
        }
        
        for checkin in checkins:
            meal_type = checkin.mealType.lower()
            if meal_type in stats:
                stats[meal_type] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Get today stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
