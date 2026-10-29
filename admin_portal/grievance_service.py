"""
grievance_service.py - Status and Priority Management Service
Enforces the status transition matrix, timestamps (resolved_at, closed_at, reopened_at),
status history logging, audit trail creation, and student notifications.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from supabase import Client
from admin_portal.constants import (
    VALID_STATUSES,
    VALID_PRIORITIES,
    STATUS_TRANSITION_MATRIX,
    PERMISSIONS,
    STATUS_RESOLVED,
    STATUS_CLOSED,
    STATUS_REOPENED,
    ROLE_SUPER_ADMIN,
)
from admin_portal.audit_service import AuditService
from admin_portal.notification_service import NotificationService


class GrievanceService:
    def __init__(self, client: Client):
        self.client = client
        self.audit_service = AuditService(client)
        self.notification_service = NotificationService(client)

    def update_priority(
        self,
        grievance_id: str,
        new_priority: str,
        acting_admin_profile: Dict[str, Any],
        acting_auth_user_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Updates the priority of a grievance.
        Validates priority enum, role permissions, records audit log, updates admin_updated_at.
        """
        if new_priority not in VALID_PRIORITIES:
            return False, f"Invalid priority '{new_priority}'. Must be one of {VALID_PRIORITIES}"

        acting_role = acting_admin_profile.get("role", "")
        if not PERMISSIONS.get(acting_role, {}).get("can_change_priority", False):
            return False, f"Permission Denied: Role '{acting_role}' cannot change grievance priority."

        try:
            # Read current priority
            res = self.client.table("grievances").select("id, priority").eq("id", grievance_id).limit(1).execute()
            if not res.data or len(res.data) == 0:
                return False, f"Grievance {grievance_id} not found."

            old_priority = res.data[0].get("priority")
            if old_priority == new_priority:
                return True, None  # No change needed

            now_iso = datetime.now(timezone.utc).isoformat()
            self.client.table("grievances").update({
                "priority": new_priority,
                "admin_updated_at": now_iso,
                "updated_at": now_iso,
            }).eq("id", grievance_id).execute()

            # Record audit log
            self.audit_service.log_action(
                admin_auth_user_id=acting_auth_user_id,
                action="grievance.priority_changed",
                entity_type="grievance",
                entity_id=grievance_id,
                old_values={"priority": old_priority},
                new_values={"priority": new_priority},
                details=f"Priority updated from {old_priority} to {new_priority} by {acting_admin_profile.get('full_name')}",
            )

            return True, None

        except Exception as e:
            return False, f"Failed to update priority: {str(e)}"

    def update_status(
        self,
        grievance_id: str,
        new_status: str,
        change_reason: Optional[str],
        acting_admin_profile: Dict[str, Any],
        acting_auth_user_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Executes a controlled status transition for a grievance.
        Validates transition matrix, updates resolution/closing timestamps, inserts
        status history, writes audit trail, and dispatches student notification.
        """
        if new_status not in VALID_STATUSES:
            return False, f"Invalid status '{new_status}'. Must be one of {VALID_STATUSES}"

        acting_role = acting_admin_profile.get("role", "")
        if not PERMISSIONS.get(acting_role, {}).get("can_update_status", False):
            return False, f"Permission Denied: Role '{acting_role}' is not authorized to update status."

        try:
            # 1. Fetch existing status and details
            res = (
                self.client.table("grievances")
                .select("id, status, student_auth_user_id, resolved_at, closed_at")
                .eq("id", grievance_id)
                .limit(1)
                .execute()
            )
            if not res.data or len(res.data) == 0:
                return False, f"Grievance {grievance_id} not found."

            grievance = res.data[0]
            current_status = grievance.get("status")
            ticket_number = f"GRV-{grievance_id[:8].upper()}"
            student_auth_id = grievance.get("student_auth_user_id")

            if current_status == new_status:
                return True, None

            # 2. Check transition matrix (allow super_admin override if necessary, but enforce matrix for standard flow)
            allowed_next = STATUS_TRANSITION_MATRIX.get(current_status, set())
            if new_status not in allowed_next and acting_role != ROLE_SUPER_ADMIN:
                return (
                    False,
                    f"Invalid status transition from '{current_status}' to '{new_status}'. "
                    f"Allowed transitions: {list(allowed_next)}",
                )

            # Special check: re-opening a closed grievance
            if current_status == STATUS_CLOSED and new_status == STATUS_REOPENED:
                if not PERMISSIONS.get(acting_role, {}).get("can_reopen_closed", False):
                    return False, f"Permission Denied: Role '{acting_role}' cannot reopen closed grievances."

            now_iso = datetime.now(timezone.utc).isoformat()
            update_payload: Dict[str, Any] = {
                "status": new_status,
                "admin_updated_at": now_iso,
                "updated_at": now_iso,
            }

            # Handle status-specific timestamps
            if new_status == STATUS_RESOLVED and not grievance.get("resolved_at"):
                update_payload["resolved_at"] = now_iso
            elif new_status == STATUS_CLOSED and not grievance.get("closed_at"):
                update_payload["closed_at"] = now_iso
            elif new_status == STATUS_REOPENED:
                update_payload["reopened_at"] = now_iso

            # 3. Update grievance
            self.client.table("grievances").update(update_payload).eq("id", grievance_id).execute()

            # 4. Insert into grievance_status_history
            reason_str = change_reason.strip() if change_reason else f"Status changed to {new_status}"
            history_payload = {
                "grievance_id": grievance_id,
                "old_status": current_status,
                "new_status": new_status,
                "changed_by": acting_auth_user_id,
                "remarks": reason_str,
                "changed_at": now_iso,
            }
            try:
                self.client.table("grievance_status_history").insert(history_payload).execute()
            except Exception:
                # Fallback in case table uses alternate column names
                history_payload_alt = {
                    "grievance_id": grievance_id,
                    "old_status": current_status,
                    "new_status": new_status,
                    "changed_by_user_id": acting_auth_user_id,
                    "change_reason": reason_str,
                }
                self.client.table("grievance_status_history").insert(history_payload_alt).execute()

            # 5. Audit log
            self.audit_service.log_action(
                admin_auth_user_id=acting_auth_user_id,
                action="grievance.status_changed",
                entity_type="grievance",
                entity_id=grievance_id,
                old_values={"status": current_status},
                new_values={"status": new_status},
                details=f"Status transitioned from {current_status} to {new_status}. Reason: {change_reason or 'None'}",
            )

            # 6. Notify student
            if student_auth_id:
                formatted_status = new_status.replace("_", " ").title()
                msg = f"Your grievance (Ticket #{ticket_number}) status has been updated to: {formatted_status}."
                if change_reason:
                    msg += f" Note: {change_reason}"
                self.notification_service.notify_student(
                    student_auth_user_id=student_auth_id,
                    grievance_id=grievance_id,
                    title=f"Grievance Status: {formatted_status}",
                    message=msg,
                )

            return True, None

        except Exception as e:
            return False, f"Status update failed: {str(e)}"
