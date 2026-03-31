"""
Security Utilities
JWT token generation/verification and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt"""
    # bcrypt.hashpw returns bytes, decode to string
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(user_id: int, secret: str, algorithm: str, expires_in_minutes: int = 15) -> str:
    """
    Create a short-lived access token.
    
    Args:
        user_id: ID of the user
        secret: JWT secret key
        algorithm: Algorithm to use (HS256, HS512, etc.)
        expires_in_minutes: Token expiration time in minutes
    
    Returns:
        Encoded JWT token
    """
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token(user_id: int, secret: str, algorithm: str, expires_in_days: int = 7) -> str:
    """
    Create a long-lived refresh token.
    
    Args:
        user_id: ID of the user
        secret: JWT secret key
        algorithm: Algorithm to use (HS256, HS512, etc.)
        expires_in_days: Token expiration time in days
    
    Returns:
        Encoded JWT token
    """
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def verify_token(token: str, secret: str, algorithm: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        secret: JWT secret key
        algorithm: Algorithm used for encoding
    
    Returns:
        Decoded token payload, or None if validation fails
    
    Raises:
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.InvalidTokenError:
        return None


def extract_user_id_from_token(token: str, secret: str, algorithm: str) -> Optional[int]:
    """Extract user ID from a valid token"""
    payload = verify_token(token, secret, algorithm)
    if payload:
        try:
            return int(payload.get("sub"))
        except (ValueError, TypeError):
            return None
    return None
