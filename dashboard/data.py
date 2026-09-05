"""Load funnel data from Supabase for the dashboard (not the local CSV).

Queries `funnel_records` using the signed-in user's own JWT via the public
anon key client - Row Level Security applies exactly as it would for any
other authenticated client (only the `authenticated` role can read; see
schema.sql). No service_role key here, per Pillar 2's key-separation rule.
"""

from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

from analysis.data_cleaning import CleaningReport, clean

load_dotenv()

PAGE_SIZE = 1000


def get_authenticated_client(access_token: str) -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    client = create_client(url, anon_key)
    client.postgrest.auth(access_token)
    return client


def fetch_funnel_records(client: Client) -> pd.DataFrame:
    rows: list[dict] = []
    start = 0
    while True:
        response = client.table("funnel_records").select("*").range(start, start + PAGE_SIZE - 1).execute()
        batch = response.data
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE

    df = pd.DataFrame(rows)
    # `id`/`created_at` are DB-only metadata, not part of the original
    # dataset - drop them so duplicate rows (which get distinct ids and
    # timestamps) are still detected the same way analysis/data_cleaning.py
    # detects them when reading the raw CSV directly.
    return df.drop(columns=["id", "created_at"], errors="ignore")


def load_clean_funnel_data(access_token: str) -> tuple[pd.DataFrame, CleaningReport]:
    client = get_authenticated_client(access_token)
    raw = fetch_funnel_records(client)
    return clean(raw)
