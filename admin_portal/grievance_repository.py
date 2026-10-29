"""
grievance_repository.py - Grievance Data Access and Query Operations
Handles real database queries, metrics aggregation, multi-filter search, and related records loading.
Respects anonymity flags and bounds queries.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from supabase import Client


class GrievanceRepository:
    def __init__(self, client: Client):
        self.client = client

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Calculates real-time statistics from the public.grievances table.
        Does not use mock numbers.
        """
        try:
            # Query status, priority, assigned_admin_id, category_id
            res = (
                self.client.table("grievances")
                .select("id, status, priority, assigned_admin_id, category_id, created_at")
                .execute()
            )
            data = res.data or []

            total = len(data)
            status_counts: Dict[str, int] = {}
            priority_counts: Dict[str, int] = {}
            category_counts: Dict[str, int] = {}
            unassigned_count = 0
            urgent_count = 0

            for g in data:
                # Status
                st = g.get("status") or "submitted"
                status_counts[st] = status_counts.get(st, 0) + 1

                # Priority
                pr = g.get("priority") or "medium"
                priority_counts[pr] = priority_counts.get(pr, 0) + 1
                if pr == "urgent":
                    urgent_count += 1

                # Assignment
                if not g.get("assigned_admin_id"):
                    unassigned_count += 1

                # Category
                cat = str(g.get("category_id") or "Uncategorized")
                category_counts[cat] = category_counts.get(cat, 0) + 1

            return {
                "total": total,
                "submitted": status_counts.get("submitted", 0),
                "under_review": status_counts.get("under_review", 0),
                "assigned": status_counts.get("assigned", 0),
                "in_progress": status_counts.get("in_progress", 0),
                "resolved": status_counts.get("resolved", 0),
                "closed": status_counts.get("closed", 0),
                "rejected": status_counts.get("rejected", 0),
                "reopened": status_counts.get("reopened", 0),
                "urgent": urgent_count,
                "unassigned": unassigned_count,
                "status_distribution": status_counts,
                "priority_distribution": priority_counts,
                "category_distribution": category_counts,
            }
        except Exception as e:
            raise RuntimeError(f"Database error while fetching dashboard metrics: {str(e)}")

    def get_categories(self) -> List[Dict[str, Any]]:
        """Fetch all grievance categories."""
        try:
            res = self.client.table("grievance_categories").select("*").order("name").execute()
            return res.data or []
        except Exception as e:
            print(f"[Warning] Could not fetch categories: {str(e)}")
            return []

    def list_grievances(
        self,
        search_query: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        category_id_filter: Optional[str] = None,
        assigned_admin_id_filter: Optional[str] = None,
        unassigned_only: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves a filtered, paginated list of grievances with real database queries.
        Returns: (grievances_list, total_count)
        """
        try:
            # We select grievance fields along with category and assigned_admin details
            query = self.client.table("grievances").select(
                "id, title, description, status, priority, is_anonymous, "
                "student_auth_user_id, category_id, assigned_admin_id, created_at, updated_at, "
                "admin_updated_at, resolved_at, closed_at",
                count="exact"
            )

            if status_filter and status_filter != "all":
                query = query.eq("status", status_filter)

            if priority_filter and priority_filter != "all":
                query = query.eq("priority", priority_filter)

            if category_id_filter and category_id_filter != "all":
                query = query.eq("category_id", category_id_filter)

            if unassigned_only:
                query = query.is_("assigned_admin_id", "null")
            elif assigned_admin_id_filter and assigned_admin_id_filter != "all":
                query = query.eq("assigned_admin_id", assigned_admin_id_filter)

            if start_date:
                query = query.gte("created_at", start_date.isoformat())
            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            # Text search (ilike title or description)
            if search_query and search_query.strip():
                clean_term = search_query.strip()
                query = query.or_(f"title.ilike.%{clean_term}%,description.ilike.%{clean_term}%")

            # Sorting & pagination
            query = query.order(sort_by, desc=sort_desc)
            query = query.range(offset, offset + limit - 1)

            res = query.execute()
            data = res.data or []
            total_count = res.count if res.count is not None else len(data)

            # Enrich category names, display ticket number, and assigned department if possible
            categories_map = {c["id"]: c["name"] for c in self.get_categories()}
            try:
                admin_profiles = self.client.table("admin_profiles").select("id, full_name, department, designation").execute().data or []
                admins_map = {a["id"]: a for a in admin_profiles}
            except Exception:
                admins_map = {}

            for g in data:
                cat_id = g.get("category_id")
                g["category_name"] = categories_map.get(cat_id, "General")
                g["ticket_number"] = f"GRV-{g['id'][:8].upper()}"
                assigned_adm = admins_map.get(g.get("assigned_admin_id"))
                if assigned_adm:
                    g["assigned_department"] = assigned_adm.get("department") or assigned_adm.get("full_name")
                else:
                    g["assigned_department"] = "Unassigned"

            return data, total_count

        except Exception as e:
            raise RuntimeError(f"Failed to query grievances: {str(e)}")

    def get_grievance_details(self, grievance_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full details for a single grievance including related records:
        - Category name
        - Student info (masked if anonymous!)
        - Assigned admin profile
        - Status history
        - Comments
        - Attachments
        - Assignment history
        """
        try:
            # 1. Fetch core grievance
            res = (
                self.client.table("grievances")
                .select("*")
                .eq("id", grievance_id)
                .limit(1)
                .execute()
            )
            if not res.data or len(res.data) == 0:
                return None

            grievance = res.data[0]
            grievance["ticket_number"] = f"GRV-{grievance['id'][:8].upper()}"

            # 2. Fetch category
            if grievance.get("category_id"):
                cat_res = (
                    self.client.table("grievance_categories")
                    .select("*")
                    .eq("id", grievance["category_id"])
                    .limit(1)
                    .execute()
                )
                grievance["category"] = cat_res.data[0] if cat_res.data else None

            # 3. Student information (Respect anonymity rules!)
            if grievance.get("student_auth_user_id"):
                if grievance.get("is_anonymous", False):
                    grievance["student"] = {
                        "full_name": "Anonymous Student",
                        "register_number": "PROTECTED",
                        "department": "Confidential",
                        "email": "confidential@student.edu",
                        "is_anonymous": True,
                    }
                else:
                    std_res = (
                        self.client.table("students")
                        .select("*")
                        .eq("auth_user_id", grievance["student_auth_user_id"])
                        .limit(1)
                        .execute()
                    )
                    if std_res.data:
                        std = std_res.data[0]
                        std["full_name"] = std.get("name") or std.get("full_name", "Student")
                        std["register_number"] = std.get("student_id") or std.get("register_number", "N/A")
                        std["phone_number"] = std.get("phone") or std.get("phone_number", "")
                        grievance["student"] = std
                    else:
                        grievance["student"] = None

            # 4. Assigned Admin details
            if grievance.get("assigned_admin_id"):
                adm_res = (
                    self.client.table("admin_profiles")
                    .select("id, full_name, email, role, department, designation")
                    .eq("id", grievance["assigned_admin_id"])
                    .limit(1)
                    .execute()
                )
                grievance["assigned_admin"] = adm_res.data[0] if adm_res.data else None

            # 5. Status history
            try:
                hist_res = (
                    self.client.table("grievance_status_history")
                    .select("*")
                    .eq("grievance_id", grievance_id)
                    .order("changed_at", desc=False)
                    .execute()
                )
            except Exception:
                hist_res = (
                    self.client.table("grievance_status_history")
                    .select("*")
                    .eq("grievance_id", grievance_id)
                    .execute()
                )
            history_rows = hist_res.data or []
            for h in history_rows:
                h["created_at"] = h.get("changed_at") or h.get("created_at", "")
                h["change_reason"] = h.get("remarks") or h.get("change_reason", "")
            grievance["status_history"] = history_rows

            # 6. Official Comments
            com_res = (
                self.client.table("grievance_comments")
                .select("*")
                .eq("grievance_id", grievance_id)
                .order("created_at", desc=False)
                .execute()
            )
            grievance["comments"] = com_res.data or []

            # 7. Attachments
            att_res = (
                self.client.table("grievance_attachments")
                .select("*")
                .eq("grievance_id", grievance_id)
                .order("created_at", desc=False)
                .execute()
            )
            grievance["attachments"] = att_res.data or []

            # 8. Assignment history
            asg_res = (
                self.client.table("grievance_assignments")
                .select("*")
                .eq("grievance_id", grievance_id)
                .order("assigned_at", desc=True)
                .execute()
            )
            grievance["assignments"] = asg_res.data or []

            return grievance

        except Exception as e:
            raise RuntimeError(f"Error fetching grievance details for {grievance_id}: {str(e)}")
