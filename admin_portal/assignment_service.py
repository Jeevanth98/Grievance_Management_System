"""
assignment_service.py - Grievance Assignment & Reassignment Workflow
Handles atomic assignment lifecycle, closing active assignments, updating grievances,
recording audit events, and student notifications.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from supabase import Client
from admin_portal.constants import PERMISSIONS, STATUS_SUBMITTED, STATUS_UNDER_REVIEW, STATUS_ASSIGNED
from admin_portal.admin_repository import AdminRepository
from admin_portal.audit_service import AuditService
from admin_portal.notification_service import NotificationService


class AssignmentService:
    def __init__(self, client: Client):
        self.client = client
        self.admin_repo = AdminRepository(client)
        self.audit_service = AuditService(client)
        self.notification_service = NotificationService(client)

    def assign_grievance(
        self,
        grievance_id: str,
        target_admin_profile_id: str,
        acting_admin_profile: Dict[str, Any],
        acting_auth_user_id: str,
        assignment_note: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Assigns or reassigns a grievance to a target administrator.
        Performs role checks, target validation, updates assignments table,
        updates grievance record, logs audit trail, and notifies student.
        """
        # 1. Authorization check
        acting_role = acting_admin_profile.get("role", "")
        if not PERMISSIONS.get(acting_role, {}).get("can_assign", False):
            return False, f"Permission Denied: Role '{acting_role}' is not authorized to assign grievances."

        # 2. Target Admin verification
        target_admin = self.admin_repo.get_by_id(target_admin_profile_id)
        if not target_admin:
            return False, "Target administrator profile does not exist."
        if not target_admin.get("is_active", False):
            return False, "Target administrator account is inactive and cannot receive assignments."

        try:
            # 3. Read current grievance state
            res = (
                self.client.table("grievances")
                .select("id, status, assigned_admin_id, student_auth_user_id")
                .eq("id", grievance_id)
                .limit(1)
                .execute()
            )
            if not res.data or len(res.data) == 0:
                return False, f"Grievance with ID {grievance_id} not found."

            grievance = res.data[0]
            old_assigned_admin_id = grievance.get("assigned_admin_id")
            old_status = grievance.get("status")
            student_auth_id = grievance.get("student_auth_user_id")
            ticket_number = f"GRV-{grievance_id[:8].upper()}"

            now_iso = datetime.now(timezone.utc).isoformat()

            # 4. Close any open assignment in public.grievance_assignments
            if old_assigned_admin_id:
                try:
                    self.client.table("grievance_assignments").update({
                        "unassigned_at": now_iso
                    }).eq("grievance_id", grievance_id).is_("unassigned_at", "null").execute()
                except Exception as e:
                    print(f"[Warning] Failed closing old assignment: {str(e)}")

            # 5. Insert new assignment history record
            assignment_payload = {
                "grievance_id": grievance_id,
                "assigned_admin_id": target_admin_profile_id,
                "assigned_by": acting_auth_user_id,
                "assigned_at": now_iso,
                "assignment_note": assignment_note.strip() if assignment_note else None,
            }
            self.client.table("grievance_assignments").insert(assignment_payload).execute()

            # 6. Update grievances table
            update_payload: Dict[str, Any] = {
                "assigned_admin_id": target_admin_profile_id,
                "admin_updated_at": now_iso,
                "updated_at": now_iso,
            }

            # If currently submitted or under_review, advance status to assigned
            new_status = old_status
            if old_status in [STATUS_SUBMITTED, STATUS_UNDER_REVIEW]:
                new_status = STATUS_ASSIGNED
                update_payload["status"] = STATUS_ASSIGNED

            self.client.table("grievances").update(update_payload).eq("id", grievance_id).execute()

            # 7. If status advanced, record status history
            dept_name = target_admin.get("department") or target_admin.get("full_name")
            target_desc = f"{dept_name} ({target_admin.get('designation') or target_admin.get('role')})"
            if new_status != old_status:
                try:
                    self.client.table("grievance_status_history").insert({
                        "grievance_id": grievance_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "changed_by": acting_auth_user_id,
                        "remarks": f"Assigned to {target_desc}",
                        "changed_at": now_iso,
                    }).execute()
                except Exception:
                    self.client.table("grievance_status_history").insert({
                        "grievance_id": grievance_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "changed_by_user_id": acting_auth_user_id,
                        "change_reason": f"Assigned to {target_desc}",
                    }).execute()

            # 8. Record audit log
            self.audit_service.log_action(
                admin_auth_user_id=acting_auth_user_id,
                action="grievance.assignment_changed",
                entity_type="grievance",
                entity_id=grievance_id,
                old_values={"assigned_admin_id": old_assigned_admin_id, "status": old_status},
                new_values={"assigned_admin_id": target_admin_profile_id, "status": new_status},
                details=f"Assigned to {target_desc}. Note: {assignment_note or 'None'}",
            )

            # 9. Notify student
            if student_auth_id:
                self.notification_service.notify_student(
                    student_auth_user_id=student_auth_id,
                    grievance_id=grievance_id,
                    title="Grievance Assigned to Department",
                    message=f"Your grievance (Ticket #{ticket_number}) has been assigned to {dept_name} for review and resolution.",
                )

            return True, None

        except Exception as e:
            return False, f"Assignment operation failed: {str(e)}"
