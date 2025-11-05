"""
User service class.
Demonstrates OOP CRUD operations.
"""
from app.models.user import User
from app.exceptions import NotFoundError, DuplicateError
from typing import Optional
from beanie import PydanticObjectId


class UserService:
    """
    User management service.
    
    OOP Principles:
    - Single Responsibility: Handles user-related operations
    - Encapsulation: Database operations hidden behind methods
    """
    
    async def get_user_by_id(self, user_id: str) -> User:
        """
        Retrieve user by ID.
        
        Args:
            user_id: User's database ID
            
        Returns:
            User object
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        try:
            user = await User.get(PydanticObjectId(user_id))
        except Exception:
            user = None
        
        if not user:
            raise NotFoundError("User")
        
        return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username.
        
        Args:
            username: Username to search
            
        Returns:
            User object or None
        """
        return await User.find_one({"username": username})
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email.
        
        Args:
            email: Email to search
            
        Returns:
            User object or None
        """
        return await User.find_one({"email": email})
    
    async def update_user(
        self,
        user_id: str,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> User:
        """
        Update user profile.
        
        Args:
            user_id: User's database ID
            username: New username (optional)
            email: New email (optional)
            
        Returns:
            Updated user object
            
        Raises:
            NotFoundError: If user doesn't exist
            DuplicateError: If new username/email already taken
        """
        user = await self.get_user_by_id(user_id)
        
        # Check username uniqueness if updating
        if username and username != user.username:
            existing = await self.get_user_by_username(username)
            if existing:
                raise DuplicateError("Username", username)
            user.username = username
        
        # Check email uniqueness if updating
        if email and email != user.email:
            existing = await self.get_user_by_email(email)
            if existing:
                raise DuplicateError("Email", email)
            user.email = email
        
        # Save changes
        await user.save()
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user account.
        
        Args:
            user_id: User's database ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        user = await self.get_user_by_id(user_id)
        await user.delete()
        return True
