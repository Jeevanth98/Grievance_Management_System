"""
test_status_transitions.py - Unit tests for Grievance Status Transitions & Timestamps
"""

import pytest
from admin_portal.grievance_service import GrievanceService
from admin_portal.constants import (
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_ASSIGNED,
    STATUS_IN_PROGRESS,
    STATUS_RESOLVED,
    STATUS_CLOSED,
    STATUS_REOPENED,
    STATUS_REJECTED,
)


def test_valid_status_transition(mock_supabase_client, mock_admin_profiles):
    """Verifies that an allowed status transition succeeds and records history."""
    acting_admin = mock_admin_profiles["admin"]
    service = GrievanceService(mock_supabase_client)

    # g-101 is currently 'submitted'. Transition to 'under_review' is valid.
    success, err = service.update_status(
        grievance_id="g-101-uuid",
        new_status=STATUS_UNDER_REVIEW,
        change_reason="Starting verification",
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
    )

    assert success is True
    assert err is None

    store = mock_supabase_client._store
    g101 = next(g for g in store["grievances"] if g["id"] == "g-101-uuid")
    assert g101["status"] == STATUS_UNDER_REVIEW

    # Check status history record
    histories = store["grievance_status_history"]
    assert len(histories) >= 1
    assert histories[-1]["new_status"] == STATUS_UNDER_REVIEW
    reason_val = histories[-1].get("remarks") or histories[-1].get("change_reason")
    assert reason_val == "Starting verification"


def test_invalid_status_transition_rejected(mock_supabase_client, mock_admin_profiles):
    """Verifies that an unauthorized/illegal status transition is rejected."""
    acting_admin = mock_admin_profiles["admin"]
    service = GrievanceService(mock_supabase_client)

    # g-101 is 'submitted'. Jumping directly to 'closed' is illegal.
    success, err = service.update_status(
        grievance_id="g-101-uuid",
        new_status=STATUS_CLOSED,
        change_reason="Attempting direct closure",
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
    )

    assert success is False
    assert "Invalid status transition" in err


def test_resolution_sets_resolved_at(mock_supabase_client, mock_admin_profiles):
    """Verifies that transitioning to 'resolved' sets the resolved_at timestamp."""
    acting_admin = mock_admin_profiles["admin"]
    service = GrievanceService(mock_supabase_client)

    # g-102 is currently 'assigned'. Transitioning to 'resolved' is allowed.
    success, err = service.update_status(
        grievance_id="g-102-uuid",
        new_status=STATUS_RESOLVED,
        change_reason="Lab marks corrected in ERP",
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
    )

    assert success is True
    store = mock_supabase_client._store
    g102 = next(g for g in store["grievances"] if g["id"] == "g-102-uuid")
    assert g102["status"] == STATUS_RESOLVED
    assert g102.get("resolved_at") is not None
