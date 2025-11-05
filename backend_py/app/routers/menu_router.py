"""
Menu router (controller).
Demonstrates CRUD operations for menu items.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.menu import Menu
from app.models.user import User
from app.dependencies import get_current_user
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from beanie import PydanticObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/menu", tags=["Menu"])


class CreateMenuRequest(BaseModel):
    """Menu creation request."""
    Menu_Name: str = Field(..., min_length=1)
    Description: str
    Price: float = Field(..., gt=0)
    Availability: Literal["Yes", "No"] = "Yes"
    Food_Type: Literal["Veg", "Non-Veg"] = "Veg"


class UpdateMenuRequest(BaseModel):
    """Menu update request."""
    Menu_Name: Optional[str] = None
    Description: Optional[str] = None
    Price: Optional[float] = None
    Availability: Optional[Literal["Yes", "No"]] = None
    Food_Type: Optional[Literal["Veg", "Non-Veg"]] = None


@router.post("/create/{owner_id}")
async def create_menu(owner_id: str, payload: CreateMenuRequest):
    """
    Create new menu item.
    
    Args:
        owner_id: Owner's user ID
        payload: Menu item data
        
    Returns:
        Created menu item
    """
    try:
        # Verify owner exists
        user = await User.get(PydanticObjectId(owner_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create menu
        menu = Menu(
            Menu_Name=payload.Menu_Name,
            Description=payload.Description,
            Price=payload.Price,
            Owner_ID=PydanticObjectId(owner_id),
            Availability=payload.Availability,
            Food_Type=payload.Food_Type,
            Date=datetime.utcnow()
        )
        await menu.insert()
        
        return {
            "success": True,
            "message": "Menu created successfully",
            "menu": menu.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create menu error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.get("/")
async def get_all_menus():
    """
    Get all menu items.
    
    Returns:
        List of all menus
    """
    try:
        menus = await Menu.find_all().to_list()
        
        return {
            "menus": [menu.to_dict() for menu in menus]
        }
    
    except Exception as e:
        logger.error(f"Get all menus error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.get("/{owner_id}")
async def get_owner_menus(owner_id: str):
    """
    Get all menu items for a specific owner.
    
    Args:
        owner_id: Owner's user ID
        
    Returns:
        List of owner's menus
    """
    try:
        menus = await Menu.find(
            Menu.Owner_ID == PydanticObjectId(owner_id)
        ).to_list()
        
        return {
            "success": True,
            "menus": [menu.to_dict() for menu in menus]
        }
    
    except Exception as e:
        logger.error(f"Get owner menus error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.get("/search/{owner_id}")
async def search_menus(owner_id: str, query: Optional[str] = ""):
    """
    Search menu items for a specific owner.
    
    Args:
        owner_id: Owner's user ID
        query: Search query (optional)
        
    Returns:
        Filtered list of menus
    """
    try:
        if query:
            # Search by Menu_Name containing query (case-insensitive)
            menus = await Menu.find(
                Menu.Owner_ID == PydanticObjectId(owner_id),
                {"Menu_Name": {"$regex": query, "$options": "i"}}
            ).to_list()
        else:
            # Get all menus for owner
            menus = await Menu.find(
                Menu.Owner_ID == PydanticObjectId(owner_id)
            ).to_list()
        
        return {
            "success": True,
            "menus": [menu.to_dict() for menu in menus]
        }
    
    except Exception as e:
        logger.error(f"Search menus error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.put("/update/{menu_id}")
async def update_menu(menu_id: str, payload: UpdateMenuRequest):
    """
    Update menu item.
    
    Args:
        menu_id: Menu item ID
        payload: Update data
        
    Returns:
        Updated menu item
    """
    try:
        menu = await Menu.get(PydanticObjectId(menu_id))
        
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu not found"
            )
        
        # Update fields
        update_data = payload.dict(exclude_none=True)
        for key, value in update_data.items():
            setattr(menu, key, value)
        
        await menu.save()
        
        return {
            "success": True,
            "message": "Menu updated successfully",
            "menu": menu.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update menu error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.delete("/delete/{menu_id}")
async def delete_menu(menu_id: str):
    """
    Delete menu item.
    
    Args:
        menu_id: Menu item ID
        
    Returns:
        Success message
    """
    try:
        menu = await Menu.get(PydanticObjectId(menu_id))
        
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu not found"
            )
        
        await menu.delete()
        
        return {
            "success": True,
            "message": "Menu deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete menu error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
