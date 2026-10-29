"""
admin_repository.py - Admin Profiles Data Access Layer
Queries and updates public.admin_profiles table.
Ensures separation between admin profile ID and Supabase auth_user_id.
"""

from typing import List, Optional, Dict, Any
from supabase import Client
from admin_portal.constants import VALID_ROLES


class AdminRepository:
    def __init__(self, client: Client):
        self.client = client

    def get_by_auth_user_id(self, auth_user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch admin profile by Supabase Auth user UUID."""
        try:
            res = (
                self.client.table("admin_profiles")
                .select("*")
                .eq("auth_user_id", auth_user_id)
                .limit(1)
                .execute()
            )
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            raise RuntimeError(f"Database error while querying admin profile: {str(e)}")

    def get_by_id(self, admin_profile_id: str) -> Optional[Dict[str, Any]]:
        """Fetch admin profile by admin_profiles.id."""
        try:
            res = (
                self.client.table("admin_profiles")
                .select("*")
                .eq("id", admin_profile_id)
                .limit(1)
                .execute()
            )
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            raise RuntimeError(f"Database error while querying admin profile by ID: {str(e)}")

    def list_all(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List admin profiles with optional active-only filter."""
        try:
            query = self.client.table("admin_profiles").select("*")
            if active_only:
                query = query.eq("is_active", True)
            res = query.order("full_name").execute()
            return res.data or []
        except Exception as e:
            raise RuntimeError(f"Failed to list admin profiles: {str(e)}")

    def create_profile(
        self,
        auth_user_id: str,
        full_name: str,
        email: str,
        role: str,
        department: Optional[str] = None,
        designation: Optional[str] = None,
        created_by_auth_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert a new admin profile."""
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of {VALID_ROLES}")

        payload = {
            "auth_user_id": auth_user_id,
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "role": role,
            "department": department.strip() if department else None,
            "designation": designation.strip() if designation else None,
            "is_active": True,
            "created_by": created_by_auth_id,
        }
        try:
            res = self.client.table("admin_profiles").insert(payload).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            raise RuntimeError("Insert succeeded but returned no data.")
        except Exception as e:
            raise RuntimeError(f"Failed to create admin profile: {str(e)}")

    def update_role(self, admin_profile_id: str, new_role: str) -> Dict[str, Any]:
        """Update the role of an administrator."""
        if new_role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{new_role}'. Must be one of {VALID_ROLES}")

        try:
            res = (
                self.client.table("admin_profiles")
                .update({"role": new_role})
                .eq("id", admin_profile_id)
                .execute()
            )
            if res.data and len(res.data) > 0:
                return res.data[0]
            raise RuntimeError(f"Admin profile {admin_profile_id} not found.")
        except Exception as e:
            raise RuntimeError(f"Failed to update admin role: {str(e)}")

    def update_active_status(self, admin_profile_id: str, is_active: bool) -> Dict[str, Any]:
        """Activate or deactivate an admin account."""
        try:
            res = (
                self.client.table("admin_profiles")
                .update({"is_active": is_active})
                .eq("id", admin_profile_id)
                .execute()
            )
            if res.data and len(res.data) > 0:
                return res.data[0]
            raise RuntimeError(f"Admin profile {admin_profile_id} not found.")
        except Exception as e:
            raise RuntimeError(f"Failed to change active status: {str(e)}")
