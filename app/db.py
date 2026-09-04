from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_service_client() -> Client:
    """Admin Supabase client using the SERVICE_ROLE key.

    Backend-only: this key bypasses Row Level Security and must never be sent
    to the frontend. The frontend/dashboard uses the public anon key instead.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not configured.")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
