"""
audit_service.py - Administrative Audit Logging Service
Records audit trails for all sensitive actions and queries historical logs.
"""

from typing import List, Optional, Dict, Any
from supabase import Client


class AuditService:
    def __init__(self, client: Client):
        self.client = client

    def log_action(
        self,
        admin_auth_user_id: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Records an audit event into public.admin_audit_logs.
        Fails safely without breaking the primary flow if an error occurs.
        """
        payload = {
            "admin_auth_user_id": admin_auth_user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_values": old_values,
            "new_values": new_values,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        try:
            self.client.table("admin_audit_logs").insert(payload).execute()
            return True
        except Exception as e:
            # Audit logging failure should not crash, but print warning
            print(f"[AuditService Error] Failed to log action '{action}': {str(e)}")
            return False

    def list_logs(
        self,
        limit: int = 100,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent audit logs in descending order."""
        try:
            query = self.client.table("admin_audit_logs").select("*")
            if action_filter:
                query = query.eq("action", action_filter)
            if entity_type_filter:
                query = query.eq("entity_type", entity_type_filter)
            res = query.order("created_at", desc=True).limit(limit).execute()
            return res.data or []
        except Exception as e:
            raise RuntimeError(f"Failed to query audit logs: {str(e)}")
