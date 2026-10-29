"""
settings_page.py - Administrative Profile & System Diagnostics
Displays session health, connected database status, and configuration details.
Never prints sensitive credentials.
"""

from typing import Dict, Any
import streamlit as st
from admin_portal.settings import settings
from admin_portal.ui.components import render_header_banner


def render_settings_page(client, admin_profile: Dict[str, Any], auth_user_id: str):
    """Renders profile inspection and system health diagnostics."""
    render_header_banner(
        title="Admin Settings & Diagnostics",
        subtitle="Active session parameters, database connectivity, and environment verification"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👤 Administrator Profile")
        st.write(f"**Full Name:** {admin_profile.get('full_name')}")
        st.write(f"**Email:** {admin_profile.get('email')}")
        st.write(f"**Role:** `{admin_profile.get('role')}`")
        st.write(f"**Department:** {admin_profile.get('department') or 'General'}")
        st.write(f"**Designation:** {admin_profile.get('designation') or 'Staff'}")
        st.write(f"**Admin Profile ID:** `{admin_profile.get('id')}`")
        st.write(f"**Supabase Auth User UUID:** `{auth_user_id}`")
        st.write(f"**Account Status:** {'Active 🟢' if admin_profile.get('is_active') else 'Deactivated 🔴'}")

    with col2:
        st.markdown("### 🌐 Backend & Connectivity")
        st.write(f"**Supabase Project URL:** `{settings.supabase_url}`")
        st.write(f"**Public Anon Key:** Configured ✅")
        st.write(f"**Service Role Key:** {'Configured (Privileged Provisioning Active) 🛡️' if settings.supabase_service_role_key else 'Not configured (Client-only mode) ℹ️'}")
        st.write(f"**Environment:** `{settings.app_env}`")

        st.write("")
        if st.button("🧪 Run Database Ping Test"):
            try:
                res = client.table("grievance_categories").select("count", count="exact").execute()
                st.success(f"Connection healthy! Database ping succeeded (found categories count: {res.count}).")
            except Exception as e:
                st.error(f"Connection test failed: {str(e)}")
