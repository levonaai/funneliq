# FunnelIQ

FunnelIQ turns raw marketing and sales data from **Northbound Media**
(`funnel_marketing_data.csv`, ~3,500 records) into a deployed, secure,
production-ready Business Intelligence tool.

The full project spans three infrastructure pillars and six analytical work
packages (see `INSTRUCTIONS.md` for the complete PRD). **This repository
currently has Pillars 1-3 scaffolded**: version control + CI (Pillar 1), a
Supabase schema/RLS/ingestion pipeline and backend JWT verification
(Pillar 2), and Railway deployment config (Pillar 3). The dashboard, login
UI, and the six ML/analytics work packages are not built yet.

## Architecture (planned)

```mermaid
flowchart LR
    U[User] --> D[Streamlit Dashboard]
    D --> A[FastAPI Backend]
    A --> S[(Supabase Postgres)]
    A --> M[Gradient Boosting Models]
    D -. Supabase Auth .-> S
    subgraph Railway [Railway - Cloud Deployment]
        D
        A
    end
    subgraph CI [GitHub Actions]
        L[Lint - ruff] --> T[Test - pytest]
    end
```

The dashboard and ML models are still planned; everything else in the
diagram (CI, backend, Postgres, auth, Railway) is wired up.

## Live app

Coming once Railway is connected to this repo (see Pillar 3 setup below) —
add the URL here once deployed.

## Pillar 2 setup: Supabase (database & auth)

1. Create a project at [supabase.com](https://supabase.com).
2. Copy `.env.example` to `.env` and fill in the values from
   **Project Settings -> API** (`SUPABASE_URL`, `SUPABASE_ANON_KEY`,
   `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`) and
   **Project Settings -> Database -> Connection string -> URI**
   (`DATABASE_URL`). Never commit `.env`.
3. Apply the schema (creates the `funnel_records` table, indexes, and RLS
   policies): open the Supabase SQL Editor and run `schema.sql`, or via CLI:
   ```bash
   psql "$DATABASE_URL" -f schema.sql
   ```
4. Load the dataset (reproducible, no manual UI upload):
   ```bash
   pip install -r requirements.txt
   python ingest_data.py --truncate
   ```
   `--truncate` empties the table first so the script is safely re-runnable.
5. In **Authentication -> Providers**, Email/Password is enabled by default —
   create a test user there (or via the Supabase Auth UI) to obtain a JWT for
   testing the protected API route below.

**Key separation:** only the `anon` key is meant for a frontend/dashboard;
the `service_role` key bypasses Row Level Security and must stay backend-only
(loaded via `app/db.py`, never sent to the browser).

## Running the backend locally

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
# GET  http://127.0.0.1:8000/         -> {"message": "Hello from FunnelIQ"}
# GET  http://127.0.0.1:8000/health   -> {"status": "ok"}
# GET  http://127.0.0.1:8000/api/me   -> requires Authorization: Bearer <supabase-jwt>
```

`/api/me` verifies the Supabase-issued JWT (HS256, signed with
`SUPABASE_JWT_SECRET`) and returns the decoded user id/email — a template for
further protected routes.

## Pillar 3 setup: Railway (cloud deployment)

1. On [railway.app](https://railway.app), create a new project ->
   **Deploy from GitHub repo** -> select `levonaai/funneliq` -> pick `main`
   as the deploy branch (merge the open PRs into `main` first).
2. Railway auto-detects the Python app via `requirements.txt` and uses the
   `Procfile` (`web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`) as the
   start command. No Dockerfile needed.
3. In the service's **Variables** tab, set every key from `.env.example`
   (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
   `SUPABASE_JWT_SECRET`, `DATABASE_URL`) as environment variables — never
   commit real values to the repo. `PORT` is injected automatically; don't
   set it manually.
4. Under **Settings -> Networking**, click **Generate Domain** to get a
   public `*.up.railway.app` URL (services aren't publicly reachable until
   you do this).
5. Under **Settings -> Source**, confirm **Auto Deploy** is on for the
   branch you picked in step 1 — every push to it now triggers a redeploy.
6. Verify it's live: `curl https://<your-app>.up.railway.app/health` should
   return `{"status": "ok"}`.
7. Verify it survives a restart: in the Railway dashboard, use the service's
   **Restart** action (or trigger a redeploy), then re-run the same `curl`
   against `/health` once it's back up — it should return the same
   `{"status": "ok"}` with no manual intervention.
8. Update the **Live app** link above with the generated URL.

## Development

```bash
ruff check .   # lint
pytest         # tests
```

Both run automatically via GitHub Actions on every push and pull request
(see `.github/workflows/ci.yml`).

## Project roadmap

- **Pillar 1 — Version Control & Automation (GitHub):** this repo, branch/PR
  workflow, `.gitignore`, CI lint + test. ✅
- **Pillar 2 — Database & Authentication (Supabase):** schema, RLS,
  ingestion script, backend JWT verification. ✅ scaffolded — needs a live
  Supabase project + a frontend login UI (tracked with the dashboard work).
- **Pillar 3 — Cloud Deployment (Railway):** `Procfile`, env var contract,
  `/health` endpoint. ✅ scaffolded — needs the Railway project connected.
- **Work Packages 1-6:** EDA, LTV regression, upsell classification,
  super-customer scoring, follow-up funnel analysis, budget optimization
  simulator (see `INSTRUCTIONS.md`).

## Security

Raw data files (`*.csv`), `.env` files, and API keys are excluded via
`.gitignore` and must never be committed. `.env.example` documents the
required variable names without real values. The backend never exposes the
`service_role` key; only the `anon` key is safe to ship to a frontend.
