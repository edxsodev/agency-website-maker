# Texas Agent Persona & Site-Gen App — Backend Skeleton

## What's here

```
backend/
├── main.py                  FastAPI app, wires up all 3 routers
├── models.py                Pydantic schemas (Agency, Persona, GeneratedSite, Job)
├── persona_prompt.py        Your 17-section prompt, adapted for JSON output + graceful degradation
├── requirements.txt
├── .env.example
├── db/
│   ├── schema.sql            Full Postgres schema — run this in Supabase's SQL editor
│   ├── client.py              Supabase client singleton
│   └── seed_data.py          Inserts your 5 real agencies
└── routers/
    ├── discovery.py          Location -> agency list (stubbed, works against seeded DB now)
    ├── persona.py             Scrape -> 17-section persona (raises NotImplementedError until wired)
    └── site_gen.py            Persona + old site -> regenerated site (enqueues a job; async by design)
```

## Setup

1. Create a free Supabase project.
2. Run `db/schema.sql` in the Supabase SQL editor.
3. Copy `.env.example` to `.env`, fill in `SUPABASE_URL` / `SUPABASE_KEY`.
4. `pip install -r requirements.txt`
5. `python -m db.seed_data` — loads your 5 agencies.
6. `uvicorn main:app --reload` — API live at `http://localhost:8000`.
7. Hit `POST /discovery` with `{"location": "Round Rock"}` — you should get Realty Texas back.

## What works right now

- Full schema, deployed and seedable.
- `/discovery` — returns real seeded agencies today (text-matches on address); ready to swap in
  Google Places without changing the response shape.
- `/persona/{agency_id}` and `/site-gen/{agency_id}` — GET endpoints work once data exists.
- `POST /persona/generate` and `POST /site-gen/enqueue` — routes and DB writes are real; the two
  functions they call (`_scrape_site`, `_call_groq`) intentionally raise `NotImplementedError` as
  placeholders so it's obvious where the next module's logic goes.

## Suggested build order from here

1. **Discovery real data**: swap the stub in `discovery.py` for a Google Places Text Search + Place
   Details call. Free up to $200/mo Google Cloud credit.
2. **Persona generation**: wire `_scrape_site` (Firecrawl free tier) and `_call_groq` (Groq free
   tier, `llama-3.3-70b-versatile`) in `persona.py`.
3. **Site generation**: the heaviest module — needs a background worker (not a request/response
   endpoint) since generation takes minutes, same timeout problem you hit on EDXSO Comms. A simple
   approach: a Supabase Edge Function or a small always-on worker (Railway/Render free tier, since
   Vercel serverless won't hold a long-running job) that polls the `jobs` table.

## Notes on the persona prompt

Your original prompt assumes a rich public footprint (LinkedIn activity, press, podcasts). Most of
the 5 agencies you gave me don't have that — they're small brokerages with just a site and a phone
number. `persona_prompt.py` keeps your 17 sections but grounds every section in only what's actually
scraped, and forces low-confidence sections to say so explicitly instead of the model inventing
quotes or competitor names. Worth deciding now whether that's the behavior you want, or whether
you'd rather the model make a broader creative persona and mark it as illustrative — those are two
different products.
