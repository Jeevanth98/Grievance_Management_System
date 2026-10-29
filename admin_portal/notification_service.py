"""
notification_service.py - Student Notification Dispatcher
Creates notifications for students when their grievance status changes or official comments are posted.
Internal notes are strictly isolated and NEVER dispatched here.
"""

from typing import Optional
from supabase import Client


class NotificationService:
    def __init__(self, client: Client):
        self.client = client

    def notify_student(
        self,
        student_auth_user_id: str,
        grievance_id: str,
        title: str,
        message: str,
    ) -> bool:
        """
        Dispatches a notification to public.notifications for the specified student.
        """
        if not student_auth_user_id or not grievance_id:
            return False

        payload = {
            "student_auth_user_id": student_auth_user_id,
            "grievance_id": grievance_id,
            "title": title.strip(),
            "message": message.strip(),
            "is_read": False,
        }
        try:
            self.client.table("notifications").insert(payload).execute()
            return True
        except Exception as e:
            print(f"[NotificationService Error] Failed to create notification: {str(e)}")
            return False
