"""
Run once against a fresh Supabase project to seed the 5 real agencies
you provided. Usage:

    python -m db.seed_data
"""
from db.client import get_supabase

AGENCIES = [
    {
        "name": "Realty Texas",
        "website": "https://realtytexas.com",
        "phone": "+1 512-476-5348",
        "address": "2000 S I-35 Frontage Rd Ste P, Round Rock, TX 78681, United States",
        "city": "Round Rock",
        "state": "TX",
    },
    {
        "name": "Gone to Texas RE",
        "website": "https://gonetotexasre.com",
        "phone": "+1 512-910-5294",
        "address": None,
        "city": None,
        "state": "TX",
    },
    {
        "name": "TX RE Brokers",
        "website": "https://txrealestatebrokers.com",
        "phone": "+1 512-948-3366",
        "address": "2804 Hunter Rd, San Marcos, TX 78666, United States",
        "city": "San Marcos",
        "state": "TX",
    },
    {
        "name": "Torrey McGraw and Keela McGraw",
        "website": "https://mcgrawtx.com",
        "phone": "+1 817-696-9208",
        "address": None,
        "city": None,
        "state": "TX",
    },
    {
        "name": "League RE",
        "website": "https://leaguere.com",
        "phone": "+1 817-523-9113",
        "address": "5220 Locke Ave, Fort Worth, TX 76107, United States",
        "city": "Fort Worth",
        "state": "TX",
    },
]


def seed():
    sb = get_supabase()
    for agency in AGENCIES:
        sb.table("agencies").upsert(agency, on_conflict="website").execute()
        print(f"Seeded: {agency['name']}")


if __name__ == "__main__":
    seed()
