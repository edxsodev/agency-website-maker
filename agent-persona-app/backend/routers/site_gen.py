"""
Site generation module: persona + original site -> a regenerated site,
via two interchangeable pipelines:

  1. /generate         -- single self-contained HTML file, generated
                           synchronously via Groq (10-30s, no build step).
  2. /generate-lovable -- a real React app, generated via a self-hosted
                           Open Lovable instance (see integrations/
                           open_lovable_client.py). Requires Open Lovable
                           running separately at OPEN_LOVABLE_BASE_URL.

Both share the same persona lookup and brand-summary logic so results stay
consistent regardless of which pipeline produced them.
"""
import os
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from groq import Groq
from db.client import get_supabase
from models import SiteGenRequest, GeneratedSite
from site_gen_prompt import build_messages, summarize_persona_for_codegen, build_lovable_prompt
from routers.persona import _scrape_site  # reuse the same Firecrawl scraper
from integrations import open_lovable_client
from integrations import vercel_deploy

router = APIRouter(prefix="/site-gen", tags=["site_gen"])

GROQ_MODEL = "llama-3.3-70b-versatile"


@lru_cache
def _groq_client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _get_agency(sb, agency_id: str) -> dict:
    agency = sb.table("agencies").select("*").eq("id", agency_id).single().execute()
    if not agency.data:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency.data


def _get_persona(sb, agency_id: str, persona_id: str | None) -> dict:
    if not persona_id:
        latest_persona = (
            sb.table("personas")
            .select("*")
            .eq("agency_id", agency_id)
            .order("generated_at", desc=True)
            .limit(1)
            .execute()
        )
        if not latest_persona.data:
            raise HTTPException(
                status_code=422,
                detail="No persona exists for this agency yet -- generate one first via /persona/generate.",
            )
        return latest_persona.data[0]

    persona_result = sb.table("personas").select("*").eq("id", persona_id).single().execute()
    if not persona_result.data:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona_result.data


def _generate_html(agency: dict, scraped_content: str, persona_sections: dict, style_notes: str | None) -> str:
    persona_summary = summarize_persona_for_codegen(persona_sections)
    messages = build_messages(
        agency_name=agency["name"],
        phone=agency.get("phone"),
        address=agency.get("address"),
        website=agency.get("website"),
        scraped_content=scraped_content,
        persona_summary=persona_summary,
        agency_id=agency["id"],
        style_notes=style_notes,
    )
    client = _groq_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.85,
            max_tokens=8000,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq call failed: {e}")

    html = response.choices[0].message.content.strip()

    # Groq sometimes wraps output in markdown fences despite instructions -- strip if present
    if html.startswith("```"):
        html = html.split("\n", 1)[1] if "\n" in html else html
        if html.endswith("```"):
            html = html.rsplit("```", 1)[0]
        html = html.strip()

    if not html.lower().startswith(("<!doctype", "<html")):
        raise HTTPException(status_code=502, detail="Groq did not return valid HTML -- try again.")

    return html


@router.post("/generate", response_model=GeneratedSite)
def generate_site(req: SiteGenRequest):
    sb = get_supabase()
    agency = _get_agency(sb, req.agency_id)
    persona = _get_persona(sb, req.agency_id, req.persona_id)

    # Get the scraped content (reuse persona's scrape if it exists)
    scraped_content = None
    if persona.get("scrape_id"):
        scrape_result = sb.table("site_scrapes").select("*").eq("id", persona["scrape_id"]).single().execute()
        if scrape_result.data:
            scraped_content = scrape_result.data.get("raw_markdown")

    if not scraped_content:
        if not agency.get("website"):
            raise HTTPException(status_code=422, detail="Agency has no website and no cached scrape available.")
        scraped_content = _scrape_site(agency["website"])

    html = _generate_html(agency, scraped_content, persona["sections"], req.style_notes)

    site_row = (
        sb.table("generated_sites")
        .insert(
            {
                "agency_id": req.agency_id,
                "persona_id": persona["id"],
                "framework": "single-file-html",
                "html_content": html,
                "generation_status": "done",
            }
        )
        .execute()
    )
    return site_row.data[0]


@router.post("/generate-lovable", response_model=GeneratedSite)
def generate_site_with_lovable(req: SiteGenRequest):
    """Same brand-aware pipeline as /generate, but produces a real React app
    via a self-hosted Open Lovable instance instead of a single HTML file.
    Requires Open Lovable running separately (see OPEN_LOVABLE_BASE_URL)."""
    sb = get_supabase()
    agency = _get_agency(sb, req.agency_id)
    if not agency.get("website"):
        raise HTTPException(status_code=422, detail="Agency has no website on file.")
    persona = _get_persona(sb, req.agency_id, req.persona_id)

    persona_summary = summarize_persona_for_codegen(persona["sections"])

    # 1. Scrape via Open Lovable's own scraper (keeps its expected context shape)
    scraped = open_lovable_client.scrape_url(agency["website"])

    # 2. Spin up a fresh sandbox
    sandbox = open_lovable_client.create_sandbox()

    # 3. Generate code (streamed, consumed to completion)
    prompt = build_lovable_prompt(
        agency["name"],
        agency.get("phone"),
        agency.get("address"),
        persona_summary,
        scraped_content=scraped.get("content", ""),
        screenshot_url=scraped.get("screenshot"),
        agency_id=agency["id"],
        style_notes=req.style_notes,
    )

    complete = open_lovable_client.generate_code(prompt, sandbox["sandboxId"], scraped)
    generated_code = complete.get("generatedCode", "")

    # 4. Apply the generated files into the sandbox so the preview URL is live
    open_lovable_client.apply_code(generated_code, sandbox["sandboxId"])

    # 5. Deploy to a real, permanent Vercel deployment -- reusing the SAME
    # file content we already parsed from the generation step, rather than
    # asking Open Lovable for it back (its get-sandbox-files route checks a
    # sandbox reference that create-ai-sandbox-v2 doesn't populate -- a
    # version mismatch in this build, not something fixable on our end).
    parsed_files = open_lovable_client.parse_files(generated_code)
    files_dict = {f["path"]: f["content"] for f in parsed_files}
    if not files_dict:
        raise HTTPException(status_code=502, detail="No files parsed from generated code -- nothing to deploy.")
    deployment = vercel_deploy.deploy_files(files_dict, agency["name"])

    site_row = (
        sb.table("generated_sites")
        .insert(
            {
                "agency_id": req.agency_id,
                "persona_id": persona["id"],
                "framework": "open-lovable-react",
                "preview_url": deployment["url"] or sandbox["url"],
                "generation_status": "done",
            }
        )
        .execute()
    )
    return site_row.data[0]


@router.get("/{agency_id}", response_model=GeneratedSite)
def get_latest_site(agency_id: str):
    sb = get_supabase()
    result = (
        sb.table("generated_sites")
        .select("*")
        .eq("agency_id", agency_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No site generated yet for this agency")
    return result.data[0]


@router.get("/{agency_id}/preview", response_class=HTMLResponse)
def preview_latest_site(agency_id: str):
    """Returns the raw generated HTML directly (single-file-html pipeline
    only) -- open this URL in a browser to see the site, or embed it in an
    <iframe src="...">. For open-lovable-react sites, use the preview_url
    from GET /site-gen/{agency_id} instead (points at the live sandbox)."""
    sb = get_supabase()
    result = (
        sb.table("generated_sites")
        .select("html_content")
        .eq("agency_id", agency_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data or not result.data[0].get("html_content"):
        raise HTTPException(
            status_code=404,
            detail="No single-file HTML site available for this agency (it may have been generated via Open Lovable instead -- check GET /site-gen/{agency_id}.preview_url).",
        )
    return HTMLResponse(content=result.data[0]["html_content"])