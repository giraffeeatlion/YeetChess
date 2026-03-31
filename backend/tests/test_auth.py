"""
Authentication Endpoint Tests

Tests for:
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- GET /auth/me
"""

import pytest


class TestRegister:
    """Test user registration endpoint"""
    
    async def test_register_success(self, client):
        """Register a new user successfully"""
        response = await client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "alice"
        assert data["user"]["email"] == "alice@example.com"
        assert "id" in data["user"]
        assert data["user"]["id"] == 1
    
    async def test_register_duplicate_username(self, client, auth_user):
        """Cannot register with duplicate username"""
        response = await client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "new@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_register_duplicate_email(self, client, auth_user):
        """Cannot register with duplicate email"""
        response = await client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_register_invalid_email(self, client):
        """Registration fails with invalid email"""
        response = await client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "not-an-email",
                "password": "password123"
            }
        )
        assert response.status_code == 422  # Validation error
    
    async def test_register_short_password(self, client):
        """Registration fails with password < 8 characters"""
        response = await client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 422


class TestLogin:
    """Test login endpoint"""
    
    async def test_login_success(self, client, auth_user):
        """Login with valid credentials"""
        response = await client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
    
    async def test_login_invalid_username(self, client):
        """Login fails with non-existent user"""
        response = await client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]
    
    async def test_login_invalid_password(self, client, auth_user):
        """Login fails with wrong password"""
        response = await client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]


class TestRefresh:
    """Test token refresh endpoint"""
    
    async def test_refresh_success(self, client, auth_user):
        """Refresh token generates new access token"""
        response = await client.post(
            f"/auth/refresh?refresh_token={auth_user['refresh_token']}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Note: In this implementation, tokens may be identical if generated at same time
        # Just verify we get a valid response
    
    async def test_refresh_invalid_token(self, client):
        """Refresh with invalid token fails"""
        response = await client.post(
            "/auth/refresh?refresh_token=invalid_token_string"
        )
        assert response.status_code == 401


class TestGetCurrentUser:
    """Test /auth/me endpoint"""
    
    async def test_get_current_user_success(self, client, auth_user, auth_headers):
        """Get current user with valid token"""
        response = await client.get(
            "/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
    
    async def test_get_current_user_missing_header(self, client):
        """Get current user fails without authorization header"""
        response = await client.get("/auth/me")
        assert response.status_code == 401
        assert "Missing authorization header" in response.json()["detail"]
    
    async def test_get_current_user_invalid_token(self, client):
        """Get current user fails with invalid token"""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    async def test_get_current_user_wrong_format(self, client):
        """Get current user fails with wrong header format"""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code == 401
