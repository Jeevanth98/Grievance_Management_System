"""
note_service.py - Internal Admin Notes Service
Manages confidential administrative review notes.
Guaranteed to be isolated from student portals and student-facing notifications.
Uses admin_profiles.id for author_admin_id.
"""

from typing import List, Optional, Dict, Any, Tuple
from supabase import Client
from admin_portal.constants import PERMISSIONS
from admin_portal.audit_service import AuditService


class InternalNoteService:
    def __init__(self, client: Client):
        self.client = client
        self.audit_service = AuditService(client)

    def list_notes_for_grievance(
        self,
        grievance_id: str,
        acting_admin_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Retrieves internal notes for a grievance in chronological order.
        Joins author profile for display.
        """
        acting_role = acting_admin_profile.get("role", "")
        if not PERMISSIONS.get(acting_role, {}).get("can_add_internal_notes", False):
            raise PermissionError("Your role is not authorized to view internal notes.")

        try:
            res = (
                self.client.table("grievance_internal_notes")
                .select("id, grievance_id, author_admin_id, note, created_at")
                .eq("grievance_id", grievance_id)
                .order("created_at", desc=False)
                .execute()
            )
            notes = res.data or []

            # Populate author details
            for note in notes:
                author_id = note.get("author_admin_id")
                if author_id:
                    adm_res = (
                        self.client.table("admin_profiles")
                        .select("full_name, role, department")
                        .eq("id", author_id)
                        .limit(1)
                        .execute()
                    )
                    note["author"] = adm_res.data[0] if adm_res.data else None

            return notes

        except Exception as e:
            raise RuntimeError(f"Failed to fetch internal notes: {str(e)}")

    def add_note(
        self,
        grievance_id: str,
        note_text: str,
        acting_admin_profile: Dict[str, Any],
        acting_auth_user_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Adds a private internal note.
        author_admin_id references public.admin_profiles.id.
        """
        text = note_text.strip()
        if not text:
            return False, "Internal note cannot be empty."

        acting_role = acting_admin_profile.get("role", "")
        if not PERMISSIONS.get(acting_role, {}).get("can_add_internal_notes", False):
            return False, f"Permission Denied: Role '{acting_role}' cannot create internal notes."

        admin_profile_id = acting_admin_profile.get("id")
        if not admin_profile_id:
            return False, "Active administrator profile ID is missing."

        try:
            payload = {
                "grievance_id": grievance_id,
                "author_admin_id": admin_profile_id,
                "note": text,
            }
            res = self.client.table("grievance_internal_notes").insert(payload).execute()
            note_id = res.data[0].get("id") if res.data else None

            # Log audit event
            self.audit_service.log_action(
                admin_auth_user_id=acting_auth_user_id,
                action="grievance.internal_note_added",
                entity_type="grievance_internal_note",
                entity_id=note_id,
                details=f"Internal note added to grievance {grievance_id} by {acting_admin_profile.get('full_name')}",
            )

            return True, None

        except Exception as e:
            return False, f"Failed to record internal note: {str(e)}"
