"""
Piper Voice Bot Provisioning Client.
Connects agency-website-maker to Piper Engine (Workflow-Voice).
"""
import os
import requests

PIPER_API_URL = os.environ.get("PIPER_API_URL", "http://127.0.0.1:3101")


def provision_agency_voice_bot(agency_id: str, agency_name: str, call_bot_prompt: str, website: str = None) -> dict:
    """Provisions a dedicated inbound DID and voice workflow for the agency."""
    url = f"{PIPER_API_URL}/api/v1/voice-agents/provision"
    payload = {
        "agency_id": str(agency_id),
        "agency_name": agency_name,
        "website": website,
        "call_bot_prompt": call_bot_prompt,
    }
    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[piper_client] Provision failed: {e}")
    return {"status": "error", "did_number": None}
