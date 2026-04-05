"""
Tests for authentication endpoints (register, login).
"""

import pytest
from tests.conftest import auth_header


class TestRegister:
    """Tests for POST /api/v1/auth/register"""

    def test_register_success(self, client):
        """Should register a new user with default viewer role."""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "securepass",
            "full_name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "newuser@test.com"
        assert data["data"]["role"] == "viewer"

    def test_register_duplicate_email(self, client):
        """Should reject registration with an existing email."""
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": "duplicate@test.com",
            "username": "dupuser1",
            "password": "securepass",
            "full_name": "Dup User",
        })
        # Try again with same email
        response = client.post("/api/v1/auth/register", json={
            "email": "duplicate@test.com",
            "username": "dupuser2",
            "password": "securepass",
            "full_name": "Dup User 2",
        })
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "EMAIL_EXISTS"

    def test_register_invalid_email(self, client):
        """Should reject invalid email format."""
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "username": "baduser",
            "password": "securepass",
            "full_name": "Bad User",
        })
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Should reject passwords shorter than 6 characters."""
        response = client.post("/api/v1/auth/register", json={
            "email": "shortpw@test.com",
            "username": "shortpw",
            "password": "123",
            "full_name": "Short PW",
        })
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client, admin_user):
        """Should return a JWT token on valid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "email": "testadmin@test.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["role"] == "admin"

    def test_login_wrong_password(self, client, admin_user):
        """Should reject login with wrong password."""
        response = client.post("/api/v1/auth/login", json={
            "email": "testadmin@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_nonexistent_user(self, client):
        """Should reject login for non-existent email."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@test.com",
            "password": "password123",
        })
        assert response.status_code == 401
