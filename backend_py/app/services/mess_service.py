"""
Mess service class.
Demonstrates OOP business logic for mess operations.
"""
from app.models.mess import Mess
from app.models.user import User
from app.exceptions import NotFoundError, AuthorizationError
from typing import List
from beanie import PydanticObjectId
from datetime import datetime


class MessService:
    """
    Mess management service.
    
    OOP Principles:
    - Single Responsibility: Handles mess-related operations
    - Encapsulation: Business rules for mess creation/updates
    """
    
    async def create_mess_for_owner(self, owner_id: str, owner: User) -> Mess:
        """
        Create a mess for a mess owner during signup.
        
        Args:
            owner_id: Owner's user ID
            owner: User object (must be Mess Owner role)
            
        Returns:
            Created Mess object
            
        Raises:
            AuthorizationError: If user is not a Mess Owner
        """
        if not owner.is_mess_owner():
            raise AuthorizationError("Only Mess Owners can create a mess")
        
        # Generate default mess name
        random_suffix = int(datetime.utcnow().timestamp() % 1000)
        mess_name = f"Mess{random_suffix}"
        
        # Create mess document
        mess = Mess(
            Mess_ID=int(datetime.utcnow().timestamp() * 1000),
            Mess_Name=mess_name,
            Mobile_No="",
            Capacity=0,
            Address="",
            Owner_ID=PydanticObjectId(owner_id),
            Description="",
            UserID=owner.UserID,
            Image="http://res.cloudinary.com/dq3ro4o3c/image/upload/v1734445757/gngcgm82wwo5t0desu0w.jpg",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await mess.insert()
        return mess
    
    async def get_mess_by_id(self, mess_id: str) -> Mess:
        """
        Retrieve mess by database ID.
        
        Args:
            mess_id: Mess database ID
            
        Returns:
            Mess object
            
        Raises:
            NotFoundError: If mess doesn't exist
        """
        try:
            mess = await Mess.get(PydanticObjectId(mess_id))
        except Exception:
            mess = None
        
        if not mess:
            raise NotFoundError("Mess")
        
        return mess
    
    async def get_mess_by_owner(self, owner_id: str) -> Mess:
        """
        Retrieve mess by owner ID.
        
        Args:
            owner_id: Owner's user ID
            
        Returns:
            Mess object or None
        """
        return await Mess.find_one({"Owner_ID": PydanticObjectId(owner_id)})
    
    async def get_all_messes(self, limit: int = 100) -> List[Mess]:
        """
        Retrieve all messes.
        
        Args:
            limit: Maximum number of messes to return
            
        Returns:
            List of Mess objects
        """
        messes = await Mess.find_all().limit(limit).to_list()
        return messes
    
    async def update_mess(
        self,
        mess_id: str,
        owner_id: str,
        **update_fields
    ) -> Mess:
        """
        Update mess details.
        
        Args:
            mess_id: Mess database ID
            owner_id: Owner's user ID (for authorization)
            **update_fields: Fields to update
            
        Returns:
            Updated Mess object
            
        Raises:
            NotFoundError: If mess doesn't exist
            AuthorizationError: If user is not the owner
        """
        mess = await self.get_mess_by_id(mess_id)
        
        # Authorization check
        if str(mess.Owner_ID) != owner_id:
            raise AuthorizationError("You can only update your own mess")
        
        # Update allowed fields
        allowed_fields = [
            "Mess_Name", "Mobile_No", "Capacity",
            "Address", "Description", "Image"
        ]
        
        for field, value in update_fields.items():
            if field in allowed_fields and value is not None:
                setattr(mess, field, value)
        
        mess.updated_at = datetime.utcnow()
        await mess.save()
        
        return mess
    
    async def add_rating_to_mess(
        self,
        mess_id: str,
        rating: int,
        user_id: str
    ) -> Mess:
        """
        Add a rating to a mess.
        
        Args:
            mess_id: Mess database ID
            rating: Rating value (1-5)
            user_id: User ID submitting rating
            
        Returns:
            Updated Mess object
            
        Raises:
            NotFoundError: If mess doesn't exist
            ValidationError: If user already rated or invalid rating
        """
        mess = await self.get_mess_by_id(mess_id)
        
        # Validate rating
        if not (1 <= rating <= 5):
            from app.exceptions import ValidationError
            raise ValidationError("Rating must be between 1 and 5")
        
        # Add rating
        user_obj_id = PydanticObjectId(user_id)
        success = mess.add_rating(rating, user_obj_id)
        
        if not success:
            from app.exceptions import ValidationError
            raise ValidationError("You have already rated this mess")
        
        await mess.save()
        return mess
    
    async def delete_mess(self, mess_id: str, owner_id: str) -> bool:
        """
        Delete a mess.
        
        Args:
            mess_id: Mess database ID
            owner_id: Owner's user ID (for authorization)
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If mess doesn't exist
            AuthorizationError: If user is not the owner
        """
        mess = await self.get_mess_by_id(mess_id)
        
        # Authorization check
        if str(mess.Owner_ID) != owner_id:
            raise AuthorizationError("You can only delete your own mess")
        
        await mess.delete()
        return True
