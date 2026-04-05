"""
Tests for dashboard / analytics endpoints.
"""

import pytest
from tests.conftest import auth_header


class TestDashboardSummary:
    """Tests for GET /api/v1/dashboard/summary"""

    def test_analyst_can_access_summary(self, client, analyst_token, sample_record):
        """Analyst should be able to access the financial summary."""
        response = client.get(
            "/api/v1/dashboard/summary",
            headers=auth_header(analyst_token),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_balance" in data
        assert "total_records" in data

    def test_admin_can_access_summary(self, client, admin_token, sample_record):
        """Admin should be able to access the financial summary."""
        response = client.get(
            "/api/v1/dashboard/summary",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200

    def test_viewer_cannot_access_summary(self, client, viewer_token):
        """Viewer should be forbidden from accessing summaries."""
        response = client.get(
            "/api/v1/dashboard/summary",
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 403


class TestCategoryBreakdown:
    """Tests for GET /api/v1/dashboard/category-breakdown"""

    def test_analyst_can_access_breakdown(self, client, analyst_token, sample_record):
        """Analyst should get category breakdown data."""
        response = client.get(
            "/api/v1/dashboard/category-breakdown",
            headers=auth_header(analyst_token),
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)


class TestMonthlyTrends:
    """Tests for GET /api/v1/dashboard/trends"""

    def test_admin_can_access_trends(self, client, admin_token, sample_record):
        """Admin should get monthly trend data."""
        response = client.get(
            "/api/v1/dashboard/trends",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    def test_viewer_cannot_access_trends(self, client, viewer_token):
        """Viewer should be forbidden from accessing trends."""
        response = client.get(
            "/api/v1/dashboard/trends",
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 403


class TestRecentActivity:
    """Tests for GET /api/v1/dashboard/recent-activity"""

    def test_viewer_can_access_recent_activity(self, client, viewer_token, sample_record):
        """Viewer should be able to access recent activity."""
        response = client.get(
            "/api/v1/dashboard/recent-activity",
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    def test_custom_limit(self, client, admin_token, sample_record):
        """Should respect the limit parameter."""
        response = client.get(
            "/api/v1/dashboard/recent-activity?limit=5",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert len(response.json()["data"]) <= 5
