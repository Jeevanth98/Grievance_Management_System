"""
settings.py - Centralized Configuration Management
Reads configuration from st.secrets, .env file, or environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Try importing streamlit for secrets access
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Load local .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    """Application configuration settings."""

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Fetch a setting from st.secrets first, then environment variables."""
        if HAS_STREAMLIT:
            try:
                # Check top-level or sections in st.secrets
                if key in st.secrets:
                    return str(st.secrets[key])
                if "supabase" in st.secrets and key in st.secrets["supabase"]:
                    return str(st.secrets["supabase"][key])
            except Exception:
                pass
        return os.environ.get(key, default)

    @property
    def supabase_url(self) -> str:
        url = self.get("SUPABASE_URL")
        if not url or url.startswith("https://your-project-id"):
            raise ValueError(
                "SUPABASE_URL is not configured. Please set SUPABASE_URL in .env or .streamlit/secrets.toml"
            )
        return url.strip().rstrip("/")

    @property
    def supabase_anon_key(self) -> str:
        key = self.get("SUPABASE_ANON_KEY")
        if not key or key.startswith("your-supabase-anon"):
            raise ValueError(
                "SUPABASE_ANON_KEY is not configured. Please set SUPABASE_ANON_KEY in .env or .streamlit/secrets.toml"
            )
        return key.strip()

    @property
    def supabase_service_role_key(self) -> Optional[str]:
        key = self.get("SUPABASE_SERVICE_ROLE_KEY")
        if key and not key.startswith("your-supabase-service"):
            return key.strip()
        return None

    @property
    def app_name(self) -> str:
        return self.get("APP_NAME", "Student Grievance Management - Admin Portal")

    @property
    def app_env(self) -> str:
        return self.get("APP_ENV", "development")

    @property
    def is_configured(self) -> bool:
        """Check if mandatory settings are set without throwing exception."""
        try:
            _ = self.supabase_url
            _ = self.supabase_anon_key
            return True
        except ValueError:
            return False


settings = Settings()
