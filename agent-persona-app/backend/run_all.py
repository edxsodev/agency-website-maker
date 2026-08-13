"""
Runs the full pipeline (persona -> site) for every agency currently in the
database, and prints a summary you can screenshot/share as a progress demo.

Usage (from the backend/ folder, with the server running in another terminal):

    python run_all.py
"""
import time
import requests

API_BASE = "http://127.0.0.1:8000"


def run_via_api():
    print("Fetching all agencies...")
    resp = requests.post(f"{API_BASE}/discovery", json={"location": "", "max_results": 50})
    if resp.status_code != 200:
        print(f"Discovery call failed: {resp.status_code} {resp.text[:300]}")
        return

    agencies = resp.json().get("agencies", [])
    if not agencies:
        print("No agencies found. Did you run db/seed_data.py?")
        return

    results = []
    for agency in agencies:
        agency_id = agency["id"]
        name = agency["name"]
        print(f"\n=== {name} ===")

        print("  Generating persona...")
        try:
            p = requests.post(f"{API_BASE}/persona/generate", json={"agency_id": agency_id}, timeout=120)
            if p.status_code != 200:
                print(f"  Persona FAILED: {p.status_code} {p.text[:300]}")
                continue
            persona = p.json()
            print(f"  Persona OK (confidence: {persona['data_confidence']})")
        except Exception as e:
            print(f"  Persona ERROR: {e}")
            continue

        print("  Generating site...")
        try:
            s = requests.post(f"{API_BASE}/site-gen/generate", json={"agency_id": agency_id, "style_notes": ""}, timeout=180)
            if s.status_code != 200:
                print(f"  Site FAILED: {s.status_code} {s.text[:300]}")
                continue
            print(f"  Site OK -> preview at {API_BASE}/site-gen/{agency_id}/preview")
        except Exception as e:
            print(f"  Site ERROR: {e}")
            continue

        results.append({"name": name, "agency_id": agency_id, "preview_url": f"{API_BASE}/site-gen/{agency_id}/preview"})
        time.sleep(1)  # be polite to free-tier rate limits

    print("\n\n========== SUMMARY ==========")
    for r in results:
        print(f"{r['name']}: {r['preview_url']}")


if __name__ == "__main__":
    run_via_api()