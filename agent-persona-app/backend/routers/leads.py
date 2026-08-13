"""
Public lead-capture endpoint -- called directly from a visitor's browser
via fetch() on a generated site's contact form. No auth, since this is
meant to be hit by anonymous site visitors.

DEMO LIMITATION: no rate limiting, spam filtering, or CAPTCHA -- fine for
a demo, not production-ready as-is if this were ever exposed publicly.
"""
from fastapi import APIRouter, HTTPException
from db.client import get_supabase
from models import LeadCreate, Lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=Lead)
def create_lead(lead: LeadCreate):
    sb = get_supabase()
    agency = sb.table("agencies").select("id").eq("id", lead.agency_id).single().execute()
    if not agency.data:
        raise HTTPException(status_code=404, detail="Agency not found")

    result = sb.table("leads").insert(lead.model_dump()).execute()
    return result.data[0]


@router.get("/{agency_id}", response_model=list[Lead])
def list_leads(agency_id: str):
    sb = get_supabase()
    result = (
        sb.table("leads")
        .select("*")
        .eq("agency_id", agency_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []