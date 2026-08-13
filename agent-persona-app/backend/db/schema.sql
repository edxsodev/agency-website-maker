-- =========================================================
-- Agent/Agency Persona & Site-Regen App — Core Schema
-- Target: Supabase (Postgres)
-- =========================================================

create extension if not exists "uuid-ossp";

-- ---------------------------------------------------------
-- 1. Locations searched (so we cache discovery runs and
--    don't burn API quota re-searching the same area)
-- ---------------------------------------------------------
create table if not exists search_locations (
    id uuid primary key default uuid_generate_v4(),
    query text not null,              -- e.g. "Round Rock, TX"
    lat double precision,
    lng double precision,
    searched_at timestamptz not null default now(),
    result_count integer default 0
);

-- ---------------------------------------------------------
-- 2. Agencies (the core entity — one row per brokerage/agent)
-- ---------------------------------------------------------
create table if not exists agencies (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    website text,
    phone text,
    address text,
    city text,
    state text default 'TX',
    zip text,
    source text default 'manual',      -- 'manual' | 'google_places' | 'osm'
    place_id text,                     -- Google Place ID if from Places API
    location_id uuid references search_locations(id),
    google_maps_url text,
    rating numeric,
    review_count integer,
    raw_data jsonb,                    -- full API payload, kept for reprocessing
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (website)
);

create index if not exists idx_agencies_state on agencies (state);
create index if not exists idx_agencies_city on agencies (city);

-- ---------------------------------------------------------
-- 3. Scrapes — raw content pulled from an agency's site
--    (kept separate from agencies so we can re-scrape /
--    version content without touching the core record)
-- ---------------------------------------------------------
create table if not exists site_scrapes (
    id uuid primary key default uuid_generate_v4(),
    agency_id uuid not null references agencies(id) on delete cascade,
    url text not null,
    raw_markdown text,
    raw_html text,
    screenshot_url text,
    scraped_at timestamptz not null default now(),
    scrape_status text default 'pending'  -- pending | success | failed
);

create index if not exists idx_scrapes_agency on site_scrapes (agency_id);

-- ---------------------------------------------------------
-- 4. Personas — the generated 17-section KYC digital persona
--    Stored as structured JSONB so the frontend can render
--    section-by-section, plus a flattened markdown copy.
-- ---------------------------------------------------------
create table if not exists personas (
    id uuid primary key default uuid_generate_v4(),
    agency_id uuid not null references agencies(id) on delete cascade,
    scrape_id uuid references site_scrapes(id),
    sections jsonb not null,           -- {"identity_snapshot": {...}, "origin_story": {...}, ...}
    markdown text,                     -- rendered full document
    data_confidence text default 'low', -- low | medium | high — how much public data existed
    missing_sections text[],           -- e.g. ['competitor_landscape', 'thought_leadership_style']
    model_used text,                   -- e.g. 'llama-3.3-70b-versatile'
    generated_at timestamptz not null default now(),
    version integer default 1
);

create index if not exists idx_personas_agency on personas (agency_id);

-- ---------------------------------------------------------
-- 5. Generated sites — output of the Open-Lovable-style
--    website regeneration step
-- ---------------------------------------------------------
create table if not exists generated_sites (
    id uuid primary key default uuid_generate_v4(),
    agency_id uuid not null references agencies(id) on delete cascade,
    persona_id uuid references personas(id),
    source_scrape_id uuid references site_scrapes(id),
    framework text default 'react-vite',
    preview_url text,                  -- Vercel/Netlify preview link
    repo_url text,                     -- if pushed to GitHub
    generation_status text default 'pending', -- pending | generating | done | failed
    generation_log text,
    created_at timestamptz not null default now()
);

create index if not exists idx_sites_agency on generated_sites (agency_id);

-- ---------------------------------------------------------
-- 6. Job queue (simple — lets discovery/persona/site-gen
--    run as background jobs instead of blocking requests,
--    important since Vercel serverless functions time out)
-- ---------------------------------------------------------
create table if not exists jobs (
    id uuid primary key default uuid_generate_v4(),
    job_type text not null,            -- 'discovery' | 'persona' | 'site_gen'
    agency_id uuid references agencies(id),
    location_id uuid references search_locations(id),
    status text default 'queued',      -- queued | running | done | failed
    error text,
    created_at timestamptz not null default now(),
    started_at timestamptz,
    finished_at timestamptz
);

create index if not exists idx_jobs_status on jobs (status);

-- ---------------------------------------------------------
-- Trigger: keep agencies.updated_at fresh
-- ---------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_agencies_updated_at on agencies;
create trigger trg_agencies_updated_at
    before update on agencies
    for each row execute function set_updated_at();
