"""
conftest.py - Pytest fixtures and Mock Supabase Client
Provides unit test isolation without requiring production database credentials.
"""

import pytest
from unittest.mock import MagicMock
from admin_portal.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_REVIEWER


@pytest.fixture
def mock_admin_profiles():
    """Sample admin profile records."""
    return {
        "super_admin": {
            "id": "adm-001-uuid",
            "auth_user_id": "auth-001-uuid",
            "full_name": "Dr. Sarah SuperAdmin",
            "email": "sarah@university.edu",
            "role": ROLE_SUPER_ADMIN,
            "department": "Administration",
            "designation": "Dean of Student Affairs",
            "is_active": True,
        },
        "admin": {
            "id": "adm-002-uuid",
            "auth_user_id": "auth-002-uuid",
            "full_name": "Prof. Alan Admin",
            "email": "alan@university.edu",
            "role": ROLE_ADMIN,
            "department": "Hostel Affairs",
            "designation": "Warden",
            "is_active": True,
        },
        "reviewer": {
            "id": "adm-003-uuid",
            "auth_user_id": "auth-003-uuid",
            "full_name": "Rita Reviewer",
            "email": "rita@university.edu",
            "role": ROLE_REVIEWER,
            "department": "Academics",
            "designation": "Teaching Assistant",
            "is_active": True,
        },
        "inactive_admin": {
            "id": "adm-004-uuid",
            "auth_user_id": "auth-004-uuid",
            "full_name": "Ian Inactive",
            "email": "ian@university.edu",
            "role": ROLE_ADMIN,
            "department": "Library",
            "designation": "Former Assistant",
            "is_active": False,
        },
    }


class MockQueryBuilder:
    def __init__(self, table_name: str, database_store: dict):
        self.table_name = table_name
        self.database_store = database_store
        self._filters = []
        self._limit_val = None
        self._count_mode = None

    def select(self, columns: str = "*", count: str = None):
        self._count_mode = count
        return self

    def eq(self, column: str, value: any):
        self._filters.append((column, "eq", value))
        return self

    def is_(self, column: str, value: str):
        self._filters.append((column, "is", value))
        return self

    def order(self, column: str, desc: bool = False):
        return self

    def limit(self, count: int):
        self._limit_val = count
        return self

    def range(self, start: int, end: int):
        return self

    def insert(self, payload: dict):
        table_rows = self.database_store.setdefault(self.table_name, [])
        record = dict(payload)
        if "id" not in record:
            record["id"] = f"mock-id-{len(table_rows) + 1}"
        table_rows.append(record)
        res = MagicMock()
        res.data = [record]
        return res

    def update(self, payload: dict):
        self._update_payload = payload
        return self

    def execute(self):
        rows = self.database_store.get(self.table_name, [])
        filtered = list(rows)
        for col, op, val in self._filters:
            if op == "eq":
                filtered = [r for r in filtered if r.get(col) == val]
            elif op == "is" and val == "null":
                filtered = [r for r in filtered if r.get(col) is None]

        # Handle update execution
        if hasattr(self, "_update_payload"):
            for r in filtered:
                r.update(self._update_payload)
            res = MagicMock()
            res.data = filtered
            return res

        if self._limit_val is not None:
            filtered = filtered[:self._limit_val]

        res = MagicMock()
        res.data = filtered
        res.count = len(rows) if self._count_mode else None
        return res


@pytest.fixture
def mock_supabase_client(mock_admin_profiles):
    """Configures a stateful mock client mimicking Supabase table operations."""
    client = MagicMock()
    database_store = {
        "admin_profiles": list(mock_admin_profiles.values()),
        "grievances": [
            {
                "id": "g-101-uuid",
                "ticket_number": "TICK-101",
                "student_auth_user_id": "student-user-uuid",
                "category_id": "cat-hostel-uuid",
                "title": "Water heater broken in Block B",
                "description": "Geyser is not working since Monday.",
                "status": "submitted",
                "priority": "high",
                "is_anonymous": False,
                "assigned_admin_id": None,
                "created_at": "2026-10-20T10:00:00Z",
                "updated_at": "2026-10-20T10:00:00Z",
                "admin_updated_at": None,
                "resolved_at": None,
                "closed_at": None,
            },
            {
                "id": "g-102-uuid",
                "ticket_number": "TICK-102",
                "student_auth_user_id": "student-user-uuid-2",
                "category_id": "cat-academic-uuid",
                "title": "Grade disparity in OOPs lab",
                "description": "Need re-evaluation of practical test.",
                "status": "assigned",
                "priority": "medium",
                "is_anonymous": True,
                "assigned_admin_id": "adm-002-uuid",
                "created_at": "2026-10-21T08:00:00Z",
                "updated_at": "2026-10-21T08:00:00Z",
                "admin_updated_at": None,
                "resolved_at": None,
                "closed_at": None,
            },
        ],
        "grievance_categories": [
            {"id": "cat-hostel-uuid", "name": "Hostel Facilities"},
            {"id": "cat-academic-uuid", "name": "Academic Evaluation"},
        ],
        "grievance_status_history": [],
        "grievance_assignments": [],
        "grievance_comments": [],
        "grievance_internal_notes": [],
        "admin_audit_logs": [],
        "notifications": [],
    }

    client.table.side_effect = lambda tname: MockQueryBuilder(tname, database_store)
    client._store = database_store
    return client
