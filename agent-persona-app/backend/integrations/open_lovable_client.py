"""
Bridge to a running Open Lovable instance (self-hosted separately at
OPEN_LOVABLE_BASE_URL, default http://localhost:3000). Open Lovable is a
full Next.js app with its own chat UI -- this client calls its internal
API routes directly to drive the same scrape -> generate -> apply workflow
headlessly, without a human in its chat interface.
"""
import os
import re
import json
import time
import requests

OPEN_LOVABLE_BASE_URL = os.environ.get("OPEN_LOVABLE_BASE_URL", "http://localhost:3000")


def scrape_url(url: str) -> dict:
    resp = requests.post(f"{OPEN_LOVABLE_BASE_URL}/api/scrape-url-enhanced", json={"url": url}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Open Lovable scrape failed: {data.get('error')}")
    return data


def create_sandbox() -> dict:
    resp = requests.post(f"{OPEN_LOVABLE_BASE_URL}/api/create-ai-sandbox-v2", timeout=120)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Sandbox creation failed: {data.get('error')}")
    return data


def generate_code(prompt: str, sandbox_id: str, scraped: dict, model: str = "google/gemini-3-flash-preview") -> dict:
    """Calls the streaming endpoint and consumes the SSE stream to completion,
    returning the final 'complete' event payload (contains generatedCode as
    raw text with <file path="..."> blocks inside)."""
    payload = {
        "prompt": prompt,
        "model": model,
        "isEdit": False,
        "context": {
            "sandboxId": sandbox_id,
            "conversationContext": {
                "scrapedWebsites": [
                    {
                        "url": scraped.get("url"),
                        "timestamp": int(time.time() * 1000),
                        "content": scraped.get("content"),
                    }
                ]
            },
        },
    }
    resp = requests.post(
        f"{OPEN_LOVABLE_BASE_URL}/api/generate-ai-code-stream",
        json=payload,
        stream=True,
        timeout=300,
    )
    resp.raise_for_status()

    complete_event = None
    for raw_line in resp.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data: "):
            continue
        chunk = raw_line[len("data: "):]
        try:
            event = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "complete":
            complete_event = event
            break
        if event.get("type") == "error":
            raise RuntimeError(f"Open Lovable generation error: {event.get('error')}")

    if not complete_event:
        raise RuntimeError("Stream ended without a 'complete' event -- generation likely failed or timed out.")

    generated_code = complete_event.get("generatedCode", "")
    if "<file path=" not in generated_code:
        raise RuntimeError(
            f"Generation completed but produced no usable code (likely failed silently). "
            f"Raw response preview: {generated_code[:300]!r}"
        )
    return complete_event


def apply_code(generated_code: str, sandbox_id: str) -> dict:
    """Writes the generated <file> blocks into the running sandbox.

    ASSUMPTION TO VERIFY: this calls an endpoint assumed to be named
    `/api/apply-ai-code`, accepting {"response": generated_code, "sandboxId":
    sandbox_id}, based on the project's naming conventions seen elsewhere
    (get-sandbox-files, analyze-edit-intent). If this 404s or errors, open
    `app/api/apply-ai-code/route.ts` in the cloned open-lovable repo and
    confirm the actual route name + expected field names, then adjust the
    `json=` payload below accordingly.
    """
    resp = requests.post(
        f"{OPEN_LOVABLE_BASE_URL}/api/apply-ai-code",
        json={"response": generated_code, "sandboxId": sandbox_id},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def parse_files(generated_code: str) -> list[dict]:
    """Local fallback parser for the <file path="...">content</file> blocks,
    mirroring the regex Open Lovable uses server-side -- useful for logging
    what was generated even independent of the apply step."""
    files = []
    for m in re.finditer(r'<file path="([^"]+)">([\s\S]*?)</file>', generated_code):
        files.append({"path": m.group(1), "content": m.group(2).strip()})
    return files

def get_sandbox_files() -> dict:
    """Fetches the current file tree + contents from the active sandbox.
    Based on the route being called elsewhere in Open Lovable's own code
    (generate-ai-code-stream references it) as a GET with no body, returning
    {success, files: {path: content}, manifest}."""
    resp = requests.get(f"{OPEN_LOVABLE_BASE_URL}/api/get-sandbox-files", timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Failed to fetch sandbox files: {data.get('error')}")
    return data