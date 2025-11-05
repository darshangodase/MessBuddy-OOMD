"""
Subscription router for subscription plans and user subscriptions.
"""
from fastapi import APIRouter, HTTPException, status
from app.models.subscription_plan import SubscriptionPlan
from app.models.user_subscription import UserSubscription
from app.models.user import User
from app.models.mess import Mess
from app.models.meal_pass import MealPass
from beanie import PydanticObjectId
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


class CreatePlanRequest(BaseModel):
    planName: str
    duration: Literal['Daily', 'Weekly', 'Monthly']
    mealType: Literal['Veg', 'Non-Veg', 'Jain']
    price: float
    description: str
    userId: str


class UpdatePlanRequest(BaseModel):
    planName: Optional[str] = None
    duration: Optional[Literal['Daily', 'Weekly', 'Monthly']] = None
    mealType: Optional[Literal['Veg', 'Non-Veg', 'Jain']] = None
    price: Optional[float] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    userId: str


class SubscribeToPlanRequest(BaseModel):
    planId: str
    userId: str


class UpdateSubscriptionRequest(BaseModel):
    status: Optional[Literal['Active', 'Expired', 'Cancelled', 'Pending']] = None
    messId: Optional[str] = None


# Create subscription plan (Mess Owner)
@router.post("/plans")
async def create_plan(payload: CreatePlanRequest):
    """Create a new subscription plan."""
    try:
        user = await User.get(PydanticObjectId(payload.userId))
        if not user or not user.is_mess_owner():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only mess owners can create subscription plans"
            )
        
        new_plan = SubscriptionPlan(
            messId=PydanticObjectId(payload.userId),
            planName=payload.planName,
            duration=payload.duration,
            mealType=payload.mealType,
            price=payload.price,
            description=payload.description
        )
        
        await new_plan.save()
        return new_plan.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create plan error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Update subscription plan
@router.put("/plans/{plan_id}")
async def update_plan(plan_id: str, payload: UpdatePlanRequest):
    """Update a subscription plan."""
    try:
        plan = await SubscriptionPlan.get(PydanticObjectId(plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        user = await User.get(PydanticObjectId(payload.userId))
        if not user or not user.is_mess_owner() or str(plan.messId) != payload.userId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own plans"
            )
        
        # Update fields
        update_data = payload.dict(exclude={'userId'}, exclude_none=True)
        for key, value in update_data.items():
            setattr(plan, key, value)
        
        plan.updated_at = datetime.utcnow()
        await plan.save()
        
        return plan.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update plan error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Delete subscription plan
@router.delete("/plans/{plan_id}/{mess_id}")
async def delete_plan(plan_id: str, mess_id: str):
    """Delete a subscription plan and update related subscriptions."""
    try:
        plan = await SubscriptionPlan.get(PydanticObjectId(plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        if str(plan.messId) != mess_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own plans"
            )
        
        # Update all subscriptions for this plan
        subscriptions = await UserSubscription.find(
            UserSubscription.planId == plan.id
        ).to_list()
        
        for sub in subscriptions:
            sub.status = 'Plan Removed'
            sub.endDate = datetime.utcnow()
            sub.cancellationReason = 'Plan deleted by mess owner'
            await sub.save()
        
        await plan.delete()
        
        return {
            "success": True,
            "message": "Plan deleted successfully and related subscriptions updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete plan error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Get all plans for a mess
@router.get("/mess/{mess_id}/plans")
async def get_mess_plans(mess_id: str):
    """Get all active plans for a specific mess."""
    try:
        plans = await SubscriptionPlan.find(
            SubscriptionPlan.messId == PydanticObjectId(mess_id),
            SubscriptionPlan.isActive == True
        ).to_list()
        
        return [plan.to_dict() for plan in plans]
        
    except Exception as e:
        logger.error(f"Get mess plans error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Get all active plans with mess details
@router.get("/plans")
async def get_all_plans():
    """Get all active subscription plans with mess details."""
    try:
        plans = await SubscriptionPlan.find(
            SubscriptionPlan.isActive == True
        ).sort("-created_at").to_list()
        
        plans_with_mess = []
        for plan in plans:
            plan_dict = plan.to_dict()
            mess = await Mess.find_one(Mess.Owner_ID == plan.messId)
            if mess:
                plan_dict['messDetails'] = mess.to_dict()
            plans_with_mess.append(plan_dict)
        
        return plans_with_mess
        
    except Exception as e:
        logger.error(f"Get all plans error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Subscribe to a plan
@router.post("/subscribe")
async def subscribe_to_plan(payload: SubscribeToPlanRequest):
    """Subscribe a user to a plan."""
    try:
        user = await User.get(PydanticObjectId(payload.userId))
        if not user or not user.is_regular_user():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only users can subscribe to plans"
            )
        
        plan = await SubscriptionPlan.get(PydanticObjectId(payload.planId))
        if not plan or not plan.isActive:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found or inactive"
            )
        
        # Check if user has already subscribed to this plan
        existing = await UserSubscription.find_one(
            UserSubscription.userId == user.id,
            UserSubscription.planId == plan.id
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already subscribed to this plan before. Each plan can only be subscribed once."
            )
        
        # Calculate dates
        start_date = datetime.utcnow()
        end_date = start_date
        
        if plan.duration == 'Daily':
            end_date = start_date + timedelta(days=1)
        elif plan.duration == 'Weekly':
            end_date = start_date + timedelta(days=7)
        elif plan.duration == 'Monthly':
            end_date = start_date + timedelta(days=30)
        
        # Create subscription
        subscription = UserSubscription(
            userId=user.id,
            planId=plan.id,
            startDate=start_date,
            endDate=end_date,
            status='Pending',
            paymentStatus='Pending'
        )
        
        await subscription.save()
        
        # Generate meal pass
        try:
            qr_data = {
                "userId": str(user.id),
                "subscriptionId": str(subscription.id),
                "planId": str(plan.id),
                "messId": str(plan.messId),
                "mealType": plan.mealType,
                "timestamp": int(datetime.utcnow().timestamp())
            }
            
            qr_string = hashlib.sha256(
                json.dumps(qr_data, sort_keys=True).encode()
            ).hexdigest()
            
            meal_pass = MealPass(
                userId=user.id,
                subscriptionId=subscription.id,
                messId=plan.messId,
                qrCode=qr_string,
                validFrom=start_date,
                validTill=end_date
            )
            
            await meal_pass.save()
            
        except Exception as e:
            logger.error(f"Failed to generate meal pass: {str(e)}")
        
        return subscription.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscribe to plan error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Get user subscriptions
@router.get("/user/{user_id}")
async def get_user_subscriptions(user_id: str):
    """Get all subscriptions for a user."""
    try:
        user = await User.get(PydanticObjectId(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        subscriptions = await UserSubscription.find(
            UserSubscription.userId == user.id
        ).sort("-created_at").to_list()
        
        result = []
        for sub in subscriptions:
            sub_dict = sub.to_dict()
            
            # Get plan details
            plan = await SubscriptionPlan.get(sub.planId)
            if plan:
                plan_dict = plan.to_dict()
                
                # Get mess details
                mess = await Mess.find_one(Mess.Owner_ID == plan.messId)
                if mess:
                    plan_dict['messDetails'] = mess.to_dict()
                
                sub_dict['planId'] = plan_dict
            
            result.append(sub_dict)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user subscriptions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Get mess subscribers
@router.get("/mess/{mess_id}/subscribers")
async def get_mess_subscribers(mess_id: str):
    """Get all subscribers for a mess."""
    try:
        # Get all plans for this mess
        plans = await SubscriptionPlan.find(
            SubscriptionPlan.messId == PydanticObjectId(mess_id)
        ).to_list()
        
        plan_ids = [plan.id for plan in plans]
        
        # Get all subscriptions for these plans
        subscriptions = await UserSubscription.find(
            {"planId": {"$in": plan_ids}}
        ).sort("-created_at").to_list()
        
        result = []
        for sub in subscriptions:
            sub_dict = sub.to_dict()
            
            # Get user details
            user = await User.get(sub.userId)
            if user:
                sub_dict['userId'] = {
                    "_id": str(user.id),
                    "username": user.username,
                    "email": user.email
                }
            
            # Get plan details
            plan = await SubscriptionPlan.get(sub.planId)
            if plan:
                sub_dict['planId'] = plan.to_dict()
            
            result.append(sub_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Get mess subscribers error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Activate/Update subscription
@router.put("/{subscription_id}/activate")
async def activate_subscription(subscription_id: str, payload: UpdateSubscriptionRequest):
    """Activate or update a subscription status."""
    try:
        subscription = await UserSubscription.get(PydanticObjectId(subscription_id))
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        plan = await SubscriptionPlan.get(subscription.planId)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Check authorization if messId provided
        if payload.messId and str(plan.messId) != payload.messId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this subscription"
            )
        
        # Update status
        if payload.status:
            subscription.status = payload.status
            
            if payload.status in ['Cancelled', 'Expired']:
                subscription.endDate = datetime.utcnow()
            elif payload.status == 'Active':
                subscription.startDate = datetime.utcnow()
                end_date = subscription.startDate
                
                if plan.duration == 'Daily':
                    end_date = subscription.startDate + timedelta(days=1)
                elif plan.duration == 'Weekly':
                    end_date = subscription.startDate + timedelta(days=7)
                elif plan.duration == 'Monthly':
                    end_date = subscription.startDate + timedelta(days=30)
                
                subscription.endDate = end_date
        
        subscription.updated_at = datetime.utcnow()
        await subscription.save()
        
        return subscription.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate subscription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
