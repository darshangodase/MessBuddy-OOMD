"""
Password hashing utility.
Demonstrates encapsulation and security best practices.
"""
import bcrypt


class PasswordHasher:
    """
    Handles password hashing and verification using bcrypt.
    
    OOP Principles:
    - Encapsulation: Hashing implementation hidden
    - Single Responsibility: Only handles password operations
    """
    
    def __init__(self):
        """Initialize with salt rounds."""
        self.salt_rounds = 10
    
    def hash_password(self, plain_password: str) -> str:
        """
        Hash a plain text password using bcrypt.
        
        Args:
            plain_password: Password in plain text
            
        Returns:
            Hashed password string
        """
        # Convert password to bytes
        password_bytes = plain_password.encode('utf-8')
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self.salt_rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Password to verify
            hashed_password: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Verify
        return bcrypt.checkpw(password_bytes, hashed_bytes)
