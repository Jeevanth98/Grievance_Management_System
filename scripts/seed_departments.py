"""
Seed departmental administrators in Supabase Auth & admin_profiles
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from admin_portal.supabase_client import get_service_role_client

def seed():
    client = get_service_role_client()

    departments = [
        {
            "email": "hostel.dept@university.edu",
            "password": "Password123!",
            "full_name": "Hostel Affairs & Student Housing",
            "department": "Hostel & Residential Life",
            "designation": "Chief Warden Office",
            "role": "admin"
        },
        {
            "email": "academics.dept@university.edu",
            "password": "Password123!",
            "full_name": "Academic Affairs Department",
            "department": "Academic Affairs",
            "designation": "Dean of Academic Affairs",
            "role": "admin"
        },
        {
            "email": "exam.dept@university.edu",
            "password": "Password123!",
            "full_name": "Examination & Evaluation Cell",
            "department": "Examination & Evaluation",
            "designation": "Controller of Examinations",
            "role": "admin"
        },
        {
            "email": "finance.dept@university.edu",
            "password": "Password123!",
            "full_name": "Finance & Accounts Section",
            "department": "Finance & Accounts",
            "designation": "Finance Officer",
            "role": "admin"
        },
        {
            "email": "it.dept@university.edu",
            "password": "Password123!",
            "full_name": "IT & Systems Infrastructure",
            "department": "IT & Campus Infrastructure",
            "designation": "Head of IT Infrastructure",
            "role": "admin"
        },
        {
            "email": "transport.dept@university.edu",
            "password": "Password123!",
            "full_name": "Campus Transport Division",
            "department": "Campus Transport",
            "designation": "Transport Manager",
            "role": "admin"
        },
        {
            "email": "library.dept@university.edu",
            "password": "Password123!",
            "full_name": "Central Library Services",
            "department": "Library Services",
            "designation": "Chief Librarian",
            "role": "admin"
        },
        {
            "email": "discipline.dept@university.edu",
            "password": "Password123!",
            "full_name": "Student Welfare & Discipline Board",
            "department": "Student Affairs & Discipline",
            "designation": "Dean of Student Welfare",
            "role": "admin"
        },
        {
            "email": "estate.dept@university.edu",
            "password": "Password123!",
            "full_name": "Campus Infrastructure & Maintenance",
            "department": "Campus Infrastructure",
            "designation": "Estate Officer",
            "role": "admin"
        }
    ]

    auth_users = client.auth.admin.list_users()
    existing_emails = {u.email.lower(): u.id for u in auth_users if u.email}

    for d in departments:
        email = d["email"].lower()
        if email in existing_emails:
            auth_id = existing_emails[email]
            print(f"Auth user exists: {email} -> {auth_id}")
        else:
            created = client.auth.admin.create_user({
                "email": email,
                "password": d["password"],
                "email_confirm": True
            })
            auth_id = created.user.id
            print(f"Created auth user: {email} -> {auth_id}")

        # Check admin profile
        prof_res = client.table("admin_profiles").select("*").eq("auth_user_id", auth_id).execute()
        if not prof_res.data:
            ins = client.table("admin_profiles").insert({
                "auth_user_id": auth_id,
                "full_name": d["full_name"],
                "email": email,
                "role": d["role"],
                "department": d["department"],
                "designation": d["designation"],
                "is_active": True
            }).execute()
            print(f"Inserted profile for {d['department']}: {ins.data[0]['id']}")
        else:
            client.table("admin_profiles").update({
                "full_name": d["full_name"],
                "department": d["department"],
                "designation": d["designation"],
                "role": d["role"],
                "is_active": True
            }).eq("auth_user_id", auth_id).execute()
            print(f"Updated profile for {d['department']}")

if __name__ == "__main__":
    seed()
