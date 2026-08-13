"""
Thin client for the BrandBoost API (blog generation + SEO tooling).
UNLIKE the rest of this stack, this is a PAID service (~$0.002-$0.03 per
generated post depending on length/model) -- call it deliberately, never
in a bulk/automated loop.
"""
import os
import requests

BASE_URL = os.environ.get("BRANDBOOST_BASE_URL", "https://redaction.in/api/v1")


def _headers() -> dict:
    return {
        "X-API-Key": os.environ["BRANDBOOST_API_KEY"],
        "Content-Type": "application/json",
    }


def get_settings() -> dict:
    resp = requests.get(f"{BASE_URL}/client/settings", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def update_settings(settings: dict) -> dict:
    resp = requests.post(f"{BASE_URL}/client/settings", headers=_headers(), json=settings, timeout=30)
    resp.raise_for_status()
    return resp.json()


def suggest_topics(agency_name: str, agency_location: str, services: str, target_audience: str, count: int = 10) -> dict:
    payload = {
        "agencyName": agency_name,
        "agencyLocation": agency_location,
        "services": services,
        "targetAudience": target_audience,
        "count": count,
    }
    resp = requests.post(f"{BASE_URL}/brandboost/suggest-topics", headers=_headers(), json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def generate_post(
    agency_name: str,
    agency_location: str,
    topic: str,
    tone: str,
    target_audience: str,
    post_type: str = "blog",
    length: str = "medium",
    include_cta: bool = True,
) -> dict:
    payload = {
        "agencyName": agency_name,
        "agencyLocation": agency_location,
        "topic": topic,
        "postType": post_type,
        "length": length,
        "tone": tone,
        "targetAudience": target_audience,
        "includeCta": include_cta,
    }
    resp = requests.post(f"{BASE_URL}/brandboost/generate-post", headers=_headers(), json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def analyze_seo(content: str, topic_label: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/brandboost/analyze-seo",
        headers=_headers(),
        json={"content": content, "topicLabel": topic_label},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def optimize_seo(content: str, topic_label: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/brandboost/optimize-seo",
        headers=_headers(),
        json={"content": content, "topicLabel": topic_label},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()


def analyze_ai_detection(content: str, topic_label: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/brandboost/analyze-ai-detection",
        headers=_headers(),
        json={"content": content, "topicLabel": topic_label},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def humanize_post(content: str, topic_label: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/brandboost/humanize-post",
        headers=_headers(),
        json={"content": content, "topicLabel": topic_label},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()