"""
storage_service.py - Attachment and File Access Service
Generates secure, short-lived signed URLs for grievance attachments.
Prevents exposure of private storage objects through permanent public URLs.
"""

from typing import Optional, Dict, Any
from supabase import Client

DEFAULT_BUCKET = "grievance-attachments"


class StorageService:
    def __init__(self, client: Client, bucket_name: str = DEFAULT_BUCKET):
        self.client = client
        self.bucket_name = bucket_name

    def create_signed_download_url(
        self,
        storage_path: str,
        expires_in_seconds: int = 300,
    ) -> Optional[str]:
        """
        Creates a short-lived signed download URL (valid for 5 minutes by default).
        """
        if not storage_path:
            return None

        try:
            # Strip bucket prefix if path includes bucket name
            clean_path = storage_path.replace(f"{self.bucket_name}/", "")
            res = self.client.storage.from_(self.bucket_name).create_signed_url(
                path=clean_path,
                expires_in=expires_in_seconds
            )
            if isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
            if hasattr(res, "signed_url"):
                return res.signed_url
            return None
        except Exception as e:
            print(f"[StorageService Warning] Could not generate signed URL: {str(e)}")
            return None
