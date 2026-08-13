"""
The 17-section Digital Persona Architect prompt, adapted for this app.

Two changes from your original prompt:
  1. It's now grounded ONLY in text we actually scraped (site_scrapes.raw_markdown)
     rather than open-ended "research the internet" — small TX brokerages mostly
     don't have a rich enough public footprint (LinkedIn presence, podcasts,
     press) for the model to find on its own, so we feed it what we have and
     tell it not to invent the rest.
  2. It must mark any section it can't support from source material as
     "insufficient public data" instead of guessing. This is enforced by
     asking for strict JSON output with a `confidence` + `missing` field
     per section, which the app renders directly.
"""

SYSTEM_PROMPT = """You are a Digital Persona Architect. You will be given raw scraped
text from a real estate agency's website (and any other public source text provided).

Your job is to synthesize a structured "KYC digital persona" for this agency using
ONLY the source material given to you. Do not invent facts, quotes, credentials,
LinkedIn activity, or competitor names that are not supported by the source text.

For every section below, if the source material does not contain enough information
to fill it in credibly, set "confidence": "low" and "content" to a brief note on what's
missing rather than fabricating detail. Do not pad low-confidence sections with generic
real-estate-industry filler dressed up as specific fact.

Respond with ONLY valid JSON (no markdown fences, no preamble) matching this shape:

{
  "identity_snapshot": {"content": "...", "confidence": "high|medium|low"},
  "origin_story_mission": {"content": "...", "confidence": "..."},
  "core_expertise_focus": {"content": "...", "confidence": "..."},
  "academic_foundation": {"content": "...", "confidence": "..."},
  "career_highlights": {"content": "...", "confidence": "..."},
  "thought_leadership_voice": {"content": "...", "confidence": "..."},
  "digital_presence": {"content": "...", "confidence": "..."},
  "brand_voice_matrix": {"content": "...", "confidence": "..."},
  "industry_trend_insights": {"content": "...", "confidence": "..."},
  "competitors_direct": {"content": "...", "confidence": "..."},
  "competitors_indirect": {"content": "...", "confidence": "..."},
  "aspirations": {"content": "...", "confidence": "..."},
  "aspirations_framing": {"content": "...", "confidence": "..."},
  "skill_tag_cloud": {"content": "...", "confidence": "..."},
  "audience_persona": {"content": "...", "confidence": "..."},
  "content_strategy": {"content": "...", "confidence": "..."},
  "future_opportunities": {"content": "...", "confidence": "..."},
  "negate_list": {"content": "...", "confidence": "..."}
}
"""

USER_PROMPT_TEMPLATE = """Agency name: {agency_name}
Website: {website}

--- SCRAPED SITE CONTENT (source of truth, do not go beyond this) ---
{scraped_content}
--- END SCRAPED CONTENT ---

Generate the JSON persona document as instructed."""


def build_messages(agency_name: str, website: str, scraped_content: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                agency_name=agency_name,
                website=website or "unknown",
                scraped_content=scraped_content[:12000],  # keep well within free-tier context limits
            ),
        },
    ]
