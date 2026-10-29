"""
test_auth.py - Unit tests for Authentication & Active Admin Verification
"""

import pytest
from unittest.mock import MagicMock, patch
from admin_portal.auth_service import AuthService


def test_admin_sign_in_success(mock_supabase_client, mock_admin_profiles):
    """Verifies that an active admin can authenticate successfully."""
    auth_service = AuthService(mock_supabase_client)

    # Mock successful Supabase Auth response
    mock_auth_user = MagicMock()
    mock_auth_user.id = "auth-001-uuid"
    mock_session = MagicMock()
    mock_session.access_token = "mock-jwt-token"

    mock_auth_response = MagicMock()
    mock_auth_response.user = mock_auth_user
    mock_auth_response.session = mock_session

    mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

    success, err, profile, token = auth_service.sign_in("sarah@university.edu", "correct_password")

    assert success is True
    assert err is None
    assert profile is not None
    assert profile["email"] == "sarah@university.edu"
    assert profile["role"] == "super_admin"
    assert token == "mock-jwt-token"


def test_student_rejected_from_admin_portal(mock_supabase_client):
    """Verifies that a student account (no record in admin_profiles) is rejected."""
    auth_service = AuthService(mock_supabase_client)

    # Student auth user
    mock_auth_user = MagicMock()
    mock_auth_user.id = "student-auth-user-id-not-in-admin-table"
    mock_session = MagicMock()
    mock_session.access_token = "student-jwt-token"

    mock_auth_response = MagicMock()
    mock_auth_response.user = mock_auth_user
    mock_auth_response.session = mock_session

    mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

    success, err, profile, token = auth_service.sign_in("student@university.edu", "student_password")

    assert success is False
    assert profile is None
    assert "Access Denied" in err
    assert "Student Portal" in err


def test_inactive_admin_rejected(mock_supabase_client):
    """Verifies that an inactive admin account cannot sign in."""
    auth_service = AuthService(mock_supabase_client)

    mock_auth_user = MagicMock()
    mock_auth_user.id = "auth-004-uuid"  # ian inactive
    mock_session = MagicMock()
    mock_session.access_token = "inactive-jwt"

    mock_auth_response = MagicMock()
    mock_auth_response.user = mock_auth_user
    mock_auth_response.session = mock_session

    mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

    success, err, profile, token = auth_service.sign_in("ian@university.edu", "password123")

    assert success is False
    assert profile is None
    assert "Account Suspended" in err or "deactivated" in err.lower()


def test_blank_credentials_rejected(mock_supabase_client):
    """Verifies that blank email or password are rejected immediately."""
    auth_service = AuthService(mock_supabase_client)
    success, err, profile, token = auth_service.sign_in("   ", "")
    assert success is False
    assert "required" in err.lower()
