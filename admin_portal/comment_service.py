"""
comment_service.py - Official Grievance Comments Service
Manages official student-visible responses posted by administrators.
Enforces author role, character bounds, audit logging, and student notifications.
"""

from typing import Optional, Dict, Any, Tuple
from supabase import Client
from admin_portal.constants import PERMISSIONS
from admin_portal.audit_service import AuditService
from admin_portal.notification_service import NotificationService


class CommentService:
    def __init__(self, client: Client):
        self.client = client
        self.audit_service = AuditService(client)
        self.notification_service = NotificationService(client)

    def add_official_comment(
        self,
        grievance_id: str,
        comment_text: str,
        acting_admin_profile: Dict[str, Any],
        acting_auth_user_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Posts an official admin response to public.grievance_comments.
        """
        text = comment_text.strip()
        if not text:
            return False, "Comment cannot be blank."
        if len(text) > 4000:
            return False, "Comment exceeds the maximum allowed length of 4000 characters."

        acting_role = acting_admin_profile.get("role", "")
        if not PERMISSIONS.get(acting_role, {}).get("can_add_official_response", False):
            return False, f"Permission Denied: Role '{acting_role}' cannot post official student-visible comments."

        try:
            # 1. Verify grievance exists and retrieve student auth ID
            res = (
                self.client.table("grievances")
                .select("id, student_auth_user_id")
                .eq("id", grievance_id)
                .limit(1)
                .execute()
            )
            if not res.data or len(res.data) == 0:
                return False, f"Grievance {grievance_id} does not exist."

            grievance = res.data[0]
            student_auth_id = grievance.get("student_auth_user_id")
            ticket_number = f"GRV-{grievance_id[:8].upper()}"

            # 2. Insert comment with verified admin auth UUID and author_role 'admin'
            payload = {
                "grievance_id": grievance_id,
                "author_user_id": acting_auth_user_id,
                "author_role": "admin",
                "comment": text,
            }
            comment_res = self.client.table("grievance_comments").insert(payload).execute()
            comment_id = comment_res.data[0].get("id") if comment_res.data else None

            # 3. Log audit event
            self.audit_service.log_action(
                admin_auth_user_id=acting_auth_user_id,
                action="grievance.comment_added",
                entity_type="grievance_comment",
                entity_id=comment_id,
                details=f"Official response added to grievance {grievance_id} by {acting_admin_profile.get('full_name')}",
            )

            # 4. Notify student
            if student_auth_id:
                preview = text[:80] + "..." if len(text) > 80 else text
                self.notification_service.notify_student(
                    student_auth_user_id=student_auth_id,
                    grievance_id=grievance_id,
                    title="Official Response Received",
                    message=f"An administrator replied to Ticket #{ticket_number}: \"{preview}\"",
                )

            return True, None

        except Exception as e:
            return False, f"Failed to post comment: {str(e)}"
