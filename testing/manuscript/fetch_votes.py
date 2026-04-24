"""
fetch_votes.py — Fetch roll-call vote records from Congress.gov for each
target legislator on specific bills defined in config.TARGET_BILLS.

Strategy:
  1. For each target bill, fetch the full roll-call vote list via the
     Congress.gov bill votes endpoint.
  2. Match each target legislator by bioguide_id.
  3. Record their vote (Yea / Nay / Not Voting / Present).
  4. Derive an `aligned_with_industry` boolean based on the industry_position
     field in TARGET_BILLS config.

Output: data/votes.csv
"""

import os
import time
import requests
import pandas as pd

from config import (
    API_KEY, CONGRESS_BASE_URL, CONGRESS_REQUEST_DELAY,
    TARGET_BILLS, TARGET_LEGISLATORS,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_CSV = os.path.join(DATA_DIR, "votes.csv")

# Build a quick lookup: bioguide_id → legislator metadata
LEG_MAP = {leg["bioguide_id"]: leg for leg in TARGET_LEGISLATORS}


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
        print(f"  ⚠  Congress API error on {url}: {e}")
        return None


def fetch_bill_votes(congress: int, bill_type: str, bill_number: str) -> list[dict]:
    """
    Fetch all roll-call vote records for a specific bill.
    Returns a list of vote dicts, each containing at minimum:
      - bioguideId, firstName, lastName, party, state, vote
    """
    all_votes: list[dict] = []
    offset = 0
    limit = 250

    while True:
        data = _congress_get(
            f"/bill/{congress}/{bill_type}/{bill_number}/votes",
            {"offset": offset, "limit": limit},
        )
        if not data:
            break

        vote_data = data.get("votes") or data.get("vote", {})

        # The response structure nests: votes → vote → members
        if isinstance(vote_data, dict):
            members = vote_data.get("members", [])
            if isinstance(members, dict):
                members = members.get("member", [])
            all_votes.extend(members if isinstance(members, list) else [])
            break  # single vote record

        elif isinstance(vote_data, list):
            # Multiple recorded votes for the bill (amendments, final passage, etc.)
            for v in vote_data:
                members = v.get("members", [])
                if isinstance(members, dict):
                    members = members.get("member", [])
                all_votes.extend(members if isinstance(members, list) else [])

        pagination = data.get("pagination", {})
        total = pagination.get("count", 0)
        offset += limit
        if offset >= total:
            break

    return all_votes


def fetch_all_votes() -> pd.DataFrame:
    """
    For every target bill × target legislator, record the roll-call vote.
    Returns a DataFrame and saves to CSV.
    """
    if os.path.exists(OUTPUT_CSV):
        print(f"✓ Cached vote data found at {OUTPUT_CSV}")
        return pd.read_csv(OUTPUT_CSV)

    rows = []

    for topic, bills in TARGET_BILLS.items():
        print(f"\n── {topic} ──")
        for bill in bills:
            congress   = bill["congress"]
            btype      = bill["type"].lower()
            bnumber    = bill["number"]
            bname      = bill["name"]
            industry_pos = bill["industry_position"]   # "Yea" or "Nay"

            print(f"  Fetching votes: {btype.upper()} {bnumber} — {bname}")
            raw_votes = fetch_bill_votes(congress, btype, bnumber)
            print(f"    → {len(raw_votes)} raw vote records")

            # Index raw votes by bioguide_id for quick lookup
            vote_index: dict[str, str] = {}
            for v in raw_votes:
                bio = v.get("bioguideId") or v.get("member", {}).get("bioguideId", "")
                vote_val = v.get("vote") or v.get("votePosition", "Not Voting")
                if bio:
                    vote_index[bio] = vote_val

            # Record vote for each target legislator
            for leg in TARGET_LEGISLATORS:
                bio   = leg["bioguide_id"]
                vote  = vote_index.get(bio, "Not Voting")
                aligned = None
                if vote in ("Yea", "Nay"):
                    aligned = (vote == industry_pos)

                rows.append({
                    "legislator_name":     leg["name"],
                    "bioguide_id":         bio,
                    "party":               leg["party"],
                    "state":               leg["state"],
                    "topic":               topic,
                    "bill_type":           btype.upper(),
                    "bill_number":         bnumber,
                    "bill_name":           bname,
                    "bill_description":    bill.get("description", ""),
                    "industry_position":   industry_pos,
                    "vote":                vote,
                    "aligned_with_industry": aligned,
                })

                status = "✓" if aligned else ("✗" if aligned is False else "—")
                print(f"    {status} {leg['name']:25s}  {vote}")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✓ Saved {len(df)} vote records to {OUTPUT_CSV}")
    return df


if __name__ == "__main__":
    df = fetch_all_votes()
    print(f"\nPreview:\n{df.head(20).to_string()}")
    aligned = df[df["aligned_with_industry"] == True]
    print(f"\nAligned votes: {len(aligned)} / {df['aligned_with_industry'].notna().sum()} cast")
