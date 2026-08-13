"""
Prompt for regenerating an agency's website as a single modern HTML file,
and a separate prompt builder for the Open Lovable (React) pipeline.

Design choice for the HTML path: single self-contained HTML file (inline
<style>, vanilla JS) rather than a full React/Vite build. A free-tier LLM
(Groq llama-3.3-70b) is far more reliable at producing one coherent file
than a correct multi-file React project, and it needs no build step -- it
can be opened directly in a browser or dropped onto any static host
(Vercel, Netlify, GitHub Pages -- all free).
"""
import re
from sample_listings import format_listings_for_prompt

HERO_VIDEO_URL = "https://videos.pexels.com/video-files/7578541/7578541-uhd_2560_1440_30fps.mp4"
SECTION_VIDEO_URL = "https://videos.pexels.com/video-files/7578544/7578544-uhd_2560_1440_30fps.mp4"
CALENDLY_URL = "https://calendly.com/sankalp-bhattacharjee10/30min"

SYSTEM_PROMPT = """You are a senior web designer and frontend developer. You will be
given (a) raw scraped content from a real estate agency's current website, and
(b) a structured brand/persona document for that agency.

Your job: produce a single, complete, modern, production-quality HTML file that
could replace their current site's homepage.

CRITICAL -- avoid the default template: the laziest possible real-estate-site
layout is "dark hero banner + three equal white cards in a grid below + dark
contact footer." Do NOT default to that. Before writing any code, pick ONE
distinct structural approach based on this agency's specific brand voice and
content, for example:

- A split hero (headline + short pitch on one side, a bold color block or
  stat on the other) instead of a centered banner
- An asymmetric layout: one large featured focus area beside two smaller ones,
  rather than three equal-width cards
- A vertical narrative flow: alternating left/right sections as the visitor
  scrolls, each with a different background treatment
- A single strong focal statement/value-prop section instead of a generic
  card grid, if the scraped content only supports one or two real claims
- Section counts and card counts should vary based on how much REAL content
  you actually have -- do not pad to exactly 3 cards if there are only 2 real
  differentiators, and do not compress 5 real service areas into 3.

Vary color usage too: not every design needs a solid dark banner top and
bottom -- consider a light palette with one strong accent color, or a single
full-width color section placed elsewhere in the page instead of bookending it.

Hard requirements:
- Output ONLY raw HTML. No markdown fences, no explanation, no preamble.
- Everything in ONE file: inline <style> in the <head>, inline <script> before
  </body> if needed. No external CSS/JS files, no build step.
- Use only the agency's REAL name, phone number, address, and any real service
  details found in the scraped content and persona. Never invent fake agent
  names, fake testimonials, fake awards, or fake stats. If you don't have a
  real detail (e.g. no testimonials were scraped), omit that section rather
  than fabricating content.
- Real typographic hierarchy (not just default browser styles), a deliberate
  2-3 color palette, generous whitespace, and a responsive layout (flexbox/grid
  + media queries, no framework needed).
- Use Google Fonts via a <link> tag for real typographic quality -- vary the
  font pairing choice based on brand tone (e.g. a serif display font for a
  more established/traditional brand voice vs. a clean geometric sans for a
  modern/tech-forward one).
- No lorem ipsum. No placeholder image URLs that 404 -- either omit images or
  use a solid-color/gradient div as a placeholder background, never a broken
  <img> tag.
- Include a floating WhatsApp button (fixed to the bottom-right corner,
  staying visible on scroll) that links directly to the WhatsApp link provided
  -- this must go to the agency's own real number, never a placeholder or
  shared number.
- Never use a dead '#' href for any button or nav item that has a real
  corresponding link provided in the REAL FUNCTIONAL LINKS section -- use the
  exact real URL instead.
- LAYOUT SAFETY: do not stack multiple content blocks on top of each other
  using position: absolute or position: fixed in a way that causes text or
  elements to overlap. Each section must sit in normal document flow, one
  after another, fully visible with no overlapping text. Only use
  position: fixed for the WhatsApp button itself -- nothing else should be
  absolutely/fixed positioned unless it's a small icon or badge clearly
  layered on top of a single parent image, never overlapping unrelated text.
- NO FAKE FUNCTIONALITY: do not build a property search bar, filter
  dropdowns, or a search input for the listings grid -- just display the
  featured listings grid directly. A search box that does nothing is worse
  than not having one.
"""

USER_PROMPT_TEMPLATE = """Agency name: {agency_name}
Phone: {phone}
Address: {address}
Website: {website}
WhatsApp link: {whatsapp_link}

--- CURRENT SITE CONTENT (scraped, use for real facts/services only) ---
{scraped_content}
--- END CURRENT SITE CONTENT ---

--- REAL FUNCTIONAL LINKS FOUND ON THEIR SITE (use these EXACT urls for the
corresponding buttons/nav items -- e.g. if "Find a Home" links to
realtytexas.com/buy in this list, your "Find a Home" button must use that
real URL, NOT '#'. If no real link matches a button you want, either omit
the button or link it to the agency's homepage URL instead of a dead '#'.) ---
{real_links}
--- END REAL LINKS ---

{trust_signals}

--- BRAND PERSONA (use for tone, positioning, focus areas) ---
{persona_summary}
--- END BRAND PERSONA ---

--- FEATURED LISTINGS (SAMPLE/PLACEHOLDER DATA -- these are illustrative
demo listings, not the agency's real current inventory. Render them as a
"Featured Listings" or "Current Listings" grid section: a photo, a status
badge (Active/Pending), price, address, and bed/bath/sqft stats per card --
matching the density and style of professional real estate listing sites.
Include a small, unobtrusive "Sample Listing" label on each card or a
section note so it's clear these are illustrative, not live inventory. Use
the exact photo URLs given -- do not invent different image URLs.) ---
{listings}
--- END LISTINGS ---

Structural direction for THIS page (follow this specifically, don't default
to a generic hero+three-cards layout instead): {layout_hint}

VIDEO REQUIREMENTS:
- Hero section: use a full-bleed background <video autoplay muted loop
  playsinline> with src="{hero_video_url}" (a real, verified, free-to-use
  stock video -- do not substitute a different URL). Add a dark
  semi-transparent overlay div on top for text contrast, same principle as
  an image hero.
- Include ONE additional section further down the page with an embedded
  <video controls> (not autoplay) using src="{section_video_url}", framed
  as something like "See Inside" or "Take a Tour" -- a real playable video
  section, not a background loop.

LEAD CAPTURE FORM:
Include a detailed contact/lead form (not just email) with fields: Full
Name, Email, Phone, and a Message textarea. On submit, use fetch() to POST
JSON to {api_base_url}/leads with this exact body shape:
{{"agency_id": "{agency_id_value}", "name": <value>, "email": <value>,
"phone": <value>, "message": <value>, "source": "website_form"}}
Show a success message on 200 response, and a simple error message
otherwise. Do not use a <form action> submit -- use JS fetch with
event.preventDefault().

BOOKING WIDGET (SAMPLE/PLACEHOLDER -- this is a demo booking calendar, not
the agency's real scheduling system). Include a "Book a Consultation"
section with an embedded Calendly widget using this exact snippet:
<link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">
<script src="https://assets.calendly.com/assets/external/widget.js" async></script>
<div class="calendly-inline-widget" data-url="{calendly_url}" style="min-width:320px;height:630px;"></div>
Add a small "Sample booking calendar" label near this section, same
principle as the sample listings label.

PREMIUM DESIGN REQUIREMENTS (this must feel like a considered, expensive
design, not a template):
- Use layered surfaces, not flat white/gray everywhere -- vary section
  backgrounds deliberately (at least one section should use a distinct
  color block, subtle gradient, or textured treatment).
- Generous vertical rhythm: 80-120px of padding on major sections, not the
  default 40-48px.
- A real typographic scale with intentional weight contrast (e.g. a bold
  56-72px display headline against a light 16-18px body), not uniform sizing.
- Subtle elevation: soft layered shadows on cards/buttons, not flat borders.
- Micro-interactions: hover states with slight scale/lift and smooth
  transitions (transition-all duration-300) on every interactive element.

{style_notes_block}

Generate the single-file HTML now."""

LAYOUT_HINTS = [
    "Split hero with headline/pitch on the left and a bold solid-color block "
    "with a key stat or short quote on the right. Below, a vertical alternating "
    "left/right section flow (not a card grid) for services.",

    "Full-bleed light hero with a large serif headline and small centered nav-style "
    "tagline, then an asymmetric two-column features area (one large featured "
    "block + a stacked list of smaller items beside it), not equal-width cards.",

    "Minimal, text-forward layout: a strong single value-proposition statement "
    "as the hero (no banner background, just generous whitespace and large type), "
    "followed by a horizontal scrolling-style or staggered-offset services section.",

    "Bold single-color-block hero with a diagonal or angled section divider, "
    "followed by a services section presented as a numbered list with large "
    "numerals rather than boxed cards.",

    "Editorial-style layout: hero image-placeholder block with overlaid text, "
    "then content organized in a magazine-style two-column layout rather than "
    "a symmetric card grid.",
]


def build_whatsapp_link(phone: str | None) -> str | None:
    """Converts a phone number like '+1 512-476-5348' into a wa.me deep link."""
    if not phone:
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        return None
    return f"https://wa.me/{digits}"


def extract_real_links(scraped_content: str, max_links: int = 8) -> list[dict]:
    """Pulls real [text](url) links out of Firecrawl's markdown output --
    these are the agency's actual functional CTAs (Buy, Schedule Appointment,
    Reviews, etc.) that currently get discarded and replaced with dead '#'
    placeholders in generated code. Filters out obvious junk (recaptcha,
    social icons with no real text) and caps the count to keep prompts lean."""
    if not scraped_content:
        return []
    raw_links = re.findall(r'\[([^\]]{2,40})\]\((https?://[^\s)]+)\)', scraped_content)
    seen_urls = set()
    links = []
    skip_terms = {"recaptcha", "verify", "click to verify", "qr"}
    for text, url in raw_links:
        text_clean = text.strip()
        if not text_clean or text_clean.lower() in skip_terms:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        links.append({"text": text_clean, "url": url})
        if len(links) >= max_links:
            break
    return links


def extract_trust_signals(scraped_content: str) -> str:
    """Looks for a real rating (e.g. '5.0 Rating') in the scraped content so
    it can be surfaced as a genuine trust badge instead of silently dropped."""
    if not scraped_content:
        return ""
    rating_match = re.search(r'(\d\.\d)\s*Rating', scraped_content)
    if rating_match:
        return f"Real rating found on their site: {rating_match.group(1)} stars -- use this as a genuine trust badge if it fits the design."
    return ""


def build_messages(
    agency_name: str,
    phone: str | None,
    address: str | None,
    website: str | None,
    scraped_content: str,
    persona_summary: str,
    agency_id: str = "",
    style_notes: str | None = None,
    layout_hint: str | None = None,
    api_base_url: str = "http://127.0.0.1:8000",
) -> list[dict]:
    import random

    style_notes_block = f"Additional style direction from the user: {style_notes}" if style_notes else ""
    chosen_hint = layout_hint or random.choice(LAYOUT_HINTS)
    whatsapp_link = build_whatsapp_link(phone)
    real_links = extract_real_links(scraped_content)
    real_links_text = "\n".join(f'- "{l["text"]}" -> {l["url"]}' for l in real_links) or "No real links found in scraped content."
    trust_signals = extract_trust_signals(scraped_content)
    listings_text = format_listings_for_prompt()

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                agency_name=agency_name,
                phone=phone or "not provided",
                address=address or "not provided",
                website=website or "unknown",
                whatsapp_link=whatsapp_link or "not available (no phone number on file)",
                scraped_content=scraped_content[:8000],
                real_links=real_links_text,
                trust_signals=trust_signals,
                persona_summary=persona_summary[:4000],
                listings=listings_text,
                style_notes_block=style_notes_block,
                layout_hint=chosen_hint,
                hero_video_url=HERO_VIDEO_URL,
                section_video_url=SECTION_VIDEO_URL,
                calendly_url=CALENDLY_URL,
                api_base_url=api_base_url,
                agency_id_value=agency_id,
            ),
        },
    ]


def summarize_persona_for_codegen(sections: dict) -> str:
    """Pull just the design-relevant sections out of the full 17-section persona
    so we don't blow the prompt budget with irrelevant sections (e.g. competitor
    landscape isn't useful for a design prompt)."""
    relevant_keys = [
        "identity_snapshot",
        "core_expertise_focus",
        "brand_voice_matrix",
        "audience_persona",
        "digital_presence",
        "content_strategy",
    ]
    lines = []
    for key in relevant_keys:
        section = sections.get(key)
        if section and section.get("content"):
            lines.append(f"{key}: {section['content']}")
    return "\n".join(lines)


def build_lovable_prompt(
    agency_name: str,
    phone: str | None,
    address: str | None,
    persona_summary: str,
    scraped_content: str = "",
    screenshot_url: str | None = None,
    agency_id: str = "",
    style_notes: str | None = None,
    api_base_url: str = "http://127.0.0.1:8000",
) -> str:
    """Prompt for Open Lovable's generate-ai-code-stream endpoint. Its own
    system prompt already handles React/Tailwind/component-structure rules --
    this only needs to supply brand-specific direction on top of that."""
    style_notes_line = f"\nAdditional direction: {style_notes}" if style_notes else ""
    whatsapp_link = build_whatsapp_link(phone)
    whatsapp_line = (
        f"\nInclude a floating WhatsApp contact button (fixed bottom-right, visible on scroll) "
        f"linking to {whatsapp_link} -- this must be the agency's own real number, never a placeholder."
        if whatsapp_link else ""
    )
    real_links = extract_real_links(scraped_content)
    real_links_text = "\n".join(f'- "{l["text"]}" -> {l["url"]}' for l in real_links) or "No real links found."
    trust_signals = extract_trust_signals(scraped_content)
    listings_text = format_listings_for_prompt()
    image_line = ""  # intentionally disabled: Firecrawl's screenshot is a screenshot of
    # their existing webpage (with its own headline/nav text baked into the
    # pixels), not a clean photograph -- using it as a hero background caused
    # duplicate-looking overlapping text. Revisit with a real photo source
    # (e.g. Unsplash) instead if a hero image is wanted later.

    return f"""Recreate this real estate agency's website as a modern, polished React app.

Agency: {agency_name}
Phone: {phone or 'not provided'}
Address: {address or 'not provided'}

Brand positioning and tone to reflect (from their persona document):
{persona_summary}

Real functional links found on their current site -- use these EXACT urls
for corresponding buttons/nav items, never a dead '#':
{real_links_text}

{trust_signals}

FEATURED LISTINGS (SAMPLE/PLACEHOLDER DATA -- illustrative demo listings,
not the agency's real current inventory). Render as a "Featured Listings"
grid section: a photo, status badge, price, address, and bed/bath/sqft per
card, styled like a professional MLS listing grid. Add a small "Sample
Listing" label per card or a section note. Use the exact photo URLs given.
{listings_text}

VIDEO REQUIREMENTS:
- Hero section: full-bleed background <video autoplay muted loop
  playsInline> with src="{HERO_VIDEO_URL}" (a real, verified, free-to-use
  stock video -- do not substitute a different URL). Add a dark
  semi-transparent overlay for text contrast.
- One additional section further down with an embedded <video controls>
  (not autoplay) using src="{SECTION_VIDEO_URL}", framed as "See Inside" or
  "Take a Tour".

LEAD CAPTURE FORM: include a detailed contact form (Full Name, Email,
Phone, Message textarea). On submit, use fetch() with
event.preventDefault() to POST JSON to "{api_base_url}/leads" with body
{{"agency_id": "{agency_id}", "name": <value>, "email": <value>, "phone":
<value>, "message": <value>, "source": "website_form"}}. Show a success
message on 200, an error message otherwise.

BOOKING WIDGET (SAMPLE/PLACEHOLDER -- a demo booking calendar, not the
agency's real scheduling system). Include a "Book a Consultation" section
embedding this exact Calendly widget:
<link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">
<script src="https://assets.calendly.com/assets/external/widget.js" async></script>
<div class="calendly-inline-widget" data-url="{CALENDLY_URL}" style="min-width:320px;height:630px;"></div>
Add a small "Sample booking calendar" label near this section.

Use ONLY real details above and whatever appears in the scraped website content
already provided in context -- do not invent testimonials, agent names, or
stats. Avoid a generic dark-hero-plus-three-cards layout; make deliberate,
distinctive structural and color choices that fit this agency's specific
brand tone.

PREMIUM DESIGN REQUIREMENTS: layered surfaces (not flat white/gray
everywhere), generous section padding (80-120px), a real typographic scale
with bold display headlines against light body text, soft layered shadows
on cards, and smooth hover/transition micro-interactions on every
interactive element.

LAYOUT SAFETY: keep every section in normal document flow, one after
another -- do not stack components on top of each other with absolute/fixed
positioning in a way that causes overlapping text or elements. Only the
WhatsApp button should be fixed-positioned.

NO FAKE FUNCTIONALITY: do not build a property search bar, filter dropdowns,
or a search input for listings -- just display the featured listings grid
directly.{image_line}{whatsapp_line}{style_notes_line}"""