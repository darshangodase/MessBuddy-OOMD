"""
Authentication service class.
Demonstrates OOP business logic encapsulation.
"""
from app.models.user import User, LoginRole
from app.utils.password_hasher import PasswordHasher
from app.utils.token_manager import TokenManager
from app.exceptions import DuplicateError, ValidationError
from datetime import datetime
from typing import Tuple


class AuthService:
    """
    Authentication service handling signup and signin operations.
    
    OOP Principles:
    - Single Responsibility: Handles only authentication logic
    - Composition: Uses PasswordHasher and TokenManager utilities
    - Encapsulation: Business logic hidden behind clean methods
    
    Attributes:
        password_hasher: Utility for password operations
        token_manager: Utility for JWT operations
    """
    
    def __init__(self):
        """Initialize service with utility dependencies."""
        self.password_hasher = PasswordHasher()
        self.token_manager = TokenManager()
    
    async def signup(
        self,
        username: str,
        email: str,
        password: str,
        login_role: LoginRole
    ) -> Tuple[User, str]:
        """
        Register a new user account.
        
        OOP Principle: Encapsulation
        - All signup logic in one cohesive method
        
        Args:
            username: Desired username
            email: User email address
            password: Plain text password
            login_role: User role (User or Mess Owner)
            
        Returns:
            Tuple of (created_user, jwt_token)
            
        Raises:
            ValidationError: If required fields are missing
            DuplicateError: If username or email already exists
        """
        # Validation
        if not all([username, email, password, login_role]):
            raise ValidationError("All fields are required")
        
        # Additional password length check
        if len(password) > 128:
            raise ValidationError("Password is too long (max 128 characters)")
        
        # Check for existing user by email
        existing_user_by_email = await User.find_one({"email": email})
        if existing_user_by_email:
            raise DuplicateError("Email", email)
        
        # Check for existing user by username
        existing_user_by_username = await User.find_one({"username": username})
        if existing_user_by_username:
            raise DuplicateError("Username", username)
        
        # Hash password
        hashed_password = self.password_hasher.hash_password(password)
        
        # Create user document
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            Login_Role=login_role,
            UserID=int(datetime.utcnow().timestamp() * 1000),  # millisecond timestamp
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        await user.insert()
        
        # Generate JWT token
        token = self.token_manager.create_token(
            user_id=str(user.id),
            role=login_role.value
        )
        
        return user, token
    
    async def signin(
        self,
        username: str,
        password: str,
        login_role: LoginRole
    ) -> Tuple[User, str]:
        """
        Authenticate existing user.
        
        Args:
            username: Username
            password: Plain text password
            login_role: Expected user role
            
        Returns:
            Tuple of (authenticated_user, jwt_token)
            
        Raises:
            ValidationError: If credentials are invalid
        """
        # Validation
        if not all([username, password, login_role]):
            raise ValidationError("All fields are required")
        
        # Find user by username and role
        user = await User.find_one({
            "username": username,
            "Login_Role": login_role
        })
        
        if not user:
            raise ValidationError("Invalid credentials")
        
        # Verify password
        if not self.password_hasher.verify_password(password, user.password):
            raise ValidationError("Invalid credentials")
        
        # Generate JWT token
        token = self.token_manager.create_token(
            user_id=str(user.id),
            role=login_role.value
        )
        
        return user, token
    
    async def verify_token_and_get_user(self, token: str) -> User:
        """
        Verify JWT token and retrieve user.
        
        Args:
            token: JWT token string
            
        Returns:
            User object
            
        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        # Verify token
        payload = self.token_manager.verify_token(token)
        user_id = payload.get("id")
        
        # Retrieve user
        user = await User.get(user_id)
        if not user:
            raise ValidationError("User not found")
        
        return user
