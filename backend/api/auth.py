"""
Authentication Endpoints
/auth/register, /auth/login, /auth/refresh, /auth/me
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..config import settings
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from ..utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    extract_user_id_from_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    
    Returns access and refresh tokens on success.
    """
    # Check if user already exists
    stmt = select(User).where(User.username == user_create.username)
    existing_user = await db.scalar(stmt)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    stmt = select(User).where(User.email == user_create.email)
    existing_email = await db.scalar(stmt)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        username=user_create.username,
        email=user_create.email,
        password_hash=hash_password(user_create.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(
        user.id,
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.jwt_access_expiration_minutes
    )
    refresh_token = create_refresh_token(
        user.id,
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.jwt_refresh_expiration_days
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with username and password.
    
    Returns access and refresh tokens on success.
    """
    # Find user by username
    stmt = select(User).where(User.username == user_login.username)
    user = await db.scalar(stmt)
    
    if not user or not verify_password(user_login.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Generate tokens
    access_token = create_access_token(
        user.id,
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.jwt_access_expiration_minutes
    )
    refresh_token = create_refresh_token(
        user.id,
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.jwt_refresh_expiration_days
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=dict)
async def refresh(refresh_token: str):
    """
    Exchange a refresh token for a new access token.
    """
    payload = verify_token(
        refresh_token,
        settings.jwt_secret_key,
        settings.jwt_algorithm
    )
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = extract_user_id_from_token(
        refresh_token,
        settings.jwt_secret_key,
        settings.jwt_algorithm
    )
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Create new access token
    access_token = create_access_token(
        user_id,
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.jwt_access_expiration_minutes
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user.
    
    Authorization header: "Bearer {access_token}"
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    payload = verify_token(
        token,
        settings.jwt_secret_key,
        settings.jwt_algorithm
    )
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = extract_user_id_from_token(
        token,
        settings.jwt_secret_key,
        settings.jwt_algorithm
    )
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    stmt = select(User).where(User.id == user_id)
    user = await db.scalar(stmt)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)
