"""
test_audit_logs.py - Unit tests for Administrative Audit Trail Generation
"""

import pytest
from admin_portal.audit_service import AuditService
from admin_portal.grievance_service import GrievanceService


def test_audit_log_written_on_priority_update(mock_supabase_client, mock_admin_profiles):
    """Verifies that updating priority produces an audit log entry."""
    acting_admin = mock_admin_profiles["super_admin"]
    service = GrievanceService(mock_supabase_client)

    success, err = service.update_priority(
        grievance_id="g-101-uuid",
        new_priority="urgent",
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
    )

    assert success is True
    store = mock_supabase_client._store
    audit_logs = store["admin_audit_logs"]
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log["action"] == "grievance.priority_changed"
    assert log["old_values"]["priority"] == "high"
    assert log["new_values"]["priority"] == "urgent"


def test_list_audit_logs_with_filter(mock_supabase_client):
    """Verifies filtering audit logs by action."""
    audit_service = AuditService(mock_supabase_client)
    audit_service.log_action("auth-user", "grievance.comment_added", "grievance", "g-1")
    audit_service.log_action("auth-user", "admin.role_changed", "admin_profile", "adm-1")

    comments_logs = audit_service.list_logs(action_filter="grievance.comment_added")
    assert len(comments_logs) == 1
    assert comments_logs[0]["action"] == "grievance.comment_added"
