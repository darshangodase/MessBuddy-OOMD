"""Meal Pass Router - QR code validation and meal pass management."""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

from ..models.meal_pass import MealPass
from ..models.user_subscription import UserSubscription
from ..models.user import User
from ..models.mess import Mess

router = APIRouter(prefix="/api/mealpass", tags=["MealPass"])


# Request Models
class ValidateMealPassRequest(BaseModel):
    qrCode: str


# Validate meal pass (QR scanner)
@router.post("/validate/{user_id}")
async def validate_meal_pass(user_id: str, payload: ValidateMealPassRequest):
    """Validate a meal pass QR code for check-in."""
    try:
        # Find meal pass by QR code
        meal_pass = await MealPass.find_one(MealPass.qrCode == payload.qrCode)
        
        if not meal_pass:
            raise HTTPException(status_code=404, detail="Invalid QR code")
        
        # Check if blocked
        if meal_pass.isBlocked:
            raise HTTPException(status_code=403, detail=f"User is blocked: {meal_pass.blockReason}")
        
        # Check if active
        if not meal_pass.isActive:
            raise HTTPException(status_code=403, detail="Meal pass is not active")
        
        # Check validity dates
        now = datetime.utcnow()
        if now < meal_pass.validFrom or now > meal_pass.validTill:
            raise HTTPException(status_code=403, detail="Meal pass has expired")
        
        # Get subscription details
        subscription = await UserSubscription.get(meal_pass.subscriptionId)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Check subscription status
        if subscription.status != 'Active':
            raise HTTPException(status_code=403, detail="Subscription is not active")
        
        # Get user details
        user = await User.get(meal_pass.userId)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get meal pass dict
        meal_pass_dict = meal_pass.to_dict()
        
        # Add user info
        meal_pass_dict["userId"] = {
            "_id": str(user.id),
            "username": user.username,
            "email": user.email
        }
        
        # Add subscription details
        from ..models.subscription_plan import SubscriptionPlan
        plan = await SubscriptionPlan.get(subscription.planId)
        if plan:
            meal_pass_dict["subscriptionId"] = {
                "_id": str(subscription.id),
                "status": subscription.status,
                "planId": {
                    "_id": str(plan.id),
                    "planName": plan.planName,
                    "mealType": plan.mealType,
                    "duration": plan.duration
                }
            }
        
        return {"valid": True, "mealPass": meal_pass_dict}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get current meal passes for user
@router.get("/current/{user_id}")
async def get_current_meal_passes(user_id: str):
    """Get all active meal passes for a user."""
    try:
        # Find active meal passes
        meal_passes = await MealPass.find(
            MealPass.userId == ObjectId(user_id),
            MealPass.isActive == True,
            MealPass.validTill > datetime.utcnow()
        ).to_list()
        
        if not meal_passes:
            raise HTTPException(status_code=404, detail="No active meal passes found")
        
        # Populate details for each pass
        result = []
        for meal_pass in meal_passes:
            pass_dict = meal_pass.to_dict()
            
            # Get subscription details
            subscription = await UserSubscription.get(meal_pass.subscriptionId)
            if subscription:
                from ..models.subscription_plan import SubscriptionPlan
                plan = await SubscriptionPlan.get(subscription.planId)
                if plan:
                    pass_dict["subscriptionId"] = {
                        "_id": str(subscription.id),
                        "status": subscription.status,
                        "startDate": subscription.startDate.isoformat() if subscription.startDate else None,
                        "endDate": subscription.endDate.isoformat() if subscription.endDate else None,
                        "planId": {
                            "_id": str(plan.id),
                            "planName": plan.planName,
                            "mealType": plan.mealType,
                            "duration": plan.duration,
                            "price": plan.price
                        }
                    }
            
            # Get mess details - find mess by Owner_ID (which is a User reference)
            user_ref = await User.get(meal_pass.messId)
            if user_ref:
                mess = await Mess.find_one(Mess.Owner_ID == meal_pass.messId)
                if mess:
                    pass_dict["messDetails"] = {
                        "_id": str(mess.id),
                        "Mess_Name": mess.Mess_Name,
                        "Address": mess.Address
                    }
            
            result.append(pass_dict)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
