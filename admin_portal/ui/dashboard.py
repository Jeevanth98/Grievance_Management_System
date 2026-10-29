"""
dashboard.py - Executive Admin Overview and Real-time Analytics
Displays summary metrics, workload distributions, priority breakdown, and recent records.
All figures are computed dynamically from real database queries.
"""

from typing import Dict, Any
import streamlit as st
import pandas as pd
from admin_portal.grievance_repository import GrievanceRepository
from admin_portal.ui.components import render_metric_card, render_header_banner, render_empty_state, get_status_badge_html, get_priority_badge_html


def render_dashboard(client, admin_profile: Dict[str, Any]):
    """Renders the administrative dashboard with real-time stats."""
    render_header_banner(
        title="Administrative Overview",
        subtitle=f"Welcome back, {admin_profile.get('full_name')} ({admin_profile.get('role').replace('_', ' ').title()})"
    )

    repo = GrievanceRepository(client)

    # Top action bar with manual refresh
    col_t1, col_t2 = st.columns([8, 2])
    with col_t2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # Fetch live metrics
    with st.spinner("Fetching database statistics..."):
        try:
            metrics = repo.get_dashboard_metrics()
        except Exception as e:
            st.error(f"⚠️ Failed to query grievance statistics: {str(e)}")
            return

    total = metrics.get("total", 0)

    # Empty State Check
    if total == 0:
        render_empty_state(
            title="No Grievances Recorded Yet",
            description="When students submit complaints through the Student Portal, real-time analytics and management actions will populate here."
        )
        return

    # First row: Overall, Urgent, Unassigned
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        render_metric_card("Total Grievances", total, "All-time campus submissions", "#2563EB", icon="📁")
    with r1_c2:
        render_metric_card("Urgent Action Required", metrics.get("urgent", 0), "Needs immediate attention", "#EF4444", icon="🚨")
    with r1_c3:
        render_metric_card("Unassigned Grievances", metrics.get("unassigned", 0), "Pending staff assignment", "#F59E0B", icon="⏳")

    st.write("")

    # Second row: Status lifecycle metrics
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    with s1:
        render_metric_card("Submitted", metrics.get("submitted", 0), "New", "#3B82F6", icon="📥")
    with s2:
        render_metric_card("Under Review", metrics.get("under_review", 0), "Triaging", "#D97706", icon="🔍")
    with s3:
        render_metric_card("Assigned", metrics.get("assigned", 0), "In queue", "#8B5CF6", icon="👤")
    with s4:
        render_metric_card("In Progress", metrics.get("in_progress", 0), "Active", "#6366F1", icon="⚙️")
    with s5:
        render_metric_card("Resolved", metrics.get("resolved", 0), "Outcome ready", "#10B981", icon="✅")
    with s6:
        render_metric_card("Closed", metrics.get("closed", 0), "Finalized", "#64748B", icon="🔒")

    st.write("")
    st.markdown("---")

    # Analytics Charts Section
    ch_col1, ch_col2 = st.columns(2)

    with ch_col1:
        st.subheader("📊 Grievances by Status")
        status_dist = metrics.get("status_distribution", {})
        if status_dist:
            df_status = pd.DataFrame(list(status_dist.items()), columns=["Status", "Count"])
            df_status["Status"] = df_status["Status"].str.replace("_", " ").str.title()
            st.bar_chart(df_status.set_index("Status"), color="#2563EB")
        else:
            st.info("No status distribution available.")

    with ch_col2:
        st.subheader("⚡ Grievance Priority Distribution")
        prio_dist = metrics.get("priority_distribution", {})
        if prio_dist:
            df_prio = pd.DataFrame(list(prio_dist.items()), columns=["Priority", "Count"])
            df_prio["Priority"] = df_prio["Priority"].str.title()
            st.bar_chart(df_prio.set_index("Priority"), color="#F97316")
        else:
            st.info("No priority distribution available.")

    st.write("")
    st.markdown("---")

    # Recent Grievances Preview Table
    st.subheader("🕒 Recently Submitted Grievances")
    recent, _ = repo.list_grievances(limit=8, sort_by="created_at", sort_desc=True)
    if recent:
        table_rows = []
        for g in recent:
            ticket = g.get("ticket_number") or f"GRV-{str(g.get('id', ''))[:8].upper()}"
            created = str(g.get("created_at", ""))[:10]
            table_rows.append({
                "Ticket #": ticket,
                "Title": g.get("title", ""),
                "Category": g.get("category_name", "General"),
                "Status": str(g.get("status", "")).replace("_", " ").title(),
                "Priority": str(g.get("priority", "")).title(),
                "Date": created,
                "ID": g.get("id"),
            })
        df_recent = pd.DataFrame(table_rows)
        st.dataframe(df_recent[["Ticket #", "Title", "Category", "Status", "Priority", "Date"]], use_container_width=True)
        st.caption("Tip: Navigate to **All Grievances** in the sidebar to review details, assign staff, or respond.")
    else:
        st.write("No recent grievances found.")
