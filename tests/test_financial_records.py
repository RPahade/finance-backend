"""
Tests for financial records endpoints.
"""

import pytest
from datetime import date
from tests.conftest import auth_header


class TestCreateRecord:
    """Tests for POST /api/v1/records/"""

    def test_admin_can_create_record(self, client, admin_token):
        """Admin should be able to create a financial record."""
        response = client.post(
            "/api/v1/records/",
            json={
                "amount": "2500.50",
                "type": "income",
                "category": "Freelance",
                "date": str(date.today()),
                "description": "Client project payment",
            },
            headers=auth_header(admin_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["category"] == "Freelance"

    def test_viewer_cannot_create_record(self, client, viewer_token):
        """Viewer should be forbidden from creating records."""
        response = client.post(
            "/api/v1/records/",
            json={
                "amount": "100.00",
                "type": "expense",
                "category": "Food",
                "date": str(date.today()),
            },
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 403

    def test_analyst_cannot_create_record(self, client, analyst_token):
        """Analyst should be forbidden from creating records."""
        response = client.post(
            "/api/v1/records/",
            json={
                "amount": "100.00",
                "type": "expense",
                "category": "Food",
                "date": str(date.today()),
            },
            headers=auth_header(analyst_token),
        )
        assert response.status_code == 403

    def test_create_record_invalid_amount(self, client, admin_token):
        """Should reject records with negative or zero amount."""
        response = client.post(
            "/api/v1/records/",
            json={
                "amount": "-50.00",
                "type": "expense",
                "category": "Food",
                "date": str(date.today()),
            },
            headers=auth_header(admin_token),
        )
        assert response.status_code == 422

    def test_create_record_missing_fields(self, client, admin_token):
        """Should reject records with missing required fields."""
        response = client.post(
            "/api/v1/records/",
            json={"amount": "100.00"},
            headers=auth_header(admin_token),
        )
        assert response.status_code == 422


class TestListRecords:
    """Tests for GET /api/v1/records/"""

    def test_viewer_can_list_records(self, client, viewer_token, sample_record):
        """Viewer should be able to list financial records."""
        response = client.get(
            "/api/v1/records/",
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data

    def test_filter_by_type(self, client, admin_token, sample_record):
        """Should filter records by type."""
        response = client.get(
            "/api/v1/records/?type=income",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        for record in response.json()["data"]:
            assert record["type"] == "income"

    def test_filter_by_category(self, client, admin_token, sample_record):
        """Should filter records by category."""
        response = client.get(
            "/api/v1/records/?category=Salary",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200


class TestUpdateRecord:
    """Tests for PUT /api/v1/records/{record_id}"""

    def test_admin_can_update_record(self, client, admin_token, sample_record):
        """Admin should be able to update a record."""
        response = client.put(
            f"/api/v1/records/{sample_record.id}",
            json={"amount": "2000.00", "category": "Bonus"},
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["data"]["category"] == "Bonus"

    def test_viewer_cannot_update_record(self, client, viewer_token, sample_record):
        """Viewer should be forbidden from updating records."""
        response = client.put(
            f"/api/v1/records/{sample_record.id}",
            json={"amount": "2000.00"},
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 403


class TestDeleteRecord:
    """Tests for DELETE /api/v1/records/{record_id}"""

    def test_admin_can_delete_record(self, client, admin_token, sample_record):
        """Admin should be able to soft-delete a record."""
        response = client.delete(
            f"/api/v1/records/{sample_record.id}",
            headers=auth_header(admin_token),
        )
        assert response.status_code == 200

        # Record should no longer be accessible
        get_response = client.get(
            f"/api/v1/records/{sample_record.id}",
            headers=auth_header(admin_token),
        )
        assert get_response.status_code == 404

    def test_viewer_cannot_delete_record(self, client, viewer_token, sample_record):
        """Viewer should be forbidden from deleting records."""
        response = client.delete(
            f"/api/v1/records/{sample_record.id}",
            headers=auth_header(viewer_token),
        )
        assert response.status_code == 403
