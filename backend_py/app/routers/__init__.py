"""FastAPI routers."""
from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.mess_router import router as mess_router
from app.routers.menu_router import router as menu_router
from app.routers.feedback_router import router as feedback_router
from app.routers.prebooking_router import router as prebooking_router
from app.routers.subscription_router import router as subscription_router
from app.routers.checkin_router import router as checkin_router
from app.routers.forum_router import router as forum_router
from app.routers.mealpass_router import router as mealpass_router

__all__ = [
    "auth_router",
    "user_router",
    "mess_router",
    "menu_router",
    "feedback_router",
    "prebooking_router",
    "subscription_router",
    "checkin_router",
    "forum_router",
    "mealpass_router"
]
