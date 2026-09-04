"""Load funnel_marketing_data.csv into the Supabase Postgres `funnel_records` table.

Reproducible, non-interactive replacement for the Supabase Table Editor's manual
CSV import. Requires DATABASE_URL (see .env.example) to point at the project's
Postgres connection string, and schema.sql to have already been run.

Usage:
    python ingest_data.py                       # append rows from ./funnel_marketing_data.csv
    python ingest_data.py --truncate             # wipe the table first (safe to re-run)
    python ingest_data.py --csv path/to/file.csv --truncate
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

TABLE_NAME = "funnel_records"

COLUMN_ORDER = [
    "ad_budget",
    "num_leads",
    "leads_answered",
    "leads_not_answered",
    "followup_1",
    "followup_2",
    "followup_3",
    "followup_4",
    "followup_5",
    "not_closed",
    "closed",
    "calls_to_closed",
    "calls_to_not_closed",
    "customer_acquisition_cost",
    "ltv_months",
    "purchased",
    "upsell",
    "cumulative_profit",
    "referred",
]

YES_NO_TO_BOOL = {"Yes": True, "No": False}


def load_dataframe(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    missing = set(COLUMN_ORDER) - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing expected columns: {sorted(missing)}")

    df = df[COLUMN_ORDER].copy()
    df["purchased"] = df["purchased"].astype(bool)
    df["upsell"] = df["upsell"].astype(bool)
    df["referred"] = df["referred"].map(YES_NO_TO_BOOL)

    if df["referred"].isna().any():
        bad_rows = df.index[df["referred"].isna()].tolist()
        raise ValueError(f"Unexpected 'referred' values (want Yes/No) at rows: {bad_rows}")

    return df


def get_engine():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env, fill in the "
            "Supabase Postgres connection string, and re-run."
        )
    return create_engine(database_url)


def ingest(csv_path: str, truncate: bool) -> int:
    df = load_dataframe(csv_path)
    engine = get_engine()

    with engine.begin() as conn:
        if truncate:
            conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME} RESTART IDENTITY"))
        df.to_sql(TABLE_NAME, con=conn, if_exists="append", index=False, method="multi", chunksize=500)

    return len(df)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default="funnel_marketing_data.csv", help="Path to the source CSV file")
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Empty the table before loading, so the script is safely re-runnable",
    )
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"CSV not found at '{args.csv}'", file=sys.stderr)
        sys.exit(1)

    row_count = ingest(args.csv, args.truncate)
    print(f"Ingested {row_count} rows into '{TABLE_NAME}'.")


if __name__ == "__main__":
    main()
