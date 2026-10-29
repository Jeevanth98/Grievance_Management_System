"""
grievance_list.py - Grievance Management, Multi-Filter Search, and Pagination
Supports searching, status/category/priority filtering, assignment states, and selection.
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
from datetime import datetime
from admin_portal.grievance_repository import GrievanceRepository
from admin_portal.admin_repository import AdminRepository
from admin_portal.constants import VALID_STATUSES, VALID_PRIORITIES
from admin_portal.ui.components import render_header_banner, render_empty_state


def render_grievance_list(
    client,
    admin_profile: Dict[str, Any],
    preset_filter: Optional[str] = None,
):
    """
    Renders the grievance management list view.
    preset_filter: Optional preset like 'unassigned' or 'my_assigned'.
    """
    title = "Grievance Directory"
    subtitle = "Review, triage, filter, and assign student grievances"
    if preset_filter == "unassigned":
        title = "Unassigned Grievances"
        subtitle = "Grievances awaiting initial assignment to an administrative reviewer"
    elif preset_filter == "my_assigned":
        title = "My Assigned Grievances"
        subtitle = "Grievances assigned specifically to your account"

    render_header_banner(title, subtitle)

    repo = GrievanceRepository(client)
    admin_repo = AdminRepository(client)

    # Load categories and active admins for filter dropdowns
    categories = repo.get_categories()
    admins = admin_repo.list_all(active_only=True)

    cat_options = {"All Categories": "all"}
    for c in categories:
        cat_options[c["name"]] = c["id"]

    admin_options = {"All Departments": "all"}
    # Populate departments first
    dept_admins = [
        a for a in admins
        if a.get("department")
        and a.get("department") not in ["Administration", "Administrative Affairs"]
        and "System Admin" not in a.get("full_name", "")
    ]
    for a in (dept_admins if dept_admins else admins):
        dept = a.get("department")
        desig = a.get("designation")
        if dept and desig:
            admin_options[f"🏢 {dept} ({desig})"] = a["id"]
        elif dept:
            admin_options[f"🏢 {dept}"] = a["id"]
        else:
            admin_options[f"👤 {a['full_name']} ({a['role']})"] = a["id"]

    # Filter Section
    with st.expander("🔍 Search & Filter Controls", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            search_query = st.text_input("Search Title or Description", placeholder="e.g. library, exam, fees...")
        with f_col2:
            status_labels = ["All Statuses"] + [s.replace("_", " ").title() for s in VALID_STATUSES]
            selected_status_label = st.selectbox("Status", status_labels, index=0)
            status_filter = (
                selected_status_label.lower().replace(" ", "_")
                if selected_status_label != "All Statuses"
                else "all"
            )
        with f_col3:
            prio_labels = ["All Priorities"] + [p.title() for p in VALID_PRIORITIES]
            selected_prio_label = st.selectbox("Priority", prio_labels, index=0)
            prio_filter = (
                selected_prio_label.lower()
                if selected_prio_label != "All Priorities"
                else "all"
            )

        f2_col1, f2_col2, f2_col3 = st.columns(3)
        with f2_col1:
            selected_cat_name = st.selectbox("Category", list(cat_options.keys()))
            cat_filter = cat_options[selected_cat_name]

        with f2_col2:
            if preset_filter == "my_assigned":
                admin_filter = admin_profile.get("id")
                st.text_input("Assigned Department", value=admin_profile.get("department") or admin_profile.get("full_name"), disabled=True)
            elif preset_filter == "unassigned":
                admin_filter = "all"
                st.text_input("Assignment State", value="Unassigned Only", disabled=True)
            else:
                selected_admin_name = st.selectbox("Assigned Department", list(admin_options.keys()))
                admin_filter = admin_options[selected_admin_name]

        with f2_col3:
            sort_choice = st.selectbox("Sort Order", ["Newest First", "Oldest First"])
            sort_desc = (sort_choice == "Newest First")

    # Pagination controls in session state
    if "list_page" not in st.session_state:
        st.session_state["list_page"] = 0

    page_size = 15
    offset = st.session_state["list_page"] * page_size

    is_unassigned = (preset_filter == "unassigned")

    with st.spinner("Loading records from database..."):
        try:
            records, total_count = repo.list_grievances(
                search_query=search_query,
                status_filter=status_filter,
                priority_filter=prio_filter,
                category_id_filter=cat_filter,
                assigned_admin_id_filter=admin_filter if not is_unassigned else None,
                unassigned_only=is_unassigned,
                sort_by="created_at",
                sort_desc=sort_desc,
                limit=page_size,
                offset=offset,
            )
        except Exception as e:
            st.error(f"Error querying grievances: {str(e)}")
            return

    st.write(f"Showing **{len(records)}** of **{total_count}** matching grievances (Page {st.session_state['list_page'] + 1})")

    if not records:
        render_empty_state("No Matching Grievances Found", "Try adjusting your search criteria or filter controls above.")
        return

    # Render Card / Grid View for clean interactivity
    for item in records:
        g_id = item["id"]
        ticket = item.get("ticket_number") or f"GRV-{g_id[:8].upper()}"
        status_text = item.get("status", "submitted").replace("_", " ").title()
        prio_text = item.get("priority", "medium").title()
        cat_name = item.get("category_name", "General")
        is_anon = item.get("is_anonymous", False)
        created_str = item.get("created_at", "")[:10]

        # Container card
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 5, 3, 2])
            with c1:
                st.markdown(f"**Ticket #{ticket}**")
                if is_anon:
                    st.markdown("<span class='anon-badge'>🕶️ Anonymous</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{item.get('title', 'Untitled')}**")
                desc = item.get('description', '')
                snippet = desc[:100] + ("..." if len(desc) > 100 else "")
                st.caption(f"{cat_name} • {snippet}")
            with c3:
                st.markdown(f"Status: **{status_text}**")
                dept_label = item.get("assigned_department", "Unassigned")
                st.caption(f"Priority: **{prio_text}** | Dept: **{dept_label}**")
            with c4:
                if st.button("Open Details →", key=f"btn_view_{g_id}", use_container_width=True):
                    st.session_state["selected_grievance_id"] = g_id
                    st.session_state["current_nav"] = "Grievance Details"
                    st.rerun()
            st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # Pagination buttons
    max_pages = (total_count + page_size - 1) // page_size
    col_p1, col_p2, col_p3 = st.columns([2, 6, 2])
    with col_p1:
        if st.session_state["list_page"] > 0:
            if st.button("← Previous Page"):
                st.session_state["list_page"] -= 1
                st.rerun()
    with col_p2:
        st.markdown(f"<div style='text-align: center; color: #64748B; padding-top: 8px;'>Page {st.session_state['list_page'] + 1} of {max(1, max_pages)}</div>", unsafe_allow_html=True)
    with col_p3:
        if (st.session_state["list_page"] + 1) < max_pages:
            if st.button("Next Page →"):
                st.session_state["list_page"] += 1
                st.rerun()
