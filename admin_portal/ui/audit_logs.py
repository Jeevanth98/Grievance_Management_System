"""
audit_logs.py - Administrative Audit Trail Viewer
Displays immutable historical logs of all administrative actions.
Accessible to Super Administrators and Administrators.
"""

from typing import Dict, Any
import streamlit as st
import pandas as pd
from admin_portal.audit_service import AuditService
from admin_portal.constants import PERMISSIONS
from admin_portal.ui.components import render_header_banner, render_empty_state


def render_audit_logs(client, admin_profile: Dict[str, Any]):
    """Renders the administrative audit log viewer."""
    acting_role = admin_profile.get("role", "")
    if not PERMISSIONS.get(acting_role, {}).get("can_view_audit_logs", False):
        st.error("⛔ Access Denied: Your role is not authorized to inspect administrative audit logs.")
        return

    render_header_banner(
        title="Security & Action Audit Logs",
        subtitle="Immutable historical records of status updates, assignments, staff notes, and account modifications"
    )

    audit_service = AuditService(client)

    # Filter row
    f1, f2, f3 = st.columns([4, 4, 2])
    with f1:
        action_options = [
            "All Actions",
            "grievance.assignment_changed",
            "grievance.status_changed",
            "grievance.priority_changed",
            "grievance.comment_added",
            "grievance.internal_note_added",
            "admin.created",
            "admin.role_changed",
            "admin.status_toggled",
        ]
        chosen_action = st.selectbox("Filter Action", action_options)
        action_filter = chosen_action if chosen_action != "All Actions" else None

    with f2:
        entity_options = ["All Entities", "grievance", "grievance_comment", "grievance_internal_note", "admin_profile"]
        chosen_entity = st.selectbox("Entity Type", entity_options)
        entity_filter = chosen_entity if chosen_entity != "All Entities" else None

    with f3:
        limit_val = st.selectbox("Max Records", [50, 100, 200], index=1)

    with st.spinner("Loading audit logs..."):
        try:
            logs = audit_service.list_logs(limit=limit_val, action_filter=action_filter, entity_type_filter=entity_filter)
        except Exception as e:
            st.error(f"Failed to fetch audit logs: {str(e)}")
            return

    if not logs:
        render_empty_state("No Audit Records Found", "No administrative actions have matched your filter criteria.")
        return

    st.write(f"Displaying **{len(logs)}** historical audit records:")

    for log in logs:
        action = log.get("action", "unknown")
        entity_type = log.get("entity_type", "")
        entity_id = log.get("entity_id") or "N/A"
        created_at = log.get("created_at", "")[:19].replace("T", " ")
        details = log.get("details") or "No details recorded"
        actor = log.get("admin_auth_user_id", "")[:8] + "..."

        with st.container():
            c1, c2 = st.columns([3, 7])
            with c1:
                st.markdown(f"**`{action}`**")
                st.caption(f"📅 {created_at} UTC\n👤 Actor: {actor}")
            with c2:
                st.write(f"**Entity:** {entity_type} (`{entity_id}`)")
                st.write(f"**Details:** {details}")
                if log.get("old_values") or log.get("new_values"):
                    with st.expander("Inspect State Diff", expanded=False):
                        sc1, sc2 = st.columns(2)
                        with sc1:
                            st.caption("Old Values:")
                            st.json(log.get("old_values") or {})
                        with sc2:
                            st.caption("New Values:")
                            st.json(log.get("new_values") or {})
            st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
