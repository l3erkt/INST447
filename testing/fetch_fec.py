"""
fetch_fec.py — Fetch PAC → Candidate contribution data from the OpenFEC API.

Strategy:
  1. Resolve each legislator's FEC candidate_id
  2. Find the candidate's principal campaign committee
  3. Use Schedule A to find receipts TO that committee FROM each industry PAC
     (filtered by contributor_id = PAC committee_id)
  4. Also fetch aggregate candidate totals for context

Output: data/donations.csv
"""

import os
import time
import requests
import pandas as pd

from config import (
    API_KEY, FEC_BASE_URL, ELECTION_CYCLE, FEC_REQUEST_DELAY,
    INDUSTRY_PACS, TARGET_LEGISLATORS,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_CSV = os.path.join(DATA_DIR, "donations.csv")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fec_get(endpoint: str, params: dict) -> dict | None:
    """Make a GET request to the FEC API with rate-limiting and error handling."""
    params["api_key"] = API_KEY
    url = f"{FEC_BASE_URL}{endpoint}"
    time.sleep(FEC_REQUEST_DELAY)
    try:
        resp = requests.get(url, params=params, timeout=45)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  ⚠  FEC API error: {e}")
        return None


def search_candidate_id(name: str, state: str) -> str | None:
    """
    Look up a legislator's FEC candidate_id by name and state.
    Returns the first matching House candidate ID, or None.
    """
    data = _fec_get("/candidates/search/", {
        "name": name,
        "state": state,
        "office": "H",
        "cycle": ELECTION_CYCLE,
        "per_page": 5,
    })
    if data and data.get("results"):
        return data["results"][0]["candidate_id"]

    # Retry without office filter (some may be Senate)
    data = _fec_get("/candidates/search/", {
        "name": name,
        "state": state,
        "cycle": ELECTION_CYCLE,
        "per_page": 5,
    })
    if data and data.get("results"):
        return data["results"][0]["candidate_id"]

    return None


def find_principal_committee(candidate_id: str) -> str | None:
    """
    Given a candidate_id, find their principal campaign committee ID.
    This is needed to query Schedule A receipts TO this committee.
    """
    data = _fec_get(f"/candidate/{candidate_id}/committees/", {
        "cycle": ELECTION_CYCLE,
        "designation": "P",  # Principal campaign committee
    })
    if data and data.get("results"):
        return data["results"][0]["committee_id"]

    # Fallback: try without designation filter
    data = _fec_get(f"/candidate/{candidate_id}/committees/", {
        "cycle": ELECTION_CYCLE,
    })
    if data and data.get("results"):
        return data["results"][0]["committee_id"]

    return None


def fetch_pac_to_committee_donations(pac_committee_id: str, recipient_committee_id: str) -> float:
    """
    Fetch total PAC donations TO a candidate's committee using Schedule A.
    
    Schedule A = receipts/contributions. We query the recipient committee
    and filter by contributor_id = PAC committee ID.
    """
    total = 0.0
    params = {
        "committee_id": recipient_committee_id,  # The candidate's committee (recipient)
        "contributor_id": pac_committee_id,       # The PAC (source of money)
        "two_year_transaction_period": ELECTION_CYCLE,
        "per_page": 100,
        "is_individual": False,
    }

    page = 1
    while True:
        data = _fec_get("/schedules/schedule_a/", params)
        if not data or not data.get("results"):
            break

        for item in data["results"]:
            amt = item.get("contribution_receipt_amount", 0)
            if amt:
                total += float(amt)

        # Keyset pagination
        pagination = data.get("pagination", {})
        last_indexes = pagination.get("last_indexes")
        if not last_indexes or page >= 10:
            break
        if "last_index" in last_indexes:
            params["last_index"] = last_indexes["last_index"]
        if "last_contribution_receipt_date" in last_indexes:
            params["last_contribution_receipt_date"] = last_indexes["last_contribution_receipt_date"]
        page += 1

    return total


def fetch_candidate_totals(candidate_id: str) -> dict | None:
    """
    Fetch aggregate financial totals for a candidate.
    """
    data = _fec_get(f"/candidate/{candidate_id}/totals/", {
        "cycle": ELECTION_CYCLE,
    })
    if data and data.get("results"):
        result = data["results"][0]
        return {
            "total_receipts": result.get("receipts", 0),
            "pac_contributions": result.get("other_political_committee_contributions", 0),
            "individual_contributions": result.get("individual_contributions", 0),
        }
    return None


# ── Main Collection ───────────────────────────────────────────────────────────

def fetch_all_donations() -> pd.DataFrame:
    """
    For every (industry, PAC) × legislator combination, fetch the donation
    amount.  Returns a DataFrame and saves it to CSV.
    """
    if os.path.exists(OUTPUT_CSV):
        print(f"✓ Cached donations found at {OUTPUT_CSV}")
        return pd.read_csv(OUTPUT_CSV)

    rows = []
    total_legislators = len(TARGET_LEGISLATORS)

    # Step 1: Resolve FEC candidate IDs and principal committees
    print("═══ Step 1: Resolving FEC candidate & committee IDs ═══")
    candidate_info = {}  # bioguide_id → {candidate_id, committee_id}
    for i, leg in enumerate(TARGET_LEGISLATORS, 1):
        name = leg["name"]
        print(f"  [{i}/{total_legislators}] Looking up {name} ({leg['state']})...")
        cid = search_candidate_id(name, leg["state"])
        if not cid:
            print(f"    ⚠ Candidate not found — will skip")
            continue

        committee_id = find_principal_committee(cid)
        if not committee_id:
            print(f"    ⚠ No principal committee found for {cid} — will skip")
            continue

        candidate_info[leg["bioguide_id"]] = {
            "candidate_id": cid,
            "committee_id": committee_id,
        }
        print(f"    → {cid} / {committee_id}")

    print(f"\n  Resolved {len(candidate_info)} of {total_legislators} legislators\n")

    # Step 2: Fetch PAC → candidate donations via Schedule A
    print("═══ Step 2: Fetching PAC → Candidate donations (Schedule A) ═══")
    for industry, pacs in INDUSTRY_PACS.items():
        print(f"\n── {industry} ──")
        for pac in pacs:
            print(f"  PAC: {pac['name']} ({pac['committee_id']})")
            for leg in TARGET_LEGISLATORS:
                info = candidate_info.get(leg["bioguide_id"])
                if not info:
                    continue

                amount = fetch_pac_to_committee_donations(
                    pac["committee_id"],
                    info["committee_id"],
                )
                if amount > 0:
                    print(f"    → {leg['name']}: ${amount:,.2f}")

                rows.append({
                    "legislator_name": leg["name"],
                    "bioguide_id": leg["bioguide_id"],
                    "candidate_id": info["candidate_id"],
                    "party": leg["party"],
                    "state": leg["state"],
                    "industry": industry,
                    "pac_name": pac["name"],
                    "pac_committee_id": pac["committee_id"],
                    "amount": amount,
                    "cycle": ELECTION_CYCLE,
                })

    # Step 3: Also fetch aggregate candidate totals for context
    print("\n═══ Step 3: Fetching aggregate candidate totals ═══")
    totals_map = {}
    for bio_id, info in candidate_info.items():
        totals = fetch_candidate_totals(info["candidate_id"])
        if totals:
            totals_map[bio_id] = totals
            print(f"  {bio_id}: total PAC ${totals['pac_contributions']:,.0f}")

    df = pd.DataFrame(rows)

    # Add aggregate totals columns
    df["total_pac_contributions"] = df["bioguide_id"].map(
        lambda b: totals_map.get(b, {}).get("pac_contributions", 0)
    )
    df["total_receipts"] = df["bioguide_id"].map(
        lambda b: totals_map.get(b, {}).get("total_receipts", 0)
    )

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✓ Saved {len(df)} records to {OUTPUT_CSV}")
    return df


if __name__ == "__main__":
    df = fetch_all_donations()
    print(f"\nPreview:\n{df.head(10)}")
    print(f"\nNon-zero donations: {(df['amount'] > 0).sum()} / {len(df)}")
