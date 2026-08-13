"""
Competitive pitch report: scrapes a real competitor, compares against the
agency's own original site, and generates a grounded gap analysis + sales
pitch summary.
"""
import os
import json
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from groq import Groq
from db.client import get_supabase
from models import PitchGenerateRequest, PitchReport
from pitch_prompt import build_messages
from routers.persona import _scrape_site
from routers.site_gen import _get_agency

router = APIRouter(prefix="/pitch", tags=["pitch"])

GROQ_MODEL = "llama-3.3-70b-versatile"


@lru_cache
def _groq_client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


@router.post("/generate", response_model=PitchReport)
def generate_pitch(req: PitchGenerateRequest):
    sb = get_supabase()
    agency = _get_agency(sb, req.agency_id)

    # Get the agency's OWN original scraped content (reuse latest scrape if we have one)
    own_content = None
    scrape_result = (
        sb.table("site_scrapes")
        .select("*")
        .eq("agency_id", req.agency_id)
        .order("scraped_at", desc=True)
        .limit(1)
        .execute()
    )
    if scrape_result.data:
        own_content = scrape_result.data[0].get("raw_markdown")

    if not own_content:
        if not agency.get("website"):
            raise HTTPException(status_code=422, detail="Agency has no website and no cached scrape available.")
        own_content = _scrape_site(agency["website"])

    # Scrape the competitor fresh
    try:
        competitor_content = _scrape_site(req.competitor_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not scrape competitor URL: {e}")

    messages = build_messages(
        agency_name=agency["name"],
        own_content=own_content,
        competitor_content=competitor_content,
        competitor_name=req.competitor_name or req.competitor_url,
    )

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
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail=f"Model returned non-JSON output: {raw[:300]}")

    row = (
        sb.table("pitch_reports")
        .insert(
            {
                "agency_id": req.agency_id,
                "competitor_url": req.competitor_url,
                "competitor_name": req.competitor_name,
                "current_site_gaps": parsed.get("current_site_gaps", []),
                "competitor_strengths": parsed.get("competitor_strengths", []),
                "our_advantages": parsed.get("our_advantages", []),
                "summary_pitch": parsed.get("summary_pitch"),
            }
        )
        .execute()
    )
    return row.data[0]


@router.get("/{agency_id}", response_model=PitchReport)
def get_latest_pitch(agency_id: str):
    sb = get_supabase()
    result = (
        sb.table("pitch_reports")
        .select("*")
        .eq("agency_id", agency_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No pitch report generated yet for this agency")
    return result.data[0]