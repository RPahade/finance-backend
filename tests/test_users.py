"""
Tests for user management endpoints.
"""

import pytest
from tests.conftest import auth_header


class TestGetProfile:
    """Tests for GET /api/v1/users/me"""

    def test_get_own_profile(self, client, admin_token):
        """Authenticated user should be able to get their profile."""
        response = client.get("/api/v1/users/me", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "testadmin@test.com"

    def test_get_profile_unauthenticated(self, client):
        """Unauthenticated request should be rejected."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403  # No Bearer token = forbidden by HTTPBearer


class TestListUsers:
    """Tests for GET /api/v1/users/"""

    def test_admin_can_list_users(self, client, admin_token):
        """Admin should be able to list all users."""
        response = client.get("/api/v1/users/", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data

    def test_viewer_cannot_list_users(self, client, viewer_token):
        """Viewer should be forbidden from listing users."""
        response = client.get("/api/v1/users/", headers=auth_header(viewer_token))
        assert response.status_code == 403

    def test_analyst_cannot_list_users(self, client, analyst_token):
        """Analyst should be forbidden from listing users."""
        response = client.get("/api/v1/users/", headers=auth_header(analyst_token))
        assert response.status_code == 403


class TestUpdateUser:
    """Tests for PUT /api/v1/users/{user_id}"""

    def test_admin_can_update_user_role(self, client, admin_token, viewer_user):
        """Admin should be able to change a user's role."""
        response = client.put(
            f"/api/v1/users/{viewer_user.id}",
            json={"role": "analyst"},
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["data"]["role"] == "analyst"

    def test_admin_cannot_deactivate_self(self, client, admin_token, admin_user):
        """Admin should not be able to deactivate their own account."""
        response = client.put(
            f"/api/v1/users/{admin_user.id}",
            json={"is_active": False},
            headers=auth_header(admin_token),
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "SELF_DEACTIVATION"
