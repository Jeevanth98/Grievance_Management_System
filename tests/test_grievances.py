"""
test_grievances.py - Unit tests for Grievance Repository and Dashboard Metrics
"""

import pytest
from admin_portal.grievance_repository import GrievanceRepository


def test_dashboard_metrics_aggregation(mock_supabase_client):
    """Verifies live computation of dashboard metric cards."""
    repo = GrievanceRepository(mock_supabase_client)
    metrics = repo.get_dashboard_metrics()

    assert metrics["total"] == 2
    assert metrics["submitted"] == 1
    assert metrics["assigned"] == 1
    assert metrics["urgent"] == 0
    assert metrics["unassigned"] == 1


def test_list_grievances_and_filters(mock_supabase_client):
    """Verifies listing and unassigned filter."""
    repo = GrievanceRepository(mock_supabase_client)

    # All
    records, count = repo.list_grievances()
    assert len(records) == 2
    assert count == 2

    # Unassigned only
    unassigned_records, u_count = repo.list_grievances(unassigned_only=True)
    assert len(unassigned_records) == 1
    assert unassigned_records[0]["id"] == "g-101-uuid"


def test_grievance_details_retrieval(mock_supabase_client):
    """Verifies single grievance details query with related joins."""
    repo = GrievanceRepository(mock_supabase_client)
    details = repo.get_grievance_details("g-101-uuid")

    assert details is not None
    assert details["title"] == "Water heater broken in Block B"
    assert "status_history" in details
    assert "comments" in details


def test_invalid_grievance_id(mock_supabase_client):
    """Verifies that non-existent grievance ID returns None."""
    repo = GrievanceRepository(mock_supabase_client)
    details = repo.get_grievance_details("non-existent-uuid")
    assert details is None
