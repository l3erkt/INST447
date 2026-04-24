"""
fetch_congress.py — Fetch legislative data from the Congress.gov API.

For each target legislator, retrieves:
  1. Sponsored legislation, counted by policy area
  2. Co-sponsored legislation, counted by policy area
  3. Committee assignments

Output: data/legislation.csv
"""

import os
import time
import requests
import pandas as pd

from config import (
    API_KEY, CONGRESS_BASE_URL, CONGRESS_NUMBER, CONGRESS_REQUEST_DELAY,
    INDUSTRY_POLICY_AREAS, TARGET_LEGISLATORS,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_CSV = os.path.join(DATA_DIR, "legislation.csv")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _congress_get(endpoint: str, params: dict | None = None) -> dict | None:
    """Make a GET request to the Congress.gov API with rate-limiting."""
    if params is None:
        params = {}
    params["api_key"] = API_KEY
    params["format"] = "json"
    url = f"{CONGRESS_BASE_URL}{endpoint}"
    time.sleep(CONGRESS_REQUEST_DELAY)
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  ⚠  Congress API error: {e}")
        return None


def fetch_sponsored_legislation(bioguide_id: str) -> list[dict]:
    """
    Fetch all bills sponsored by a member.  Paginates through results.
    Returns a list of bill dicts.
    """
    all_bills = []
    offset = 0
    limit = 250

    while True:
        data = _congress_get(
            f"/member/{bioguide_id}/sponsored-legislation",
            {"offset": offset, "limit": limit},
        )
        if not data:
            break

        bills = data.get("sponsoredLegislation", [])
        if not bills:
            break

        all_bills.extend(bills)
        offset += limit

        # Check if there are more pages
        pagination = data.get("pagination", {})
        total = pagination.get("count", 0)
        if offset >= total:
            break

    return all_bills


def fetch_cosponsored_legislation(bioguide_id: str) -> list[dict]:
    """
    Fetch all bills co-sponsored by a member.  Paginates through results.
    """
    all_bills = []
    offset = 0
    limit = 250

    while True:
        data = _congress_get(
            f"/member/{bioguide_id}/cosponsored-legislation",
            {"offset": offset, "limit": limit},
        )
        if not data:
            break

        bills = data.get("cosponsoredLegislation", [])
        if not bills:
            break

        all_bills.extend(bills)
        offset += limit

        pagination = data.get("pagination", {})
        total = pagination.get("count", 0)
        if offset >= total:
            break

    return all_bills


def fetch_bill_detail(congress: int, bill_type: str, bill_number: str) -> dict | None:
    """
    Fetch detailed info for a single bill, including policyArea.
    Used as fallback when the list endpoint doesn't include policyArea.
    """
    data = _congress_get(f"/bill/{congress}/{bill_type}/{bill_number}")
    if data:
        return data.get("bill", {})
    return None


def count_bills_by_policy(bills: list[dict], target_areas: list[str]) -> tuple[int, int]:
    """
    Count how many bills match the target policy areas.
    Returns (matching_count, total_count).
    """
    matching = 0
    total = len(bills)
    for bill in bills:
        policy = bill.get("policyArea", {})
        if policy and policy.get("name") in target_areas:
            matching += 1
    return matching, total


def fetch_member_details(bioguide_id: str) -> dict | None:
    """Fetch member bio and committee details."""
    data = _congress_get(f"/member/{bioguide_id}")
    if data:
        return data.get("member", {})
    return None


# ── Main Collection ───────────────────────────────────────────────────────────

def fetch_all_legislation() -> pd.DataFrame:
    """
    For every target legislator × industry, count how many sponsored and
    co-sponsored bills match the industry's policy areas.
    """
    if os.path.exists(OUTPUT_CSV):
        print(f"✓ Cached legislation data found at {OUTPUT_CSV}")
        return pd.read_csv(OUTPUT_CSV)

    rows = []
    total = len(TARGET_LEGISLATORS)

    for i, leg in enumerate(TARGET_LEGISLATORS, 1):
        bio = leg["bioguide_id"]
        name = leg["name"]
        print(f"\n[{i}/{total}] {name} ({leg['party']}-{leg['state']}) [{bio}]")

        # Fetch sponsored legislation
        print("  Fetching sponsored bills...")
        sponsored = fetch_sponsored_legislation(bio)
        print(f"    → {len(sponsored)} sponsored bills")

        # Fetch co-sponsored legislation
        print("  Fetching co-sponsored bills...")
        cosponsored = fetch_cosponsored_legislation(bio)
        print(f"    → {len(cosponsored)} co-sponsored bills")

        # Count by industry-relevant policy areas
        for industry, areas in INDUSTRY_POLICY_AREAS.items():
            matched_sponsored, total_sponsored = count_bills_by_policy(sponsored, areas)
            matched_cosponsored, total_cosponsored = count_bills_by_policy(cosponsored, areas)

            on_relevant_committee = any(
                c in leg.get("committees", [])
                for c in _get_relevant_committees(industry)
            )

            print(f"  {industry}: {matched_sponsored}S + {matched_cosponsored}C bills matched")

            rows.append({
                "legislator_name": name,
                "bioguide_id": bio,
                "party": leg["party"],
                "state": leg["state"],
                "committees": ", ".join(leg.get("committees", [])),
                "industry": industry,
                "policy_areas_checked": ", ".join(areas),
                "bills_sponsored_relevant": matched_sponsored,
                "bills_cosponsored_relevant": matched_cosponsored,
                "total_relevant_bills": matched_sponsored + matched_cosponsored,
                "total_bills_sponsored": total_sponsored,
                "total_bills_cosponsored": total_cosponsored,
                "on_relevant_committee": on_relevant_committee,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✓ Saved {len(df)} records to {OUTPUT_CSV}")
    return df


def _get_relevant_committees(industry: str) -> list[str]:
    """Map industry to the relevant congressional committees."""
    mapping = {
        "Fossil Fuels": ["Energy and Commerce"],
        "Data Centers / Tech": ["Science, Space, and Technology", "Energy and Commerce"],
        "Defense / Iran": ["Armed Services"],
    }
    return mapping.get(industry, [])


if __name__ == "__main__":
    df = fetch_all_legislation()
    print(f"\nPreview:\n{df.head(10)}")
