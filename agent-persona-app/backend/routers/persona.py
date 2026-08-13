"""
Persona module: scrape an agency's site -> generate the 17-section
KYC digital persona.

Real implementation plugs in here (next build step):
  1. Scrape: Firecrawl free tier (POST /v0/scrape) -> raw_markdown,
     saved to `site_scrapes`.
  2. Generate: call Groq's chat completions with persona_prompt.build_messages(),
     model="llama-3.3-70b-versatile", response_format json.
  3. Parse the JSON, store in `personas.sections`, compute
     `data_confidence` (majority vote across section confidences) and
     `missing_sections` (any section marked "low").
  4. Render `markdown` from sections for display/export.
"""
import json
import os
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from firecrawl import FirecrawlApp
from groq import Groq
from db.client import get_supabase
from models import PersonaGenerateRequest, Persona
from persona_prompt import build_messages

router = APIRouter(prefix="/persona", tags=["persona"])

GROQ_MODEL = "llama-3.3-70b-versatile"  # free-tier model, matches your existing RAG project


@lru_cache
def _firecrawl_client() -> FirecrawlApp:
    return FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])


@lru_cache
def _groq_client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _scrape_site(url: str) -> str:
    """Scrape a site with Firecrawl, return the markdown content."""
    app = _firecrawl_client()
    try:
        result = app.scrape_url(url, params={"formats": ["markdown"]})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scrape failed for {url}: {e}")

    markdown = result.get("markdown") if isinstance(result, dict) else getattr(result, "markdown", None)
    if not markdown:
        raise HTTPException(status_code=502, detail=f"Scrape returned no content for {url}")
    return markdown


def _call_groq(messages: list[dict]) -> dict:
    """Call Groq's chat completion, forcing JSON output, and parse it."""
    client = _groq_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.4,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq call failed: {e}")

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail=f"Groq returned non-JSON output: {raw[:500]}")


@router.post("/generate", response_model=Persona)
def generate_persona(req: PersonaGenerateRequest):
    sb = get_supabase()

    agency = sb.table("agencies").select("*").eq("id", req.agency_id).single().execute()
    if not agency.data:
        raise HTTPException(status_code=404, detail="Agency not found")
    agency = agency.data

    if not agency.get("website"):
        raise HTTPException(
            status_code=422,
            detail="Agency has no website on file — persona generation needs at least one public source.",
        )

    # 1. Scrape (or reuse latest scrape unless force_rescrape)
    scrape_query = (
        sb.table("site_scrapes")
        .select("*")
        .eq("agency_id", req.agency_id)
        .order("scraped_at", desc=True)
        .limit(1)
        .execute()
    )
    if scrape_query.data and not req.force_rescrape:
        scrape = scrape_query.data[0]
    else:
        raw_markdown = _scrape_site(agency["website"])  # NotImplementedError until wired up
        scrape_row = (
            sb.table("site_scrapes")
            .insert(
                {
                    "agency_id": req.agency_id,
                    "url": agency["website"],
                    "raw_markdown": raw_markdown,
                    "scrape_status": "success",
                }
            )
            .execute()
        )
        scrape = scrape_row.data[0]

    # 2. Generate persona JSON
    messages = build_messages(agency["name"], agency["website"], scrape["raw_markdown"] or "")
    sections = _call_groq(messages)  # NotImplementedError until wired up

    confidences = [s.get("confidence", "low") for s in sections.values()]
    missing = [k for k, v in sections.items() if v.get("confidence") == "low"]
    overall = "high" if confidences.count("high") > len(confidences) / 2 else (
        "medium" if confidences.count("low") < len(confidences) / 2 else "low"
    )

    persona_row = (
        sb.table("personas")
        .insert(
            {
                "agency_id": req.agency_id,
                "scrape_id": scrape["id"],
                "sections": sections,
                "data_confidence": overall,
                "missing_sections": missing,
                "model_used": GROQ_MODEL,
            }
        )
        .execute()
    )
    return persona_row.data[0]


@router.get("/{agency_id}", response_model=Persona)
def get_latest_persona(agency_id: str):
    sb = get_supabase()
    result = (
        sb.table("personas")
        .select("*")
        .eq("agency_id", agency_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No persona generated yet for this agency")
    return result.data[0]
