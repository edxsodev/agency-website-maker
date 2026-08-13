"""
Discovery module: location -> list of real estate agencies.

Real implementation plugs in here (next build step):
  1. Call Google Places API "Text Search" with query
     f"real estate agency in {location}"
  2. Paginate through next_page_token (max 60 results per Google's cap)
  3. For each result, call Place Details to backfill phone/website
     (Text Search alone doesn't return phone/website)
  4. Upsert into `agencies` table keyed on website (or place_id)
  5. Insert a `search_locations` row to cache the run

For now this returns data from the `agencies` table only (i.e. your
5 seeded Texas agencies), so the frontend has something real to hit
while Places integration is built.
"""
from fastapi import APIRouter, HTTPException
from db.client import get_supabase
from models import DiscoveryRequest, DiscoveryResult, Agency

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("", response_model=DiscoveryResult)
def discover_agencies(req: DiscoveryRequest):
    sb = get_supabase()

    # TODO: replace this block with an actual Google Places call.
    # Stubbed: just filter what's already in the DB by city/state text match
    # so the endpoint is usable end-to-end today.
    q = sb.table("agencies").select("*")
    if req.location:
        # naive contains-match against city/address until real geo search lands
        q = q.ilike("address", f"%{req.location.split(',')[0]}%")
    result = q.limit(req.max_results).execute()

    agencies = result.data or []

    # log the search
    loc_row = (
        sb.table("search_locations")
        .insert({"query": req.location, "result_count": len(agencies)})
        .execute()
    )
    location_id = loc_row.data[0]["id"] if loc_row.data else None

    return DiscoveryResult(
        location_id=location_id,
        agencies_found=len(agencies),
        agencies=agencies,
    )


@router.get("/{agency_id}", response_model=Agency)
def get_agency(agency_id: str):
    sb = get_supabase()
    result = sb.table("agencies").select("*").eq("id", agency_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Agency not found")
    return result.data
