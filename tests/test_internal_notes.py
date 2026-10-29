"""
test_internal_notes.py - Unit tests for Private Internal Admin Notes
"""

import pytest
from admin_portal.note_service import InternalNoteService


def test_add_internal_note_success(mock_supabase_client, mock_admin_profiles):
    """Verifies that an authorized admin can add an internal review note."""
    acting_admin = mock_admin_profiles["admin"]
    service = InternalNoteService(mock_supabase_client)

    success, err = service.add_note(
        grievance_id="g-101-uuid",
        note_text="Electrician contacted. Spares expected by tomorrow.",
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
    )

    assert success is True
    assert err is None

    store = mock_supabase_client._store
    notes = store["grievance_internal_notes"]
    assert len(notes) == 1
    assert notes[0]["author_admin_id"] == acting_admin["id"]  # Must use admin_profiles.id
    assert "Electrician" in notes[0]["note"]


def test_blank_internal_note_rejected(mock_supabase_client, mock_admin_profiles):
    """Verifies that empty internal notes are rejected."""
    acting_admin = mock_admin_profiles["admin"]
    service = InternalNoteService(mock_supabase_client)

    success, err = service.add_note(
        grievance_id="g-101-uuid",
        note_text="     ",
        acting_admin_profile=acting_admin,
        acting_auth_user_id=acting_admin["auth_user_id"],
    )

    assert success is False
    assert "empty" in err.lower()
