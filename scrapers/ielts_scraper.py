#!/usr/bin/env python3
"""
Keystone IELTS Institute Scraper
Scrapes IELTS coaching centers from Bangladesh tier-2/3 districts
for B2B partnership outreach.

Usage: python ielts_scraper.py --district narsingdi,gazipur,mymensingh
"""

import requests
import json
import csv
import time
import argparse
from urllib.parse import urlencode

# Google Places API (free tier: $200 credit/month = ~10,000 requests)
# Alternative: Use Google Maps scraping without API key
API_KEY = "YOUR_GOOGLE_PLACES_API_KEY"  # Replace with actual key

TIER_2_3_DISTRICTS = [
    "Gazipur", "Narsingdi", "Mymensingh", "Tangail", "Kishoreganj",
    "Jamalpur", "Sherpur", "Netrokona", "Rajbari", "Manikganj",
    "Munshiganj", "Narayanganj", "Faridpur", "Madaripur", "Gopalganj",
    "Shariatpur", "Chandpur", "Lakshmipur", "Noakhali", "Feni",
    "Brahmanbaria", "Comilla", "Chandpur", "Cox's Bazar", "Bandarban",
    "Rangamati", "Khagrachari", "Patuakhali", "Bhola", "Barisal",
    "Pirojpur", "Jhalokati", "Barguna", "Pabna", "Sirajganj",
    "Natore", "Naogaon", "Nawabganj", "Bogra", "Rajshahi",
    "Dinajpur", "Thakurgaon", "Panchagarh", "Nilphamari", "Lalmonirhat",
    "Kurigram", "Rangpur", "Gaibandha", "Joypurhat", "Meherpur",
    "Kushtia", "Chuadanga", "Jhenaidah", "Magura", "Narail",
    "Jessore", "Satkhira", "Khulna", "Bagerhat"
]

SEARCH_KEYWORDS = [
    "IELTS coaching",
    "IELTS preparation",
    "IELTS center",
    "English language training",
    "Spoken English",
    "British Council partner",
    "IDP IELTS",
    "English coaching center"
]


def search_places(district, keyword, api_key):
    """Search Google Places for IELTS institutes in a district."""
    query = f"{keyword} {district} Bangladesh"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": api_key,
        "region": "bd"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"Error searching {district}: {e}")
        return []


def get_place_details(place_id, api_key):
    """Get detailed info including phone, website, hours."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,rating,user_ratings_total",
        "key": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        return data.get("result", {})
    except Exception as e:
        print(f"Error getting details for {place_id}: {e}")
        return {}


def scrape_district(district, api_key, delay=1):
    """Scrape all IELTS institutes in one district."""
    results = []
    seen = set()

    for keyword in SEARCH_KEYWORDS:
        places = search_places(district, keyword, api_key)
        for place in places:
            place_id = place.get("place_id")
            if place_id in seen:
                continue
            seen.add(place_id)

            details = get_place_details(place_id, api_key)

            record = {
                "district": district,
                "name": place.get("name", ""),
                "address": details.get("formatted_address", place.get("formatted_address", "")),
                "phone": details.get("formatted_phone_number", ""),
                "website": details.get("website", ""),
                "rating": details.get("rating", ""),
                "total_reviews": details.get("user_ratings_total", ""),
                "place_id": place_id,
                "search_keyword": keyword,
                "keystone_status": "NOT_CONTACTED",
                "contact_date": "",
                "contact_person": "",
                "notes": "",
                "referral_count": 0,
                "commission_paid": 0
            }
            results.append(record)
            time.sleep(delay)

    return results


def scrape_all(districts=None, api_key=None, output_file="ielts_institutes.csv"):
    """Main scraper function."""
    if api_key is None or api_key == "YOUR_GOOGLE_PLACES_API_KEY":
        print("⚠️  WARNING: No Google Places API key provided.")
        print("   Options:")
        print("   1. Get a free key at https://developers.google.com/maps/documentation/places/web-service")
        print("   2. Use the manual_fallback() function to scrape from Facebook/Google manually")
        print("   3. Use the bdjobs_scraper approach for local listings")
        return []

    districts = districts or TIER_2_3_DISTRICTS
    all_results = []

    for district in districts:
        print(f"🔍 Scraping {district}...")
        results = scrape_district(district, api_key)
        all_results.extend(results)
        print(f"   Found {len(results)} institutes in {district}")
        time.sleep(2)

    # Save to CSV
    if all_results:
        keys = all_results[0].keys()
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"\n✅ Saved {len(all_results)} institutes to {output_file}")

    return all_results


def manual_fallback():
    """
    Manual fallback: Use Facebook search + Google Maps manual scraping
    without API key. Marina can run this from her phone.
    """
    print("""
    📱 MANUAL SCRAPING GUIDE (No API Key Needed)
    =============================================

    Step 1: Open Facebook on your phone
    Step 2: Search: "IELTS coaching [DISTRICT NAME]"
    Step 3: Click "Pages" tab
    Step 4: For each page:
        - Screenshot the page name
        - Click "About" → copy phone number
        - Click "About" → copy address
        - Note: Page likes (popularity indicator)
    Step 5: Save to this Google Sheet: [LINK]

    Step 6: Open Google Maps
    Step 7: Search: "IELTS coaching near me" (in each district)
    Step 8: For each result:
        - Name
        - Address
        - Phone (if listed)
        - Website (if listed)
        - Rating
    Step 9: Add to same sheet

    TARGET: 10 institutes per district
    TIME: 30 minutes per district
    """")


def bdjobs_scraper_approach():
    """
    Alternative: Scrape bdjobs.com for English teacher/coaching center listings
    This finds IELTS instructors who may be connected to centers.
    """
    print("""
    🌐 BDJOBS SCRAPER APPROACH
    ===========================

    bdjobs.com has job postings for:
    - "IELTS Instructor"
    - "English Teacher"
    - "Spoken English Trainer"

    Each job posting has:
    - Company name (the institute)
    - Location
    - Contact info

    This is a BACKDOOR to finding IELTS centers that are actively hiring.
    Active hiring = growing business = more students = better partner.

    Use the existing bdjobs scraper skill and adapt the search terms.
    """)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keystone IELTS Institute Scraper")
    parser.add_argument("--districts", help="Comma-separated district names")
    parser.add_argument("--api-key", help="Google Places API key")
    parser.add_argument("--output", default="ielts_institutes.csv", help="Output CSV file")
    parser.add_argument("--manual", action="store_true", help="Show manual fallback guide")
    parser.add_argument("--bdjobs", action="store_true", help="Show bdjobs approach")

    args = parser.parse_args()

    if args.manual:
        manual_fallback()
    elif args.bdjobs:
        bdjobs_scraper_approach()
    else:
        districts = args.districts.split(",") if args.districts else None
        scrape_all(districts=districts, api_key=args.api_key, output_file=args.output)
