"""
Pytest Configuration and Fixtures

Provides database, app, and client fixtures for testing.
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import settings
from backend.database import get_db, Base
from backend.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """
    Create in-memory SQLite database for testing.
    Automatically creates all tables and cleans up after tests.
    """
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def get_test_db():
        async with AsyncSessionLocal() as session:
            yield session
    
    # Override the app's database dependency
    app.dependency_overrides[get_db] = get_test_db
    
    yield AsyncSessionLocal
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_db):
    """
    Create AsyncClient for testing FastAPI app.
    Uses in-memory database.
    """
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture
async def auth_user(client, test_db):
    """
    Register and authenticate a test user.
    Returns (user_data, access_token, refresh_token).
    """
    # Register user
    response = await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    
    return {
        "username": "testuser",
        "email": "test@example.com",
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "user": data["user"]
    }


@pytest.fixture
async def auth_headers(auth_user):
    """Get authorization headers for authenticated requests"""
    return {
        "Authorization": f"Bearer {auth_user['access_token']}"
    }
