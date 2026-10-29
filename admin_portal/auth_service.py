"""
auth_service.py - Authentication and Admin Authorization Service
Handles sign-in via Supabase Auth, active-admin validation, session management, and logout.
"""

from typing import Optional, Dict, Any, Tuple
from supabase import Client
from admin_portal.supabase_client import get_supabase_client
from admin_portal.admin_repository import AdminRepository


class AuthService:
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()
        self.admin_repo = AdminRepository(self.client)

    def sign_in(self, email: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticates user with Supabase Auth and strictly verifies admin authorization.
        Returns:
            (success: bool, error_message: Optional[str], admin_profile: Optional[dict], access_token: Optional[str])
        """
        email = email.strip()
        if not email or not password:
            return False, "Email and password are required.", None, None

        try:
            # 1. Supabase Auth sign-in
            auth_response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            user = auth_response.user
            session = auth_response.session

            if not user or not session:
                return False, "Authentication failed. Please verify your credentials.", None, None

            auth_user_id = str(user.id)
            access_token = session.access_token

            # 2. Check admin profile existence
            profile = None
            try:
                from admin_portal.settings import settings
                if settings.is_configured:
                    auth_client = get_supabase_client(access_token=access_token)
                    admin_repo = AdminRepository(auth_client)
                    profile = admin_repo.get_by_auth_user_id(auth_user_id)
            except Exception:
                pass

            # Fallback to current client
            if not profile:
                profile = self.admin_repo.get_by_auth_user_id(auth_user_id)

            # 3. Reject if no admin profile found (e.g., student account)
            if not profile:
                # Log out of Supabase auth session immediately
                try:
                    self.client.auth.sign_out()
                except Exception:
                    pass
                return (
                    False,
                    "Access Denied: This account is not registered as an administrator. Students must use the Student Portal.",
                    None,
                    None,
                )

            # 4. Reject inactive admin
            if not profile.get("is_active", False):
                try:
                    self.client.auth.sign_out()
                except Exception:
                    pass
                return (
                    False,
                    "Account Suspended: Your administrator account is deactivated. Please contact a Super Administrator.",
                    None,
                    None,
                )

            return True, None, profile, access_token

        except Exception as e:
            err_str = str(e).lower()
            if "invalid login credentials" in err_str or "invalid_grant" in err_str:
                return False, "Invalid email or password.", None, None
            if "email not confirmed" in err_str:
                return False, "Email address has not been confirmed. Please check your inbox.", None, None
            return False, f"Authentication error: {str(e)}", None, None

    def sign_out(self) -> None:
        """Terminates the Supabase session."""
        try:
            self.client.auth.sign_out()
        except Exception:
            pass
