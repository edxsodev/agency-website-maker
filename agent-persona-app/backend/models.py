"""
Pydantic schemas shared across routers.
Keep these in sync with db/schema.sql.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, HttpUrl, Field


# ---------- Agencies ----------

class AgencyBase(BaseModel):
    name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: str = "TX"
    zip: Optional[str] = None
    source: str = "manual"
    place_id: Optional[str] = None
    google_maps_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class AgencyCreate(AgencyBase):
    pass


class Agency(AgencyBase):
    id: str
    location_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Discovery ----------

class DiscoveryRequest(BaseModel):
    location: str = Field(..., description="e.g. 'Round Rock, TX' or a lat/lng pair as text")
    radius_meters: int = 20000
    max_results: int = 20


class DiscoveryResult(BaseModel):
    location_id: str
    agencies_found: int
    agencies: list[Agency]


# ---------- Personas ----------

class PersonaSection(BaseModel):
    title: Optional[str] = None
    content: Any  # free-form: str, list, or nested dict depending on section
    confidence: str = "medium"  # low | medium | high


class PersonaGenerateRequest(BaseModel):
    agency_id: str
    force_rescrape: bool = False


class Persona(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}

    id: str
    agency_id: str
    sections: dict[str, PersonaSection]
    markdown: Optional[str] = None
    data_confidence: str = "low"
    missing_sections: list[str] = []
    model_used: Optional[str] = None
    generated_at: datetime
    version: int = 1


# ---------- Site generation ----------

class SiteGenRequest(BaseModel):
    agency_id: str
    persona_id: Optional[str] = None  # if omitted, uses latest persona
    style_notes: Optional[str] = None  # e.g. "keep it minimal, navy + gold palette"


class GeneratedSite(BaseModel):
    id: str
    agency_id: str
    persona_id: Optional[str] = None
    framework: str = "single-file-html"
    html_content: Optional[str] = None
    preview_url: Optional[str] = None
    repo_url: Optional[str] = None
    generation_status: str = "pending"
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Jobs ----------

class Job(BaseModel):
    id: str
    job_type: str
    agency_id: Optional[str] = None
    location_id: Optional[str] = None
    status: str = "queued"
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


# ---------- Leads ----------

class LeadCreate(BaseModel):
    agency_id: str
    name: str
    email: str
    phone: Optional[str] = None
    message: Optional[str] = None
    source: str = "website_form"


class Lead(LeadCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- BrandBoost blog posts ----------

class SuggestTopicsRequest(BaseModel):
    agency_id: str
    count: int = 10


class GeneratePostRequest(BaseModel):
    agency_id: str
    topic: str
    post_type: str = "blog"  # blog | listicle | case-study | guide | news | opinion
    length: str = "medium"   # short | medium | long | xlong
    include_cta: bool = True


class PostActionRequest(BaseModel):
    blog_post_id: str


class BlogPost(BaseModel):
    id: str
    agency_id: str
    topic: Optional[str] = None
    post_type: str = "blog"
    content: Optional[str] = None
    word_count: Optional[int] = None
    seo_score: Optional[int] = None
    ai_detection_verdict: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

    # ---------- Pitch reports ----------

class PitchGenerateRequest(BaseModel):
    agency_id: str
    competitor_url: str
    competitor_name: Optional[str] = None


class PitchReport(BaseModel):
    id: str
    agency_id: str
    competitor_url: str
    competitor_name: Optional[str] = None
    current_site_gaps: list = []
    competitor_strengths: list = []
    our_advantages: list = []
    summary_pitch: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

    # ---------- Voice agent integration ----------

class VoiceAgentDirectoryEntry(BaseModel):
    agency_number: int
    agency_name: str
    website: Optional[str] = None


class VoiceAgentPersonaResponse(BaseModel):
    agency_number: int
    agency_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    persona: dict
    call_bot_prompt: Optional[str] = None