"""
test_assignments.py - Unit tests for Assignment & Reassignment Workflow
"""

import pytest
from admin_portal.assignment_service import AssignmentService


def test_assign_unassigned_grievance(mock_supabase_client, mock_admin_profiles):
    """Verifies assigning an unassigned grievance to an active admin."""
    acting_admin = mock_admin_profiles["super_admin"]
    target_admin = mock_admin_profiles["admin"]
    assign_service = AssignmentService(mock_supabase_client)

    success, err = assign_service.assign_grievance(
        grievance_id="g-101-uuid",
        target_admin_profile_id=target_admin["id"],
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
        assignment_note="Please inspect immediately",
    )

    assert success is True
    assert err is None

    # Check updated grievance in store
    store = mock_supabase_client._store
    grievances = store["grievances"]
    g101 = next(g for g in grievances if g["id"] == "g-101-uuid")
    assert g101["assigned_admin_id"] == target_admin["id"]
    # Status should advance from submitted to assigned
    assert g101["status"] == "assigned"

    # Check assignment record was written
    assignments = store["grievance_assignments"]
    assert len(assignments) >= 1
    assert assignments[-1]["assigned_admin_id"] == target_admin["id"]
    assert assignments[-1]["assignment_note"] == "Please inspect immediately"

    # Check audit log was written
    audit_logs = store["admin_audit_logs"]
    assert any(log["action"] == "grievance.assignment_changed" for log in audit_logs)


def test_reject_assignment_to_inactive_admin(mock_supabase_client, mock_admin_profiles):
    """Verifies that grievances cannot be assigned to inactive admin accounts."""
    acting_admin = mock_admin_profiles["super_admin"]
    inactive_target = mock_admin_profiles["inactive_admin"]
    assign_service = AssignmentService(mock_supabase_client)

    success, err = assign_service.assign_grievance(
        grievance_id="g-101-uuid",
        target_admin_profile_id=inactive_target["id"],
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
    )

    assert success is False
    assert "inactive" in err.lower()


def test_assign_to_department_records_department_in_audit_and_history(mock_supabase_client, mock_admin_profiles):
    """Verifies assigning a grievance to a department administrator records proper department info."""
    acting_admin = mock_admin_profiles["super_admin"]
    dept_admin = {
        "id": "dept-hostel-uuid",
        "auth_user_id": "auth-dept-hostel",
        "full_name": "Hostel Affairs & Student Housing",
        "email": "hostel.dept@university.edu",
        "role": "admin",
        "department": "Hostel & Residential Life",
        "designation": "Chief Warden Office",
        "is_active": True,
    }
    mock_supabase_client._store["admin_profiles"].append(dept_admin)

    assign_service = AssignmentService(mock_supabase_client)
    success, err = assign_service.assign_grievance(
        grievance_id="g-101-uuid",
        target_admin_profile_id=dept_admin["id"],
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
        assignment_note="Hostel room leak verification",
    )

    assert success is True
    assert err is None

    store = mock_supabase_client._store
    audit_logs = store["admin_audit_logs"]
    assignment_log = next(log for log in audit_logs if log["action"] == "grievance.assignment_changed")
    assert "Hostel & Residential Life" in assignment_log["details"]

    history_records = store.get("grievance_status_history", [])
    assert any("Hostel & Residential Life" in (h.get("remarks") or h.get("change_reason") or "") for h in history_records)

