"""
app.py - Student Grievance Management System: Admin Portal
Main entry point for Streamlit application.
Enforces real Supabase authentication, strict role-based access control,
session management, and modular UI routing.
"""
import sys
from pathlib import Path

# Ensure root workspace directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from admin_portal.settings import settings
from admin_portal.supabase_client import get_supabase_client
from admin_portal.auth_service import AuthService
from admin_portal.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_REVIEWER
from admin_portal.ui.styles import apply_custom_styles
from admin_portal.ui.dashboard import render_dashboard
from admin_portal.ui.grievance_list import render_grievance_list
from admin_portal.ui.grievance_details import render_grievance_details
from admin_portal.ui.admin_management import render_admin_management
from admin_portal.ui.audit_logs import render_audit_logs
from admin_portal.ui.settings_page import render_settings_page

# Configure Streamlit page options (guarded if already set by parent launcher)
try:
    st.set_page_config(
        page_title="Grievance Admin Portal",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    pass

# Apply sleek styling
apply_custom_styles()


def render_login_view(auth_service: AuthService):
    """Renders the secure administrator authentication portal."""
    st.markdown(
        """
        <div style="max-width: 440px; margin: 40px auto; background: #FFFFFF; border-radius: 12px;
                    padding: 32px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="font-size: 2.8rem; margin-bottom: 8px;">🏛️</div>
                <h2 style="margin: 0; color: #0F172A; font-size: 1.5rem; font-weight: 700;">Grievance Admin Portal</h2>
                <p style="margin: 6px 0 0 0; color: #64748B; font-size: 0.88rem;">Student Grievance Redressal System</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        col_pad1, col_form, col_pad2 = st.columns([1, 2, 1])
        with col_form:
            with st.form("admin_login_form"):
                email = st.text_input("Administrator Email", placeholder="admin@university.edu")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In to Portal", use_container_width=True, type="primary")

                if submitted:
                    with st.spinner("Verifying credentials & admin privileges..."):
                        success, err_msg, profile, access_token = auth_service.sign_in(email, password)
                        if success and profile:
                            st.session_state["admin_profile"] = profile
                            st.session_state["auth_user_id"] = profile["auth_user_id"]
                            st.session_state["access_token"] = access_token
                            st.session_state["current_nav"] = "Dashboard"
                            st.success(f"Welcome back, {profile.get('full_name')}!")
                            st.rerun()
                        else:
                            st.error(err_msg or "Authentication failed.")

            st.caption(
                "🔒 **Access Restricted:** Ordinary student accounts cannot access this portal. "
                "Contact the University System Administrator to request administrative access."
            )

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    # Apply custom design system on every execution cycle
    apply_custom_styles()

    # 1. Verify Configuration
    if not settings.is_configured:
        st.error(
            "⚠️ **Supabase Configuration Missing!**\n\n"
            "Please create a `.env` file in the project root or configure `.streamlit/secrets.toml` with:\n"
            "```bash\n"
            "SUPABASE_URL=https://your-project.supabase.co\n"
            "SUPABASE_ANON_KEY=your-anon-key\n"
            "```\n"
            "See `.env.example` for reference."
        )
        return

    # 2. Initialize Clients
    access_token = st.session_state.get("access_token")
    client = get_supabase_client(access_token=access_token)
    auth_service = AuthService(client)

    # 3. Check Authentication State
    admin_profile = st.session_state.get("admin_profile")
    auth_user_id = st.session_state.get("auth_user_id")

    if not admin_profile or not auth_user_id:
        render_login_view(auth_service)
        return

    # 4. Render Authenticated Sidebar Navigation
    role = admin_profile.get("role", "admin")
    role_display = role.replace("_", " ").title()

    with st.sidebar:
        # Branding header
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 22px; padding: 6px 0;">
                <span style="font-size: 2rem;">⚖️</span>
                <div>
                    <div style="font-weight: 800; font-size: 1.25rem; color: #0F172A; letter-spacing: -0.02em;">Grievance Admin</div>
                    <div style="font-size: 0.74rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">University Portal</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Profile Card
        full_name = admin_profile.get("full_name", "Administrator")
        initials = "".join([part[0] for part in full_name.split()[:2]]).upper() or "AD"
        st.markdown(
            f"""
            <div class="sidebar-profile-card">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #2563EB, #4F46E5); display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35); flex-shrink: 0;">
                        {initials}
                    </div>
                    <div style="overflow: hidden;">
                        <div class="sidebar-label">Authenticated As</div>
                        <div style="font-weight: 800; color: #0F172A; font-size: 1.15rem; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{full_name}</div>
                    </div>
                </div>
                <div style="margin-top: 12px; display: flex; align-items: center; justify-content: space-between;">
                    <span class="sidebar-role-badge">
                        🛡️ {role_display}
                    </span>
                    <span style="display: flex; align-items: center; gap: 5px; font-size: 0.78rem; color: #059669; font-weight: 700;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: #10B981; display: inline-block;"></span>
                        Online
                    </span>
                </div>
            </div>
            <div class="sidebar-menu-header">Menu Navigation</div>
            """,
            unsafe_allow_html=True,
        )

        nav_options = [
            "📊 Dashboard",
            "📋 All Grievances",
            "⏳ Unassigned Grievances",
            "🎯 My Assigned Grievances",
        ]

        if "selected_grievance_id" in st.session_state:
            nav_options.append("📝 Grievance Details")

        if role == ROLE_SUPER_ADMIN:
            nav_options.append("👥 Admin Management")

        if role in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
            nav_options.append("📜 Audit Logs")

        nav_options.append("⚙️ Settings")

        current_nav = st.session_state.get("current_nav", "Dashboard")
        # Match label
        default_index = 0
        for idx, opt in enumerate(nav_options):
            if current_nav in opt:
                default_index = idx
                break

        selected_page = st.radio("Go To", nav_options, index=default_index, label_visibility="collapsed")

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            auth_service.sign_out()
            st.session_state.clear()
            st.rerun()

    # 5. Route to Selected Page
    clean_choice = selected_page.split(" ", 1)[-1]
    st.session_state["current_nav"] = clean_choice

    if clean_choice == "Dashboard":
        render_dashboard(client, admin_profile)
    elif clean_choice == "All Grievances":
        render_grievance_list(client, admin_profile)
    elif clean_choice == "Unassigned Grievances":
        render_grievance_list(client, admin_profile, preset_filter="unassigned")
    elif clean_choice == "My Assigned Grievances":
        render_grievance_list(client, admin_profile, preset_filter="my_assigned")
    elif clean_choice == "Grievance Details":
        selected_gid = st.session_state.get("selected_grievance_id")
        render_grievance_details(client, admin_profile, auth_user_id, grievance_id=selected_gid)
    elif clean_choice == "Admin Management":
        render_admin_management(client, admin_profile, auth_user_id)
    elif clean_choice == "Audit Logs":
        render_audit_logs(client, admin_profile)
    elif clean_choice == "Settings":
        render_settings_page(client, admin_profile, auth_user_id)


if __name__ == "__main__":
    main()
