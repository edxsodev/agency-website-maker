"""
Public integration endpoint for the external voice assistant app. Returns
an agency's name + full brand persona keyed by a simple sequential
agency_number (1, 2, 3...) instead of a UUID, since that's far easier for
a third-party app to reference and configure per phone line.

NOTE ON AUTH: this endpoint currently has NO authentication -- anyone with
the URL can read any agency's persona. Fine for a private demo/friend
integration, but before sharing this URL beyond that, add a shared API key
check (see the integration guide for the planned approach).
"""
from fastapi import APIRouter, HTTPException
from db.client import get_supabase
from models import VoiceAgentDirectoryEntry, VoiceAgentPersonaResponse

router = APIRouter(prefix="/voice-agent", tags=["voice_agent"])


@router.get("", response_model=list[VoiceAgentDirectoryEntry])
def list_agencies_for_voice_agent():
    """Directory of all agencies and their numbers -- useful for the voice
    app to show/configure which number maps to which agency."""
    sb = get_supabase()
    result = sb.table("agencies").select("agency_number, name, website").order("agency_number").execute()
    return [
        {"agency_number": row["agency_number"], "agency_name": row["name"], "website": row.get("website")}
        for row in (result.data or [])
    ]


@router.get("/{agency_number}", response_model=VoiceAgentPersonaResponse)
def get_persona_by_number(agency_number: int):
    sb = get_supabase()
    agency_result = sb.table("agencies").select("*").eq("agency_number", agency_number).single().execute()
    if not agency_result.data:
        raise HTTPException(status_code=404, detail=f"No agency found with agency_number {agency_number}")
    agency = agency_result.data

    persona_result = (
        sb.table("personas")
        .select("*")
        .eq("agency_id", agency["id"])
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    if not persona_result.data:
        raise HTTPException(
            status_code=422,
            detail=f"Agency {agency_number} ({agency['name']}) has no persona generated yet.",
        )
    persona = persona_result.data[0]

    call_bot_result = (
        sb.table("call_bot_prompts")
        .select("prompt_text")
        .eq("agency_id", agency["id"])
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    call_bot_prompt = call_bot_result.data[0]["prompt_text"] if call_bot_result.data else None

    return {
        "agency_number": agency["agency_number"],
        "agency_name": agency["name"],
        "phone": agency.get("phone"),
        "address": agency.get("address"),
        "persona": persona["sections"],
        "call_bot_prompt": call_bot_prompt,
    }