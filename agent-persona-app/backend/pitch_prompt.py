"""
Builds a structured competitive-comparison prompt: the agency's OWN original
site vs. a real competitor's site vs. what we actually built for them.

Grounding rule: every claim must be traceable to real scraped content or to
a feature we actually shipped (video hero, WhatsApp CTA, lead form, sample
listings grid, booking widget, blog/insights) -- never invent a competitor
weakness or an advantage we didn't build. This becomes a literal sales
script, so fabrication here is a much bigger liability than a demo page.
"""

OUR_FEATURES = [
    "A full-bleed video hero and a second embedded 'Take a Tour' video section",
    "A floating WhatsApp button linking directly to their real number",
    "A detailed lead-capture form wired to a live backend (not a dead mailto link)",
    "A 'Book a Consultation' scheduling widget",
    "A featured listings grid styled like a professional MLS presentation",
    "An Insights/Blog section for ongoing SEO content",
    "Modern layered visual design (typography, shadows, spacing) built specifically around their brand tone",
]

SYSTEM_PROMPT = """You are a competitive analyst preparing a sales pitch document
for a web design/marketing agency. You will be given: (a) the target
agency's OWN original website content, (b) a real competitor's website
content, and (c) a list of features the agency built for the target.

Your job: produce a grounded, honest comparison that a salesperson could
read on a real call with the site owner.

CRITICAL RULES:
- Every gap you claim about the target's current site must be traceable to
  the actual scraped content provided -- if their scraped content doesn't
  mention a feature (e.g. no contact form, no blog, no video), you can note
  its absence. Do not claim something is missing if it's actually present
  in their content.
- Every competitor strength must be grounded in the competitor's actual
  scraped content -- do not invent capabilities they don't show evidence of.
- Paraphrase content in your own words -- never quote either site's
  marketing copy verbatim.
- "Our advantages" must come ONLY from the provided feature list -- do not
  invent capabilities beyond what's listed.
- Keep it factual and specific, not hypey. A site owner will see through
  exaggeration immediately.

Respond with ONLY valid JSON (no markdown fences, no preamble):
{
  "current_site_gaps": [{"gap": "short label", "evidence": "1 sentence, grounded in their scraped content"}],
  "competitor_strengths": [{"strength": "short label", "evidence": "1 sentence, grounded in competitor's scraped content"}],
  "our_advantages": [{"advantage": "short label", "detail": "1 sentence explaining the concrete benefit"}],
  "summary_pitch": "A 2-3 sentence pitch a salesperson could say out loud on a call, grounded in the above -- no hype, just the honest case."
}
"""

USER_PROMPT_TEMPLATE = """Target agency: {agency_name}

--- TARGET'S OWN ORIGINAL SITE CONTENT (scraped) ---
{own_content}
--- END ---

--- COMPETITOR SITE CONTENT (scraped from {competitor_name}) ---
{competitor_content}
--- END ---

--- FEATURES WE BUILT FOR THE TARGET ---
{our_features}
--- END ---

Generate the comparison JSON now."""


def build_messages(
    agency_name: str,
    own_content: str,
    competitor_content: str,
    competitor_name: str,
) -> list[dict]:
    features_text = "\n".join(f"- {f}" for f in OUR_FEATURES)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                agency_name=agency_name,
                own_content=own_content[:6000],
                competitor_content=competitor_content[:6000],
                competitor_name=competitor_name or "the competitor",
                our_features=features_text,
            ),
        },
    ]