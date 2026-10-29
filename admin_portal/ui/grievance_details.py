"""
grievance_details.py - Detailed Grievance Management View
Features:
- Full overview with anonymity protection
- Dynamic status transition workflow
- Priority adjustment
- Staff assignment and reassignment
- Student-visible official discussion
- Strictly isolated internal admin review notes
- Attachment access with short-lived signed URLs
- Comprehensive status and assignment history timelines
"""

from typing import Dict, Any, Optional
import streamlit as st
from datetime import datetime
from admin_portal.grievance_repository import GrievanceRepository
from admin_portal.admin_repository import AdminRepository
from admin_portal.assignment_service import AssignmentService
from admin_portal.grievance_service import GrievanceService
from admin_portal.comment_service import CommentService
from admin_portal.note_service import InternalNoteService
from admin_portal.storage_service import StorageService
from admin_portal.constants import (
    STATUS_TRANSITION_MATRIX,
    VALID_PRIORITIES,
    PERMISSIONS,
    ROLE_SUPER_ADMIN,
)
from admin_portal.ui.components import (
    render_header_banner,
    get_status_badge_html,
    get_priority_badge_html,
)


def render_grievance_details(
    client,
    admin_profile: Dict[str, Any],
    auth_user_id: str,
    grievance_id: Optional[str] = None,
):
    """Renders the comprehensive grievance detail and action workspace."""
    if not grievance_id:
        st.warning("No grievance selected. Please select one from the Grievance Directory.")
        if st.button("← Back to Directory"):
            st.session_state["current_nav"] = "All Grievances"
            st.rerun()
        return

    repo = GrievanceRepository(client)
    admin_repo = AdminRepository(client)
    assign_service = AssignmentService(client)
    grievance_service = GrievanceService(client)
    comment_service = CommentService(client)
    note_service = InternalNoteService(client)
    storage_service = StorageService(client)

    # Back button
    col_nav, _ = st.columns([2, 8])
    with col_nav:
        if st.button("← Back to List"):
            st.session_state["current_nav"] = "All Grievances"
            st.rerun()

    # Load details
    with st.spinner("Fetching grievance record..."):
        try:
            g = repo.get_grievance_details(grievance_id)
        except Exception as e:
            st.error(f"Error loading grievance details: {str(e)}")
            return

    if not g:
        st.error(f"Grievance with ID '{grievance_id}' does not exist.")
        return

    ticket = g.get("ticket_number") or f"GRV-{g['id'][:8].upper()}"
    title = g.get("title", "Untitled")
    status = g.get("status", "submitted")
    priority = g.get("priority", "medium")
    is_anon = g.get("is_anonymous", False)
    category_name = g.get("category", {}).get("name") if g.get("category") else "General"
    created_at = g.get("created_at", "")[:19].replace("T", " ")
    admin_updated_at = g.get("admin_updated_at", "")[:19].replace("T", " ") if g.get("admin_updated_at") else "Not updated yet"

    render_header_banner(
        title=f"Ticket #{ticket}: {title}",
        subtitle=f"Category: {category_name} | Submitted: {created_at} UTC"
    )

    # Top Status & Metadata Bar
    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.markdown(f"**Current Status:** {get_status_badge_html(status)}", unsafe_allow_html=True)
    with col_meta2:
        st.markdown(f"**Priority:** {get_priority_badge_html(priority)}", unsafe_allow_html=True)
    with col_meta3:
        if is_anon:
            st.markdown("**Submitter:** <span class='anon-badge'>🕶️ Anonymous</span>", unsafe_allow_html=True)
        else:
            student = g.get("student")
            student_name = student.get("full_name") if student else "Registered Student"
            st.markdown(f"**Submitter:** {student_name}")
    with col_meta4:
        assigned = g.get("assigned_admin")
        if assigned:
            dept = assigned.get("department")
            desig = assigned.get("designation")
            if dept:
                display_assigned = f"🏛️ **{dept}**"
                if desig:
                    display_assigned += f"<br><small style='color: #64748B;'>{desig}</small>"
            else:
                display_assigned = f"👤 {assigned.get('full_name', 'Staff')}"
        else:
            display_assigned = "<span style='color: #E11D48; font-weight: 600;'>⚠️ Unassigned</span>"
        st.markdown(f"**Assigned Department:**<br>{display_assigned}", unsafe_allow_html=True)

    st.write("")

    # Main Grid: Left = Grievance Info & Tabs, Right = Action Control Panel
    col_content, col_actions = st.columns([7, 3])

    with col_content:
        # Grievance Description Card
        st.markdown("### 📝 Grievance Description")
        st.info(g.get("description", "No description provided."))

        # Submitter Details (if not anonymous)
        if not is_anon and g.get("student"):
            student = g["student"]
            with st.expander("👤 Student Profile Details", expanded=False):
                st.write(f"**Name:** {student.get('full_name')}")
                st.write(f"**Register Number:** {student.get('register_number')}")
                st.write(f"**Department:** {student.get('department')}")
                st.write(f"**Email:** {student.get('email')}")
                if student.get("phone_number"):
                    st.write(f"**Phone:** {student.get('phone_number')}")

        st.write("")

        # Operational Tabs
        tab_comments, tab_notes, tab_history, tab_attachments, tab_assignments = st.tabs([
            "💬 Official Discussion",
            "🔒 Internal Admin Notes",
            "📜 Status History",
            "📎 Attachments",
            "👥 Assignment Log",
        ])

        # TAB 1: Official Discussion
        with tab_comments:
            st.markdown("#### Official Grievance Discussion")
            st.caption("Responses posted here are visible to the student in their portal.")
            comments = g.get("comments", [])
            if comments:
                for c in comments:
                    role_badge = "👨‍💼 Administrator" if c.get("author_role") == "admin" else "🎓 Student"
                    c_date = c.get("created_at", "")[:19].replace("T", " ")
                    with st.chat_message("user" if c.get("author_role") == "student" else "assistant"):
                        st.markdown(f"**{role_badge}** • *{c_date} UTC*")
                        st.write(c.get("comment", ""))
            else:
                st.write("No official responses have been posted yet.")

            st.write("")
            acting_role = admin_profile.get("role", "")
            if PERMISSIONS.get(acting_role, {}).get("can_add_official_response", False):
                with st.form("form_official_comment", clear_on_submit=True):
                    new_comment = st.text_area("Post Official Response to Student", placeholder="Type response here...")
                    submit_comment = st.form_submit_button("Send Official Response")
                    if submit_comment:
                        success, err = comment_service.add_official_comment(
                            grievance_id=g["id"],
                            comment_text=new_comment,
                            acting_admin_profile=admin_profile,
                            acting_auth_user_id=auth_user_id,
                        )
                        if success:
                            st.success("Official response posted and student notified.")
                            st.rerun()
                        else:
                            st.error(f"Failed to post response: {err}")
            else:
                st.info("Your current role does not have permission to post official responses.")

        # TAB 2: Internal Admin Notes
        with tab_notes:
            st.markdown(
                """
                <div class="internal-note-box">
                    <strong>⚠️ CONFIDENTIAL ADMIN AREA:</strong> Notes in this section are visible ONLY to authorized administrators.
                    They are strictly isolated in the database and NEVER visible to students.
                </div>
                """,
                unsafe_allow_html=True,
            )
            acting_role = admin_profile.get("role", "")
            if PERMISSIONS.get(acting_role, {}).get("can_add_internal_notes", False):
                try:
                    notes = note_service.list_notes_for_grievance(g["id"], admin_profile)
                    if notes:
                        for n in notes:
                            author = n.get("author") or {}
                            auth_name = author.get("full_name", "Staff Member")
                            auth_role = author.get("role", "").replace("_", " ").title()
                            n_date = n.get("created_at", "")[:19].replace("T", " ")
                            st.markdown(f"**{auth_name}** ({auth_role}) — *{n_date} UTC*")
                            st.markdown(f"> {n.get('note')}")
                            st.write("---")
                    else:
                        st.write("No internal notes recorded yet.")

                    # Add new note form
                    with st.form("form_internal_note", clear_on_submit=True):
                        new_note_text = st.text_area("Add Private Staff Note", placeholder="Internal observations, cross-department investigation findings...")
                        submit_note = st.form_submit_button("Save Internal Note")
                        if submit_note:
                            ok, err_msg = note_service.add_note(
                                grievance_id=g["id"],
                                note_text=new_note_text,
                                acting_admin_profile=admin_profile,
                                acting_auth_user_id=auth_user_id,
                            )
                            if ok:
                                st.success("Internal note recorded securely.")
                                st.rerun()
                            else:
                                st.error(f"Failed: {err_msg}")
                except Exception as e:
                    st.error(f"Error accessing internal notes: {str(e)}")
            else:
                st.warning("Your role does not have authorization to view internal notes.")

        # TAB 3: Status History
        with tab_history:
            st.markdown("#### Status Transition History")
            history = g.get("status_history", [])
            if history:
                for h in history:
                    old_s = (h.get("old_status") or "initial").replace("_", " ").title()
                    new_s = (h.get("new_status") or "").replace("_", " ").title()
                    h_date = h.get("created_at", "")[:19].replace("T", " ")
                    reason = h.get("change_reason") or "No reason provided"
                    st.markdown(f"• **{old_s} → {new_s}** on *{h_date} UTC*")
                    st.caption(f"Reason: {reason}")
            else:
                st.write("No status changes recorded yet.")

        # TAB 4: Attachments
        with tab_attachments:
            st.markdown("#### Evidence & Supporting Attachments")
            attachments = g.get("attachments", [])
            if attachments:
                for att in attachments:
                    file_name = att.get("file_name", "Attachment")
                    size_kb = (att.get("file_size") or 0) / 1024
                    storage_path = att.get("storage_path")
                    att_col1, att_col2 = st.columns([7, 3])
                    with att_col1:
                        st.write(f"📄 **{file_name}** ({size_kb:.1f} KB)")
                    with att_col2:
                        if st.button("Generate Download Link", key=f"att_btn_{att.get('id')}"):
                            signed_url = storage_service.create_signed_download_url(storage_path)
                            if signed_url:
                                st.markdown(f"[📥 Open/Download File]({signed_url})")
                            else:
                                st.error("Could not generate secure download URL.")
            else:
                st.write("No files were attached with this submission.")

        # TAB 5: Assignment Log
        with tab_assignments:
            st.markdown("#### Assignment Audit Log")
            assignments = g.get("assignments", [])
            if assignments:
                for asg in assignments:
                    adm_id = asg.get("assigned_admin_id")
                    adm_rec = admin_repo.get_by_id(adm_id) if adm_id else None
                    if adm_rec:
                        dept = adm_rec.get("department")
                        desig = adm_rec.get("designation")
                        if dept:
                            adm_name = f"🏛️ {dept} ({desig or adm_rec.get('full_name')})"
                        else:
                            adm_name = adm_rec.get("full_name", "Staff")
                    else:
                        adm_name = "Unknown Department/Officer"

                    assigned_at = asg.get("assigned_at", "")[:19].replace("T", " ")
                    unassigned_at = asg.get("unassigned_at", "")[:19].replace("T", " ") if asg.get("unassigned_at") else "Currently Active"
                    note = asg.get("assignment_note") or "None"
                    st.markdown(f"**Assigned Department / Staff:** {adm_name}")
                    st.caption(f"Period: {assigned_at} to {unassigned_at} | Note: {note}")
                    st.write("---")
            else:
                st.write("No historical assignment records.")

    # Right Action Control Panel
    with col_actions:
        st.markdown("### ⚙️ Administrative Actions")

        # 1. Assignment Action Card (Departmental Assignment)
        acting_role = admin_profile.get("role", "")
        if PERMISSIONS.get(acting_role, {}).get("can_assign", False):
            with st.container():
                st.markdown("#### 🏛️ Assign to Department")
                active_admins = admin_repo.list_all(active_only=True)

                # Filter out pure System Administrator / general super-admin records without specific department
                dept_admins = [
                    a for a in active_admins
                    if a.get("department")
                    and a.get("department") not in ["Administration", "Administrative Affairs"]
                    and "System Admin" not in a.get("full_name", "")
                ]
                assignment_candidates = dept_admins if dept_admins else active_admins

                # Build clean department choices
                dept_choices = {}
                for a in assignment_candidates:
                    dept = a.get("department")
                    desig = a.get("designation")
                    if dept and desig:
                        label = f"🏢 {dept} — {desig}"
                    elif dept:
                        label = f"🏢 {dept} — {a['full_name']}"
                    else:
                        label = f"👤 {a['full_name']} ({a['role']})"
                    dept_choices[label] = a["id"]

                current_assigned_id = g.get("assigned_admin_id")
                default_idx = 0
                found_current = False

                # If already assigned, select current department
                if current_assigned_id:
                    for idx, aid in enumerate(dept_choices.values()):
                        if aid == current_assigned_id:
                            default_idx = idx
                            found_current = True
                            break

                # If unassigned, auto-match department with grievance category
                if not found_current and category_name:
                    cat_lower = category_name.lower()
                    for idx, a in enumerate(assignment_candidates):
                        dept_lower = (a.get("department") or "").lower()
                        if (
                            cat_lower in dept_lower
                            or dept_lower in cat_lower
                            or ("hostel" in cat_lower and "hostel" in dept_lower)
                            or ("exam" in cat_lower and "exam" in dept_lower)
                            or ("academic" in cat_lower and "academic" in dept_lower)
                            or ("faculty" in cat_lower and "academic" in dept_lower)
                            or ("fee" in cat_lower and "finance" in dept_lower)
                            or ("finance" in cat_lower and "finance" in dept_lower)
                            or ("transport" in cat_lower and "transport" in dept_lower)
                            or ("library" in cat_lower and "library" in dept_lower)
                            or ("it" in cat_lower and "it" in dept_lower)
                            or ("technical" in cat_lower and "it" in dept_lower)
                            or ("discipline" in cat_lower and "discipline" in dept_lower)
                            or ("harassment" in cat_lower and "discipline" in dept_lower)
                            or ("infrastructure" in cat_lower and "infrastructure" in dept_lower)
                        ):
                            default_idx = idx
                            break

                selected_target_label = st.selectbox(
                    "Select Department to Assign",
                    options=list(dept_choices.keys()),
                    index=default_idx if dept_choices else 0,
                    help="Select the university department responsible for investigating and resolving this grievance.",
                )
                target_admin_id = dept_choices.get(selected_target_label) if dept_choices else None
                assignment_note = st.text_input(
                    "Routing / Investigation Note (Optional)",
                    placeholder="e.g. Please inspect hostel block 4 plumbing logs urgently",
                )

                if st.button("Confirm Department Assignment", use_container_width=True):
                    if target_admin_id:
                        ok, err = assign_service.assign_grievance(
                            grievance_id=g["id"],
                            target_admin_profile_id=target_admin_id,
                            acting_admin_profile=admin_profile,
                            acting_auth_user_id=auth_user_id,
                            assignment_note=assignment_note,
                        )
                        if ok:
                            st.success("Grievance assigned successfully!")
                            st.rerun()
                        else:
                            st.error(f"Assignment failed: {err}")

        st.markdown("---")

        # 2. Status Transition Card
        if PERMISSIONS.get(acting_role, {}).get("can_update_status", False):
            with st.container():
                st.markdown("#### 🔄 Update Grievance Status")
                allowed_transitions = list(STATUS_TRANSITION_MATRIX.get(status, set()))
                if acting_role == ROLE_SUPER_ADMIN:
                    # Super admin can perform any transition if needed
                    from admin_portal.constants import VALID_STATUSES
                    transition_options = [s for s in VALID_STATUSES if s != status]
                else:
                    transition_options = allowed_transitions

                if transition_options:
                    formatted_options = {s.replace("_", " ").title(): s for s in transition_options}
                    chosen_target = st.selectbox("Next Status", list(formatted_options.keys()))
                    next_status_val = formatted_options[chosen_target]
                    change_reason = st.text_input("Status Change Reason", placeholder="e.g. Resolution verified by department head")

                    if st.button("Apply Status Change", use_container_width=True):
                        ok, err = grievance_service.update_status(
                            grievance_id=g["id"],
                            new_status=next_status_val,
                            change_reason=change_reason,
                            acting_admin_profile=admin_profile,
                            acting_auth_user_id=auth_user_id,
                        )
                        if ok:
                            st.success(f"Status changed to {chosen_target}!")
                            st.rerun()
                        else:
                            st.error(f"Transition error: {err}")
                else:
                    st.info(f"No further transitions permitted from status '{status}'.")

        st.markdown("---")

        # 3. Priority Adjustment Card
        if PERMISSIONS.get(acting_role, {}).get("can_change_priority", False):
            with st.container():
                st.markdown("#### ⚡ Adjust Priority")
                prio_idx = VALID_PRIORITIES.index(priority) if priority in VALID_PRIORITIES else 1
                new_prio_label = st.selectbox(
                    "Priority Level",
                    [p.title() for p in VALID_PRIORITIES],
                    index=prio_idx,
                )
                new_prio_val = new_prio_label.lower()
                if new_prio_val != priority:
                    if st.button("Update Priority", use_container_width=True):
                        ok, err = grievance_service.update_priority(
                            grievance_id=g["id"],
                            new_priority=new_prio_val,
                            acting_admin_profile=admin_profile,
                            acting_auth_user_id=auth_user_id,
                        )
                        if ok:
                            st.success("Priority updated successfully!")
                            st.rerun()
                        else:
                            st.error(f"Priority error: {err}")
