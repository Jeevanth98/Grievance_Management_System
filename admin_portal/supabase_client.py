"""
supabase_client.py - Centralized Supabase Client Factory
Manages public anon client, authenticated user sessions, and isolated privileged client.
"""

from typing import Optional
from supabase import create_client, Client
from admin_portal.settings import settings


def get_supabase_client(access_token: Optional[str] = None) -> Client:
    """
    Returns an anonymous or user-authenticated Supabase client.
    If access_token is provided, sets the Authorization header so RLS policies
    identify the authenticated admin correctly using auth.uid().
    """
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    if access_token:
        # Set auth header for postgrest queries
        client.postgrest.auth(access_token)
    return client


def get_service_role_client() -> Optional[Client]:
    """
    Returns a service-role client for privileged backend-only operations
    (such as provisioning new auth users for admin profiles), if configured.
    WARNING: Never expose this to browser/client context.
    """
    service_key = settings.supabase_service_role_key
    if not service_key:
        return None
    return create_client(settings.supabase_url, service_key)
