"""
constants.py - Application Constants, Enums, Role Permissions & Transition Rules
"""

from typing import Dict, List, Set

# Supported Admin Roles
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_REVIEWER = "reviewer"
VALID_ROLES: Set[str] = {ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_REVIEWER}

# Grievance Status Enum Values
STATUS_SUBMITTED = "submitted"
STATUS_UNDER_REVIEW = "under_review"
STATUS_ASSIGNED = "assigned"
STATUS_IN_PROGRESS = "in_progress"
STATUS_RESOLVED = "resolved"
STATUS_CLOSED = "closed"
STATUS_REJECTED = "rejected"
STATUS_REOPENED = "reopened"

VALID_STATUSES: List[str] = [
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_ASSIGNED,
    STATUS_IN_PROGRESS,
    STATUS_RESOLVED,
    STATUS_CLOSED,
    STATUS_REJECTED,
    STATUS_REOPENED,
]

# Grievance Priority Enum Values
PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_URGENT = "urgent"

VALID_PRIORITIES: List[str] = [
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_URGENT,
]

# Allowed Status Transition Matrix
# key: current_status -> set of allowed target statuses
STATUS_TRANSITION_MATRIX: Dict[str, Set[str]] = {
    STATUS_SUBMITTED: {STATUS_UNDER_REVIEW, STATUS_ASSIGNED, STATUS_REJECTED},
    STATUS_UNDER_REVIEW: {STATUS_ASSIGNED, STATUS_IN_PROGRESS, STATUS_REJECTED},
    STATUS_ASSIGNED: {STATUS_IN_PROGRESS, STATUS_UNDER_REVIEW, STATUS_RESOLVED, STATUS_REJECTED},
    STATUS_IN_PROGRESS: {STATUS_RESOLVED, STATUS_UNDER_REVIEW, STATUS_REJECTED},
    STATUS_RESOLVED: {STATUS_CLOSED, STATUS_REOPENED},
    STATUS_CLOSED: {STATUS_REOPENED},
    STATUS_REJECTED: {STATUS_REOPENED},
    STATUS_REOPENED: {STATUS_UNDER_REVIEW, STATUS_ASSIGNED, STATUS_IN_PROGRESS},
}

# Role-Based Permissions
PERMISSIONS = {
    ROLE_SUPER_ADMIN: {
        "can_view_all_grievances": True,
        "can_assign": True,
        "can_change_priority": True,
        "can_update_status": True,
        "can_add_internal_notes": True,
        "can_add_official_response": True,
        "can_view_audit_logs": True,
        "can_manage_admins": True,
        "can_reopen_closed": True,
    },
    ROLE_ADMIN: {
        "can_view_all_grievances": True,
        "can_assign": True,
        "can_change_priority": True,
        "can_update_status": True,
        "can_add_internal_notes": True,
        "can_add_official_response": True,
        "can_view_audit_logs": True,
        "can_manage_admins": False,
        "can_reopen_closed": True,
    },
    ROLE_REVIEWER: {
        "can_view_all_grievances": True,
        "can_assign": False,
        "can_change_priority": False,
        "can_update_status": True,  # e.g., can move submitted -> under_review
        "can_add_internal_notes": True,
        "can_add_official_response": False,
        "can_view_audit_logs": False,
        "can_manage_admins": False,
        "can_reopen_closed": False,
    },
}

# Visual Styling Badges & Themes
STATUS_STYLES = {
    STATUS_SUBMITTED: {"bg": "#EFF6FF", "text": "#1E40AF", "border": "#BFDBFE", "label": "Submitted"},
    STATUS_UNDER_REVIEW: {"bg": "#FEF3C7", "text": "#92400E", "border": "#FDE68A", "label": "Under Review"},
    STATUS_ASSIGNED: {"bg": "#F5F3FF", "text": "#5B21B6", "border": "#DDD6FE", "label": "Assigned"},
    STATUS_IN_PROGRESS: {"bg": "#E0E7FF", "text": "#3730A3", "border": "#C7D2FE", "label": "In Progress"},
    STATUS_RESOLVED: {"bg": "#ECFDF5", "text": "#065F46", "border": "#A7F3D0", "label": "Resolved"},
    STATUS_CLOSED: {"bg": "#F1F5F9", "text": "#334155", "border": "#CBD5E1", "label": "Closed"},
    STATUS_REJECTED: {"bg": "#FEF2F2", "text": "#991B1B", "border": "#FECACA", "label": "Rejected"},
    STATUS_REOPENED: {"bg": "#FFFBEB", "text": "#B45309", "border": "#FDE68A", "label": "Reopened"},
}

PRIORITY_STYLES = {
    PRIORITY_LOW: {"bg": "#F1F5F9", "text": "#475569", "border": "#CBD5E1", "label": "Low"},
    PRIORITY_MEDIUM: {"bg": "#EFF6FF", "text": "#1D4ED8", "border": "#BFDBFE", "label": "Medium"},
    PRIORITY_HIGH: {"bg": "#FFF7ED", "text": "#C2410C", "border": "#FFEDD5", "label": "High"},
    PRIORITY_URGENT: {"bg": "#FEF2F2", "text": "#B91C1C", "border": "#FECACA", "label": "Urgent"},
}
