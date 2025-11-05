"""
Database connection and initialization.
Demonstrates singleton pattern and dependency management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from typing import List
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection manager (Singleton pattern).
    
    OOP Principles:
    - Encapsulation: Hides connection details
    - Singleton: One database connection per application
    """
    
    _client: AsyncIOMotorClient = None
    _database = None
    
    @classmethod
    async def connect(cls, document_models: List):
        """
        Initialize database connection and Beanie ODM.
        
        Args:
            document_models: List of Beanie Document classes to register
        """
        try:
            cls._client = AsyncIOMotorClient(settings.MONGO_URI)
            cls._database = cls._client.get_default_database()
            
            # Initialize Beanie with document models
            await init_beanie(
                database=cls._database,
                document_models=document_models
            )
            
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Close database connection."""
        if cls._client:
            cls._client.close()
            logger.info("Database connection closed")
    
    @classmethod
    def get_database(cls):
        """Get database instance."""
        return cls._database


async def init_db():
    """
    Initialize database with all document models.
    Called on application startup.
    """
    # Import models here to avoid circular imports
    from app.models.user import User
    from app.models.mess import Mess
    from app.models.menu import Menu
    from app.models.feedback import Feedback
    from app.models.prebooking import Prebooking
    from app.models.subscription_plan import SubscriptionPlan
    from app.models.user_subscription import UserSubscription
    from app.models.meal_pass import MealPass
    from app.models.check_in import CheckIn
    from app.models.forum_post import ForumPost
    
    await DatabaseManager.connect([
        User,
        Mess,
        Menu,
        Feedback,
        Prebooking,
        SubscriptionPlan,
        UserSubscription,
        MealPass,
        CheckIn,
        ForumPost
    ])


async def close_db():
    """Close database connection. Called on application shutdown."""
    await DatabaseManager.disconnect()
