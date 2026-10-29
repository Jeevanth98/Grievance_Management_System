"""
admin_management.py - Super Admin Profile Management & Account Provisioning
Restricted strictly to Super Administrators.
Allows listing, searching, role modification, account activation/deactivation,
and provisioning of new administrator credentials.
"""

from typing import Dict, Any
import streamlit as st
import pandas as pd
from admin_portal.admin_repository import AdminRepository
from admin_portal.audit_service import AuditService
from admin_portal.supabase_client import get_service_role_client
from admin_portal.constants import VALID_ROLES, ROLE_SUPER_ADMIN
from admin_portal.ui.components import render_header_banner


def render_admin_management(client, admin_profile: Dict[str, Any], auth_user_id: str):
    """Renders administrative team management view."""
    current_role = admin_profile.get("role")
    if current_role != ROLE_SUPER_ADMIN:
        st.error("⛔ Access Denied: Administrator Management is restricted to Super Administrators only.")
        return

    render_header_banner(
        title="Administrator Management",
        subtitle="Manage administrative staff accounts, role permissions, and access privileges"
    )

    admin_repo = AdminRepository(client)
    audit_service = AuditService(client)

    tab_list, tab_create = st.tabs(["👥 Current Administrators", "➕ Provision New Administrator"])

    # TAB 1: Current Admins List & Actions
    with tab_list:
        with st.spinner("Loading administrators..."):
            try:
                all_admins = admin_repo.list_all(active_only=False)
            except Exception as e:
                st.error(f"Error fetching administrators: {str(e)}")
                return

        # Search & Filter
        col_s1, col_s2 = st.columns([6, 4])
        with col_s1:
            search = st.text_input("Search by Name or Email", placeholder="e.g. John, admin@university.edu")
        with col_s2:
            role_filter = st.selectbox("Filter by Role", ["All Roles"] + [r.replace("_", " ").title() for r in VALID_ROLES])

        filtered = all_admins
        if search.strip():
            term = search.strip().lower()
            filtered = [a for a in filtered if term in a.get("full_name", "").lower() or term in a.get("email", "").lower()]
        if role_filter != "All Roles":
            expected_role = role_filter.lower().replace(" ", "_")
            filtered = [a for a in filtered if a.get("role") == expected_role]

        st.write(f"Showing **{len(filtered)}** administrative accounts:")

        for adm in filtered:
            adm_id = adm["id"]
            is_self = (adm["auth_user_id"] == auth_user_id)
            is_active = adm.get("is_active", True)
            role_title = adm.get("role", "admin").replace("_", " ").title()

            with st.container():
                c1, c2, c3, c4 = st.columns([3, 3, 2, 4])
                with c1:
                    st.markdown(f"**{adm.get('full_name')}** {'*(You)*' if is_self else ''}")
                    st.caption(adm.get("email"))
                with c2:
                    st.write(f"**Role:** {role_title}")
                    st.caption(f"Dept: {adm.get('department') or 'General'} | {adm.get('designation') or 'Staff'}")
                with c3:
                    if is_active:
                        st.markdown("<span style='color: #10B981; font-weight: 600;'>🟢 Active</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color: #EF4444; font-weight: 600;'>🔴 Deactivated</span>", unsafe_allow_html=True)
                with c4:
                    if not is_self:
                        sub_c1, sub_c2 = st.columns(2)
                        with sub_c1:
                            # Change Role Form
                            new_r = st.selectbox(
                                "Role",
                                options=list(VALID_ROLES),
                                index=list(VALID_ROLES).index(adm.get("role", "admin")),
                                key=f"role_sel_{adm_id}",
                                label_visibility="collapsed"
                            )
                            if new_r != adm.get("role"):
                                if st.button("Save", key=f"save_role_{adm_id}"):
                                    try:
                                        old_role = adm.get("role")
                                        admin_repo.update_role(adm_id, new_r)
                                        audit_service.log_action(
                                            admin_auth_user_id=auth_user_id,
                                            action="admin.role_changed",
                                            entity_type="admin_profile",
                                            entity_id=adm_id,
                                            old_values={"role": old_role},
                                            new_values={"role": new_r},
                                            details=f"Role of {adm.get('full_name')} changed from {old_role} to {new_r}",
                                        )
                                        st.success("Role updated!")
                                        st.rerun()
                                    except Exception as ex:
                                        st.error(f"Error: {str(ex)}")
                        with sub_c2:
                            toggle_label = "Deactivate" if is_active else "Activate"
                            btn_type = "secondary" if is_active else "primary"
                            if st.button(toggle_label, key=f"toggle_{adm_id}", type=btn_type):
                                try:
                                    admin_repo.update_active_status(adm_id, not is_active)
                                    audit_service.log_action(
                                        admin_auth_user_id=auth_user_id,
                                        action="admin.status_toggled",
                                        entity_type="admin_profile",
                                        entity_id=adm_id,
                                        old_values={"is_active": is_active},
                                        new_values={"is_active": not is_active},
                                        details=f"Account status of {adm.get('full_name')} changed to {'active' if not is_active else 'inactive'}",
                                    )
                                    st.success(f"Account {toggle_label}d!")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error: {str(ex)}")
                    else:
                        st.caption("Cannot modify self.")
                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # TAB 2: Provision New Administrator
    with tab_create:
        st.markdown("#### Create New Administrator Profile")
        st.caption("Provision credentials and assign an administrative role.")

        service_client = get_service_role_client()
        if not service_client:
            st.info(
                "ℹ️ **Note on Service Role Key:** To provision new Auth credentials directly from this form, "
                "configure `SUPABASE_SERVICE_ROLE_KEY` in your `.env` or `.streamlit/secrets.toml`. "
                "Alternatively, you can register the user in Supabase Auth Dashboard and link them using their Auth User UUID below."
            )

        with st.form("form_create_admin"):
            full_name = st.text_input("Full Name", placeholder="e.g. Dr. Rajesh Kumar")
            email = st.text_input("Email Address", placeholder="e.g. rkumar@university.edu")
            role = st.selectbox("Assigned Role", list(VALID_ROLES), format_func=lambda r: r.replace("_", " ").title())
            department = st.text_input("Department", placeholder="e.g. Computer Science, Academic Affairs")
            designation = st.text_input("Designation", placeholder="e.g. Head of Department, Student Counselor")

            if service_client:
                password = st.text_input("Initial Password (Min 8 chars)", type="password", placeholder="Secure temporary password")
                auth_user_id_override = None
            else:
                password = None
                auth_user_id_override = st.text_input("Supabase Auth User UUID (From Supabase Auth Dashboard)", placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000")

            submit_create = st.form_submit_button("Provision Administrator", type="primary")

            if submit_create:
                if not full_name.strip() or not email.strip():
                    st.error("Name and Email are required.")
                else:
                    try:
                        target_auth_id = None
                        if service_client:
                            if not password or len(password) < 6:
                                st.error("Password must be at least 6 characters.")
                                return
                            # Create user via Supabase Auth Admin API
                            auth_res = service_client.auth.admin.create_user({
                                "email": email.strip().lower(),
                                "password": password,
                                "email_confirm": True,
                            })
                            if auth_res.user:
                                target_auth_id = str(auth_res.user.id)
                            else:
                                st.error("Failed to create Auth user.")
                                return
                        else:
                            if not auth_user_id_override or len(auth_user_id_override.strip()) < 10:
                                st.error("Please supply the Auth User UUID from Supabase Auth Dashboard.")
                                return
                            target_auth_id = auth_user_id_override.strip()

                        # Insert admin profile
                        new_profile = admin_repo.create_profile(
                            auth_user_id=target_auth_id,
                            full_name=full_name,
                            email=email,
                            role=role,
                            department=department,
                            designation=designation,
                            created_by_auth_id=auth_user_id,
                        )

                        audit_service.log_action(
                            admin_auth_user_id=auth_user_id,
                            action="admin.created",
                            entity_type="admin_profile",
                            entity_id=new_profile.get("id"),
                            details=f"Admin {full_name} ({email}) provisioned with role {role}",
                        )
                        st.success(f"Administrator {full_name} created successfully!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed to provision administrator: {str(e)}")
