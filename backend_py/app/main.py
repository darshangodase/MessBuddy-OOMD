"""
FastAPI application initialization and configuration.
Demonstrates OOP application structure with clean architecture.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.db import init_db, close_db
from app.routers import (
    auth_router,
    user_router,
    mess_router,
    feedback_router,
    prebooking_router,
    menu_router,
    subscription_router,
    checkin_router,
    forum_router,
    mealpass_router
)
from app.exceptions import MessBuddyException
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Application factory function.
    
    OOP Principle: Factory Pattern
    - Creates and configures FastAPI app instance
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="MessBuddy API",
        description="Object-Oriented MessBuddy Backend (Python FastAPI)",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register event handlers
    @app.on_event("startup")
    async def startup_event():
        """Initialize database on application startup."""
        logger.info("Starting application...")
        await init_db()
        logger.info("Database initialized")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Close database connection on application shutdown."""
        logger.info("Shutting down application...")
        await close_db()
        logger.info("Database connection closed")
    
    # Register exception handler for custom exceptions
    @app.exception_handler(MessBuddyException)
    async def messbuddy_exception_handler(request: Request, exc: MessBuddyException):
        """
        Global exception handler for custom exceptions.
        
        OOP Principle: Exception Handling
        - Centralizes error response formatting
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "statusCode": exc.status_code
            }
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "MessBuddy API (Python FastAPI)",
            "version": "2.0.0",
            "docs": "/docs"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "message": "MessBuddy API is running"
        }
    
    # Include routers
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(mess_router)
    app.include_router(menu_router)
    app.include_router(feedback_router)
    app.include_router(prebooking_router)
    app.include_router(subscription_router)
    app.include_router(checkin_router)
    app.include_router(forum_router)
    app.include_router(mealpass_router)
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
