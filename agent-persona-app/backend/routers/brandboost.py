"""
BrandBoost integration: blog topic suggestions, post generation, SEO
analysis/optimization, AI-detection check, and humanization.

COST WARNING: /generate-post is a PAID call (~$0.002-$0.03 per post
depending on length). Never call this in a bulk loop (e.g. across all
agencies at once) without explicit intent -- unlike Groq/Firecrawl/Vercel
elsewhere in this app, BrandBoost is not free.

Auto-fills agency name/location/services/audience/tone from the agency's
already-generated persona, so the caller only needs to supply agency_id and
a topic -- no need to re-type brand details BrandBoost already has via us.
"""
from fastapi import APIRouter, HTTPException
from db.client import get_supabase
from models import SuggestTopicsRequest, GeneratePostRequest, PostActionRequest, BlogPost
from integrations import brandboost_client
from routers.site_gen import _get_agency, _get_persona
from site_gen_prompt import summarize_persona_for_codegen

router = APIRouter(prefix="/brandboost", tags=["brandboost"])


def _persona_field(sections: dict, key: str, default: str = "") -> str:
    section = sections.get(key)
    if section and section.get("content"):
        return str(section["content"])
    return default


@router.post("/suggest-topics")
def suggest_topics(req: SuggestTopicsRequest):
    sb = get_supabase()
    agency = _get_agency(sb, req.agency_id)
    persona = _get_persona(sb, req.agency_id, None)
    sections = persona["sections"]

    location = f"{agency.get('city') or ''}, {agency.get('state') or 'TX'}".strip(", ")
    services = _persona_field(sections, "core_expertise_focus", "Real estate sales and leasing")
    audience = _persona_field(sections, "audience_persona", "Home buyers and sellers")

    result = brandboost_client.suggest_topics(
        agency_name=agency["name"],
        agency_location=location or "Texas",
        services=services,
        target_audience=audience,
        count=req.count,
    )
    return result


@router.post("/generate-post", response_model=BlogPost)
def generate_post(req: GeneratePostRequest):
    """PAID call -- see module docstring."""
    sb = get_supabase()
    agency = _get_agency(sb, req.agency_id)
    persona = _get_persona(sb, req.agency_id, None)
    sections = persona["sections"]

    location = f"{agency.get('city') or ''}, {agency.get('state') or 'TX'}".strip(", ")
    tone = _persona_field(sections, "brand_voice_matrix", "Professional and trustworthy")
    audience = _persona_field(sections, "audience_persona", "Home buyers and sellers")

    result = brandboost_client.generate_post(
        agency_name=agency["name"],
        agency_location=location or "Texas",
        topic=req.topic,
        tone=tone,
        target_audience=audience,
        post_type=req.post_type,
        length=req.length,
        include_cta=req.include_cta,
    )
    data = result.get("data", {})
    if not data:
        raise HTTPException(status_code=502, detail=f"BrandBoost returned no data: {result}")

    row = (
        sb.table("blog_posts")
        .insert(
            {
                "agency_id": req.agency_id,
                "topic": data.get("topic", req.topic),
                "post_type": req.post_type,
                "content": data.get("post"),
                "word_count": data.get("wordCount"),
            }
        )
        .execute()
    )
    return row.data[0]


@router.post("/analyze-seo/{blog_post_id}")
def analyze_seo(blog_post_id: str):
    sb = get_supabase()
    post = sb.table("blog_posts").select("*").eq("id", blog_post_id).single().execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Blog post not found")
    result = brandboost_client.analyze_seo(post.data["content"], post.data.get("topic", ""))
    score = result.get("data", {}).get("score")
    if score is not None:
        sb.table("blog_posts").update({"seo_score": score}).eq("id", blog_post_id).execute()
    return result


@router.post("/optimize-seo/{blog_post_id}")
def optimize_seo(blog_post_id: str):
    """PAID call -- rewrites content, see module docstring."""
    sb = get_supabase()
    post = sb.table("blog_posts").select("*").eq("id", blog_post_id).single().execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Blog post not found")
    result = brandboost_client.optimize_seo(post.data["content"], post.data.get("topic", ""))
    optimized = result.get("data", {}).get("optimizedContent")
    if optimized:
        sb.table("blog_posts").update({"content": optimized}).eq("id", blog_post_id).execute()
    return result


@router.post("/analyze-ai-detection/{blog_post_id}")
def analyze_ai_detection(blog_post_id: str):
    sb = get_supabase()
    post = sb.table("blog_posts").select("*").eq("id", blog_post_id).single().execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Blog post not found")
    result = brandboost_client.analyze_ai_detection(post.data["content"], post.data.get("topic", ""))
    verdict = result.get("data", {}).get("verdict")
    if verdict:
        sb.table("blog_posts").update({"ai_detection_verdict": verdict}).eq("id", blog_post_id).execute()
    return result


@router.post("/humanize-post/{blog_post_id}")
def humanize_post(blog_post_id: str):
    """PAID call -- rewrites content, see module docstring."""
    sb = get_supabase()
    post = sb.table("blog_posts").select("*").eq("id", blog_post_id).single().execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Blog post not found")
    result = brandboost_client.humanize_post(post.data["content"], post.data.get("topic", ""))
    humanized = result.get("data", {}).get("humanizedContent")
    if humanized:
        sb.table("blog_posts").update({"content": humanized}).eq("id", blog_post_id).execute()
    return result


@router.get("/posts/{agency_id}", response_model=list[BlogPost])
def list_posts(agency_id: str):
    sb = get_supabase()
    result = (
        sb.table("blog_posts")
        .select("*")
        .eq("agency_id", agency_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []