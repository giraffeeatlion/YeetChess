"""
YeetChess FastAPI Backend
Real-time multiplayer chess API with WebSocket support.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import router as auth_router
from .api.games import router as games_router
from .database import init_db, close_db
from .config import settings

app = FastAPI(
    title="YeetChess API",
    description="Real-time multiplayer chess API with WebSocket support",
    version="0.2.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(games_router)


# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    try:
        await init_db()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        # Don't fail startup if DB isn't ready yet


@app.on_event("shutdown")
async def shutdown():
    """Close database connections on shutdown"""
    try:
        await close_db()
    except Exception as e:
        print(f"Warning: Error closing database: {e}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to YeetChess API", "version": "0.2.0"}


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "yeetchess-api",
        "version": "0.2.0",
    }
async def docs_redirect():
    """Redirect to Swagger UI."""
    return {"message": "API documentation available at /docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
