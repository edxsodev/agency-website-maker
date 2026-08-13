"""
Sample/placeholder property listings, used to populate the "Featured
Listings" section on generated agency sites. These are illustrative demo
data, NOT real inventory -- explicitly labeled as such in generation
prompts and in the rendered UI, since presenting invented listings as real
would be misleading once a real agency looks at this.

Photos: Picsum (picsum.photos) seeded placeholder photography -- real
stock photos, but not photos of the actual (fictional) addresses below.
"""

SAMPLE_LISTINGS = [
    {
        "id": "L001", "status": "Active", "listing_type": "For Sale",
        "price": 379000, "address": "116 Hares Foot Cove", "city": "Georgetown",
        "state": "TX", "zip": "78626", "subdivision": "Carlson Place",
        "beds": 3, "baths": 2.5, "sqft": 2121, "year_built": 2020,
        "lot_size": "0.14 acres", "hoa_fee": "$29/month",
        "description": "Two-story home with open-concept living, a home office, "
                        "and a versatile upstairs game room. Granite counters, "
                        "vinyl plank flooring, and a covered patio.",
        "photo_seed": "listing-georgetown-1",
    },
    {
        "id": "L002", "status": "Active", "listing_type": "For Sale",
        "price": 549000, "address": "156 Great Frontier Drive", "city": "Georgetown",
        "state": "TX", "zip": "78633", "subdivision": "Wolf Ranch",
        "beds": 3, "baths": 2, "sqft": 2461, "year_built": 2019,
        "lot_size": "0.19 acres", "hoa_fee": "$45/month",
        "description": "Stone-and-brick single story on a mature, tree-shaded lot. "
                        "Open kitchen with island seating and a private primary suite.",
        "photo_seed": "listing-georgetown-2",
    },
    {
        "id": "L003", "status": "Active", "listing_type": "For Sale",
        "price": 875000, "address": "120 W Vienna Drive", "city": "Hutto",
        "state": "TX", "zip": "78634", "subdivision": "Vienna Estates",
        "beds": 4, "baths": 3, "sqft": 3375, "year_built": 2021,
        "lot_size": "0.6 acres", "hoa_fee": "N/A",
        "description": "Sprawling single-story estate home on a large corner lot "
                        "with mature trees and a circular drive.",
        "photo_seed": "listing-hutto-1",
    },
    {
        "id": "L004", "status": "Active", "listing_type": "For Lease",
        "price": 2200, "address": "4410 Sunfield Trail", "city": "Round Rock",
        "state": "TX", "zip": "78681", "subdivision": "Sunfield",
        "beds": 3, "baths": 2, "sqft": 1850, "year_built": 2018,
        "lot_size": "0.15 acres", "hoa_fee": "Included",
        "description": "Move-in ready single story with a fenced backyard, "
                        "open living/dining, and a two-car garage. $2,200/month.",
        "photo_seed": "listing-roundrock-1",
    },
    {
        "id": "L005", "status": "Pending", "listing_type": "For Sale",
        "price": 425000, "address": "2201 Rabbit Hill Road", "city": "Round Rock",
        "state": "TX", "zip": "78665", "subdivision": "Behrens Ranch",
        "beds": 4, "baths": 2.5, "sqft": 2560, "year_built": 2016,
        "lot_size": "0.18 acres", "hoa_fee": "$38/month",
        "description": "Family home with a bright open floor plan, upstairs "
                        "media room, and a covered back patio.",
        "photo_seed": "listing-roundrock-2",
    },
    {
        "id": "L006", "status": "Active", "listing_type": "For Sale",
        "price": 315000, "address": "812 Comal Street", "city": "San Marcos",
        "state": "TX", "zip": "78666", "subdivision": "Downtown San Marcos",
        "beds": 2, "baths": 2, "sqft": 1420, "year_built": 2015,
        "lot_size": "0.08 acres", "hoa_fee": "N/A",
        "description": "Walkable downtown bungalow near the river, updated "
                        "kitchen, and a private backyard patio.",
        "photo_seed": "listing-sanmarcos-1",
    },
    {
        "id": "L007", "status": "Active", "listing_type": "For Lease",
        "price": 1650, "address": "305 Hunter Meadow Lane", "city": "San Marcos",
        "state": "TX", "zip": "78666", "subdivision": "Hunter Ridge",
        "beds": 2, "baths": 1.5, "sqft": 1180, "year_built": 2012,
        "lot_size": "0.05 acres", "hoa_fee": "Included",
        "description": "Townhome-style lease with attached garage, community "
                        "pool access, and low-maintenance living. $1,650/month.",
        "photo_seed": "listing-sanmarcos-2",
    },
    {
        "id": "L008", "status": "Active", "listing_type": "For Sale",
        "price": 289000, "address": "1740 Locke Avenue", "city": "Fort Worth",
        "state": "TX", "zip": "76107", "subdivision": "West 7th",
        "beds": 3, "baths": 2, "sqft": 1680, "year_built": 1998,
        "lot_size": "0.12 acres", "hoa_fee": "N/A",
        "description": "Charming craftsman near West 7th's dining and shopping, "
                        "with original hardwood floors and a renovated kitchen.",
        "photo_seed": "listing-fortworth-1",
    },
    {
        "id": "L009", "status": "Active", "listing_type": "For Sale",
        "price": 612000, "address": "3390 Crestline Road", "city": "Fort Worth",
        "state": "TX", "zip": "76107", "subdivision": "Crestline",
        "beds": 4, "baths": 3, "sqft": 2980, "year_built": 2005,
        "lot_size": "0.22 acres", "hoa_fee": "N/A",
        "description": "Two-story traditional with a formal dining room, "
                        "updated primary bath, and a pool-ready backyard.",
        "photo_seed": "listing-fortworth-2",
    },
    {
        "id": "L010", "status": "Active", "listing_type": "For Lease",
        "price": 1950, "address": "918 Magnolia Court", "city": "Fort Worth",
        "state": "TX", "zip": "76104", "subdivision": "Fairmount",
        "beds": 2, "baths": 1, "sqft": 1120, "year_built": 1948,
        "lot_size": "0.1 acres", "hoa_fee": "N/A",
        "description": "Restored historic cottage in the Fairmount district, "
                        "original details with modern systems. $1,950/month.",
        "photo_seed": "listing-fortworth-3",
    },
    {
        "id": "L011", "status": "Active", "listing_type": "For Sale",
        "price": 465000, "address": "77 Cedar Bend Circle", "city": "Austin",
        "state": "TX", "zip": "78745", "subdivision": "Cedar Bend",
        "beds": 3, "baths": 2, "sqft": 1890, "year_built": 2010,
        "lot_size": "0.16 acres", "hoa_fee": "$20/month",
        "description": "South Austin single story with a shaded backyard deck, "
                        "open kitchen, and a short commute downtown.",
        "photo_seed": "listing-austin-1",
    },
    {
        "id": "L012", "status": "Active", "listing_type": "For Sale",
        "price": 398000, "address": "540 Live Oak Lane", "city": "Georgetown",
        "state": "TX", "zip": "78628", "subdivision": "Live Oak",
        "beds": 3, "baths": 2, "sqft": 1975, "year_built": 2017,
        "lot_size": "0.14 acres", "hoa_fee": "$32/month",
        "description": "Bright single-story with a split floor plan, covered "
                        "front porch, and community walking trails nearby.",
        "photo_seed": "listing-georgetown-3",
    },
]


def format_listings_for_prompt(max_listings: int = 12) -> str:
    """Renders listings as compact text for inclusion in an LLM prompt."""
    lines = []
    for listing in SAMPLE_LISTINGS[:max_listings]:
        price_str = f"${listing['price']:,}" + ("/month" if listing["listing_type"] == "For Lease" else "")
        photo_url = f"https://picsum.photos/seed/{listing['photo_seed']}/800/600"
        lines.append(
            f"- ID {listing['id']} | {listing['status']} | {listing['listing_type']} | {price_str} | "
            f"{listing['address']}, {listing['city']}, {listing['state']} {listing['zip']} | "
            f"{listing['beds']} bd / {listing['baths']} ba / {listing['sqft']} sqft | "
            f"Built {listing['year_built']} | Lot {listing['lot_size']} | HOA {listing['hoa_fee']} | "
            f"Photo: {photo_url} | {listing['description']}"
        )
    return "\n".join(lines)