"""
Custom exception classes.
Demonstrates inheritance and exception handling OOP principles.
"""
from fastapi import HTTPException, status


class MessBuddyException(Exception):
    """
    Base exception for application errors.
    
    OOP Principle: Inheritance
    - All custom exceptions inherit from this base
    """
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(MessBuddyException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(MessBuddyException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationError(MessBuddyException):
    """Raised for input validation errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class NotFoundError(MessBuddyException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status.HTTP_404_NOT_FOUND)


class DuplicateError(MessBuddyException):
    """Raised when attempting to create duplicate resource."""
    
    def __init__(self, field: str, value: str):
        super().__init__(
            f"{field} '{value}' already exists",
            status.HTTP_400_BAD_REQUEST
        )


def convert_exception_to_http(exc: MessBuddyException) -> HTTPException:
    """
    Convert custom exception to FastAPI HTTPException.
    
    Args:
        exc: Custom exception instance
        
    Returns:
        HTTPException with appropriate status code and detail
    """
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message
    )
