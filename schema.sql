-- FunnelIQ: Pillar 2 - relational schema for funnel_marketing_data.csv
-- Run this once against the Supabase project's Postgres database
-- (Supabase Dashboard -> SQL Editor -> paste and run), or via the CLI:
--   psql "$DATABASE_URL" -f schema.sql

create table if not exists public.funnel_records (
    id                          bigserial primary key,
    ad_budget                   numeric(10, 2) not null,
    num_leads                   integer not null,
    leads_answered              integer not null,
    leads_not_answered          integer not null,
    followup_1                  integer not null default 0,
    followup_2                  integer not null default 0,
    followup_3                  integer not null default 0,
    followup_4                  integer not null default 0,
    followup_5                  integer not null default 0,
    not_closed                  integer not null default 0,
    closed                      integer not null default 0,
    calls_to_closed             integer,
    calls_to_not_closed         integer,
    customer_acquisition_cost   numeric(10, 2),
    ltv_months                  numeric(6, 2),
    purchased                   boolean not null default false,
    upsell                      boolean not null default false,
    cumulative_profit           numeric(12, 2),
    referred                    boolean not null default false,
    created_at                  timestamptz not null default now()
);

-- Indexes for the query patterns in the PRD's analytical work packages
-- (conversion analysis, budget tiers, upsell/referral classification).
create index if not exists idx_funnel_records_closed      on public.funnel_records (closed);
create index if not exists idx_funnel_records_upsell       on public.funnel_records (upsell);
create index if not exists idx_funnel_records_referred     on public.funnel_records (referred);
create index if not exists idx_funnel_records_ad_budget    on public.funnel_records (ad_budget);
create index if not exists idx_funnel_records_created_at   on public.funnel_records (created_at);

-- Row Level Security: only authenticated Supabase users (valid JWT) may
-- read or write. Anonymous requests are denied by default (no policy for
-- the `anon` role). The ingestion script uses the service_role key, which
-- bypasses RLS entirely, so it is unaffected by these policies.
alter table public.funnel_records enable row level security;

create policy "authenticated_select" on public.funnel_records
    for select
    to authenticated
    using (true);

create policy "authenticated_insert" on public.funnel_records
    for insert
    to authenticated
    with check (true);

create policy "authenticated_update" on public.funnel_records
    for update
    to authenticated
    using (true)
    with check (true);

create policy "authenticated_delete" on public.funnel_records
    for delete
    to authenticated
    using (true);
