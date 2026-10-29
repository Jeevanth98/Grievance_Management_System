"""
test_authorization.py - Unit tests for Role-Based Access Control
"""

import pytest
from admin_portal.constants import (
    ROLE_SUPER_ADMIN,
    ROLE_ADMIN,
    ROLE_REVIEWER,
    PERMISSIONS,
)
from admin_portal.assignment_service import AssignmentService
from admin_portal.grievance_service import GrievanceService
from admin_portal.comment_service import CommentService
from admin_portal.note_service import InternalNoteService


def test_reviewer_cannot_assign_grievance(mock_supabase_client, mock_admin_profiles):
    """Reviewers must not be able to assign grievances."""
    reviewer_profile = mock_admin_profiles["reviewer"]
    assign_service = AssignmentService(mock_supabase_client)

    success, err = assign_service.assign_grievance(
        grievance_id="g-101-uuid",
        target_admin_profile_id=mock_admin_profiles["admin"]["id"],
        acting_admin_profile=reviewer_profile,
        acting_auth_user_id=reviewer_profile["auth_user_id"],
        assignment_note="Attempt by reviewer",
    )

    assert success is False
    assert "Permission Denied" in err
    assert "reviewer" in err


def test_reviewer_cannot_change_priority(mock_supabase_client, mock_admin_profiles):
    """Reviewers must not be able to adjust grievance priority."""
    reviewer_profile = mock_admin_profiles["reviewer"]
    service = GrievanceService(mock_supabase_client)

    success, err = service.update_priority(
        grievance_id="g-101-uuid",
        new_priority="urgent",
        acting_admin_profile=reviewer_profile,
        acting_auth_user_id=reviewer_profile["auth_user_id"],
    )

    assert success is False
    assert "Permission Denied" in err


def test_reviewer_cannot_post_official_comment(mock_supabase_client, mock_admin_profiles):
    """Reviewers cannot post student-visible official responses."""
    reviewer_profile = mock_admin_profiles["reviewer"]
    service = CommentService(mock_supabase_client)

    success, err = service.add_official_comment(
        grievance_id="g-101-uuid",
        comment_text="Official comment",
        acting_admin_profile=reviewer_profile,
        acting_auth_user_id=reviewer_profile["auth_user_id"],
    )

    assert success is False
    assert "Permission Denied" in err


def test_super_admin_has_full_permissions():
    """Validates that super_admin permissions permit all management workflows."""
    super_perm = PERMISSIONS[ROLE_SUPER_ADMIN]
    assert super_perm["can_assign"] is True
    assert super_perm["can_change_priority"] is True
    assert super_perm["can_update_status"] is True
    assert super_perm["can_add_internal_notes"] is True
    assert super_perm["can_add_official_response"] is True
    assert super_perm["can_manage_admins"] is True
    assert super_perm["can_view_audit_logs"] is True
