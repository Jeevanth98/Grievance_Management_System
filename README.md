# Grievance Management System — Admin Portal

An enterprise-grade, secure administrative portal for the University Student Grievance Redressal System built with **Python 3.11+**, **Streamlit**, and **Supabase (PostgreSQL & Auth)**.

---

## 1. Project Overview & Architecture

The **Admin Portal** interfaces directly with the shared Supabase backend to enable administrative staff to triage, prioritize, assign, investigate, resolve, and audit student grievances. 

### Core Architectural Layers

```
Grievance_management_System/
├── admin_portal/
│   ├── app.py                   # Main Streamlit application entry point
│   ├── settings.py              # Centralized environment & secrets configuration
│   ├── supabase_client.py       # Client factory supporting authenticated user JWT sessions
│   ├── constants.py             # Enums, transition matrix, role permissions, badge styles
│   ├── auth_service.py          # Supabase Auth sign-in & active admin verification
│   ├── admin_repository.py      # Admin profiles data access layer (id vs auth_user_id separation)
│   ├── grievance_repository.py  # Real database metrics, pagination, multi-filtering, details
│   ├── assignment_service.py    # Assignment lifecycle, unassign tracking, student notifications
│   ├── grievance_service.py     # Status transition enforcement, timestamps, audit trails
│   ├── comment_service.py       # Student-visible official responses
│   ├── note_service.py          # Confidential internal staff notes (isolated from students)
│   ├── storage_service.py       # Short-lived signed download URLs for private attachments
│   ├── notification_service.py  # Student notification dispatcher
│   ├── audit_service.py         # Administrative audit logging
│   └── ui/
│       ├── styles.py            # Custom CSS styling tokens & layout rules
│       ├── components.py        # Reusable metric cards, badges, empty states
│       ├── dashboard.py         # Live analytics, status/priority breakdown charts
│       ├── grievance_list.py    # Multi-filter search (status, category, admin, dates)
│       ├── grievance_details.py # Comprehensive detail view, workflow tabs & action cards
│       ├── admin_management.py  # Super-admin staff management & provisioning
│       ├── audit_logs.py        # Filterable security & operation audit logs
│       └── settings_page.py     # Session health, profile details, and database ping
├── tests/
│   ├── conftest.py              # Pytest mock Supabase client & fixtures
│   ├── test_auth.py             # Login, student rejection, inactive rejection tests
│   ├── test_authorization.py    # RBAC boundary enforcement tests
│   ├── test_grievances.py       # Search, pagination, filter, detail loading tests
│   ├── test_assignments.py      # Assignment & reassignment lifecycle tests
│   ├── test_status_transitions.py # Transition matrix & timestamp tests
│   ├── test_internal_notes.py   # Staff note creation & validation tests
│   └── test_audit_logs.py       # Audit trail generation & filter tests
├── sql/
│   └── 01_initial_schema.sql    # Schema reference for core tables
├── .env.example                 # Environment configuration template
├── .streamlit/
│   └── config.toml              # Streamlit server & theme configuration
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```

---

## 2. Database Schema & Relationships

The admin portal operates against the following Supabase tables:

| Table | Purpose | Key Relationships |
| :--- | :--- | :--- |
| `public.students` | Student profiles | `auth_user_id` references `auth.users(id)` |
| `public.grievance_categories` | Categories (Hostel, Academics, etc.) | Referenced by `grievances.category_id` |
| `public.grievances` | Canonical grievance records | `student_auth_user_id` references `auth.users(id)`, `assigned_admin_id` references `admin_profiles.id` |
| `public.grievance_status_history` | Audit trail of status changes | `grievance_id` references `grievances.id` |
| `public.grievance_comments` | Official student-visible responses | `author_user_id` references `auth.users(id)`, `author_role` = `'admin'` or `'student'` |
| `public.grievance_attachments` | Uploaded evidence files | `grievance_id` references `grievances.id` |
| `public.notifications` | Student-facing alerts | `student_auth_user_id` references `auth.users(id)` |
| `public.admin_profiles` | Administrator profiles & roles | `auth_user_id` references `auth.users(id)` |
| `public.grievance_assignments` | Historical log of staff assignments | `grievance_id` references `grievances.id`, `assigned_admin_id` references `admin_profiles.id` |
| `public.grievance_internal_notes`| Confidential staff review notes | `author_admin_id` references `admin_profiles.id` (**Strictly hidden from students**) |
| `public.admin_audit_logs` | Immutable administrative audit trails | `admin_auth_user_id` references `auth.users(id)` |

---

## 3. Role-Based Access Control (RBAC)

| Capability | `super_admin` | `admin` | `reviewer` |
| :--- | :---: | :---: | :---: |
| **View Dashboard & Metrics** | ✅ | ✅ | ✅ |
| **View Grievance Directory** | ✅ | ✅ | ✅ |
| **Assign / Reassign Grievances** | ✅ | ✅ | ❌ |
| **Change Grievance Priority** | ✅ | ✅ | ❌ |
| **Update Grievance Status** | ✅ | ✅ | ✅ *(Workflow)* |
| **Post Official Responses to Students** | ✅ | ✅ | ❌ |
| **Add & Inspect Private Internal Notes** | ✅ | ✅ | ✅ |
| **View Audit Logs** | ✅ | ✅ | ❌ |
| **Manage & Provision Staff Accounts** | ✅ | ❌ | ❌ |

---

## 4. Status Transition Matrix

To prevent arbitrary status corruption, status transitions follow this controlled state machine:

```
[submitted] ──────► [under_review] ──────► [assigned] ──────► [in_progress] ──────► [resolved] ──────► [closed]
     │                    │                                         │                     │                ▲
     └────────────────────┴─────────────────────────────────────────┴─────────────────────┼────────────────┘
                          ▼                                                               ▼
                     [rejected] ───────────────────────────────────────────────────► [reopened]
```

- When status reaches **`resolved`**, `resolved_at` is automatically recorded.
- When status reaches **`closed`**, `closed_at` is automatically recorded.
- Only authorized roles can reopen closed or rejected grievances.

---

## 5. Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` (or configure `.streamlit/secrets.toml`):

```bash
cp .env.example .env
```

Edit `.env`:
```ini
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_ANON_KEY="your-anon-publishable-key"

# Optional: Needed only if you wish to auto-provision Auth users from the Admin Management UI
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

---

## 6. Safe Provisioning of the First Super-Admin

To initialize the portal securely without public registration:

### Option A: Via Supabase SQL Editor (Recommended)
1. Go to **Supabase Dashboard** > **Authentication** > **Users** > **Add User** (Create User with email e.g. `admin@university.edu` and a strong password).
2. Copy the generated User UID (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`).
3. Open the **SQL Editor** in Supabase and run:

```sql
INSERT INTO public.admin_profiles (
    auth_user_id,
    full_name,
    email,
    role,
    department,
    designation,
    is_active
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890', -- Replace with the UID from Step 2
    'Chief System Administrator',
    'admin@university.edu',
    'super_admin',
    'Information Technology',
    'System Administrator',
    true
);
```

### Option B: Automatic Provisioning
If `SUPABASE_SERVICE_ROLE_KEY` is provided in `.env`, the Super Administrator can provision subsequent staff accounts directly from the **Admin Management** page in the UI.

---

## 7. Running the Application

Launch the Streamlit Admin Portal:

```bash
# On Windows PowerShell:
$env:PYTHONIOENCODING="utf-8"
streamlit run admin_portal/app.py

# On Linux / macOS:
streamlit run admin_portal/app.py
```

The application will start on `http://localhost:8501`.

---

## 8. Running Automated Tests

All business logic, authentication rules, role-based access checks, assignment workflows, transition matrices, and audit logging are fully tested using unit tests with mock state machines (no production credentials required):

```bash
python -m pytest tests/ -v
```

Output:
```
tests/test_assignments.py::test_assign_unassigned_grievance PASSED
tests/test_assignments.py::test_reject_assignment_to_inactive_admin PASSED
tests/test_audit_logs.py::test_audit_log_written_on_priority_update PASSED
tests/test_audit_logs.py::test_list_audit_logs_with_filter PASSED
tests/test_auth.py::test_admin_sign_in_success PASSED
tests/test_auth.py::test_student_rejected_from_admin_portal PASSED
tests/test_auth.py::test_inactive_admin_rejected PASSED
tests/test_auth.py::test_blank_credentials_rejected PASSED
tests/test_authorization.py::test_reviewer_cannot_assign_grievance PASSED
tests/test_authorization.py::test_reviewer_cannot_change_priority PASSED
tests/test_authorization.py::test_reviewer_cannot_post_official_comment PASSED
tests/test_authorization.py::test_super_admin_has_full_permissions PASSED
tests/test_grievances.py::test_dashboard_metrics_aggregation PASSED
tests/test_grievances.py::test_list_grievances_and_filters PASSED
tests/test_grievances.py::test_grievance_details_retrieval PASSED
tests/test_grievances.py::test_invalid_grievance_id PASSED
tests/test_internal_notes.py::test_add_internal_note_success PASSED
tests/test_internal_notes.py::test_blank_internal_note_rejected PASSED
tests/test_status_transitions.py::test_valid_status_transition PASSED
tests/test_status_transitions.py::test_invalid_status_transition_rejected PASSED
tests/test_status_transitions.py::test_resolution_sets_resolved_at PASSED
============================= 21 passed in 0.64s ==============================
```

---

## 9. Security & Privacy Guarantees

1. **Active Admin Verification:** A successful password check in Supabase Auth is not sufficient. The user's UUID must be present in `admin_profiles` with `is_active = true`. Student accounts attempting to sign in are immediately logged out and rejected.
2. **Internal Notes Isolation:** `grievance_internal_notes` is accessed solely by authenticated admin roles and is never queried or exposed in student contexts.
3. **Anonymity Protection:** When a grievance has `is_anonymous = true`, student profile fields (`full_name`, `register_number`, `email`) are masked from view.
4. **Credential Safety:** The `SUPABASE_SERVICE_ROLE_KEY` is completely optional and never passed into browser-rendered code or frontend state. Public anon keys are used with user access tokens.
5. **Private Attachments:** Private storage objects are never exposed via permanent URLs; short-lived signed URLs (5-minute expiration) are generated on-demand.
