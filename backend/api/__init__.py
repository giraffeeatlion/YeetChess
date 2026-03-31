"""API package - export routers"""

from .auth import router as auth_router
from .games import router as games_router

__all__ = ["auth_router", "games_router"]
