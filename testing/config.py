"""
Configuration for The Lobbying Subsidy Tracker.
Loads API keys, defines PAC-to-industry mappings, target legislators,
policy area mappings, and specific target bills for roll-call vote analysis.

Updated for 119th Congress / 2024 Election Cycle.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Configuration ─────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY")
FEC_BASE_URL = "https://api.open.fec.gov/v1"
CONGRESS_BASE_URL = "https://api.congress.gov/v3"
ELECTION_CYCLE = 2024       # 2024 General Election cycle
CONGRESS_NUMBER = 119       # 119th Congress (2025–2026)

# ── Rate-Limiting ─────────────────────────────────────────────────────────────
FEC_REQUEST_DELAY = 0.6     # seconds between FEC API calls (1000/hr limit)
CONGRESS_REQUEST_DELAY = 0.3  # seconds between Congress API calls (5000/hr)

# ── Industry → PAC Mapping ────────────────────────────────────────────────────
# Each industry maps to a list of known PACs with their FEC committee IDs.
INDUSTRY_PACS = {
    "Fossil Fuels": [
        {"name": "ExxonMobil PAC",              "committee_id": "C00121368"},
        {"name": "Chevron Employees PAC",       "committee_id": "C00035006"},
        {"name": "Koch Industries PAC",         "committee_id": "C00236489"},
        {"name": "ConocoPhillips Spirit PAC",   "committee_id": "C00112896"},
        {"name": "Marathon Petroleum PAC",      "committee_id": "C00496307"},
    ],
    "Data Centers / Tech": [
        {"name": "Google NetPAC",               "committee_id": "C00428623"},
        {"name": "Meta Platforms PAC",          "committee_id": "C00502906"},
        {"name": "Amazon PAC",                  "committee_id": "C00360354"},
        {"name": "Microsoft PAC",               "committee_id": "C00227546"},
    ],
    "Defense / Iran": [
        {"name": "Lockheed Martin PAC",         "committee_id": "C00303024"},
        {"name": "Northrop Grumman PAC",        "committee_id": "C00088591"},
        {"name": "RTX (Raytheon) PAC",          "committee_id": "C00097568"},
        {"name": "General Dynamics PAC",        "committee_id": "C00078451"},
        {"name": "Boeing PAC",                  "committee_id": "C00142711"},
        {"name": "L3Harris PAC",                "committee_id": "C00100321"},
    ],
}

# ── Industry → Congress.gov Policy Areas ──────────────────────────────────────
# Used to count how many of a legislator's sponsored bills relate to each topic.
INDUSTRY_POLICY_AREAS = {
    "Fossil Fuels": [
        "Energy",
        "Environmental Protection",
        "Public Lands and Natural Resources",
    ],
    "Data Centers / Tech": [
        "Science, Technology, Communications",
        "Energy",
        "Commerce",
    ],
    "Defense / Iran": [
        "Armed Forces and National Security",
        "International Affairs",
        "Emergency Management",
    ],
}

# ── Target Bills for Roll-Call Vote Analysis ──────────────────────────────────
# Specific bills from the 119th Congress (2025) that have had floor votes.
# Each entry maps to a topic and has a Congress.gov bill identifier.
# Votes: "Yea" = supports industry position, "Nay" = opposes.
# industry_position: "Yea" means a Yea vote FAVORS that industry's interests.
TARGET_BILLS = {
    "Fossil Fuels": [
        {
            "congress": 119,
            "type": "hr",
            "number": "4776",
            "name": "SPEED Act",
            "description": "Streamlines environmental permitting for energy projects",
            "industry_position": "Yea",   # Yea = pro-fossil fuel / pro-permitting
        },
        {
            "congress": 119,
            "type": "hr",
            "number": "3616",
            "name": "Reliable Power Act",
            "description": "Promotes reliable domestic energy production",
            "industry_position": "Yea",
        },
        {
            "congress": 119,
            "type": "hr",
            "number": "1366",
            "name": "Mining Regulatory Clarity Act",
            "description": "Reduces regulatory burdens on mining and energy extraction",
            "industry_position": "Yea",
        },
    ],
    "Defense / Iran": [
        {
            "congress": 119,
            "type": "hr",
            "number": "23",
            "name": "Illegitimate Court Counteraction Act",
            "description": "Sanctions related to international legal actions against U.S. allies",
            "industry_position": "Yea",   # Yea = hawkish / pro-defense stance
        },
    ],
    "Data Centers / Tech": [
        {
            "congress": 119,
            "type": "hr",
            "number": "123",
            "name": "Improving Science in Chemical Assessments Act",
            "description": "Science and technology committee-referred bill on chemical risk assessment",
            "industry_position": "Yea",
        },
    ],
}

# ── Target Legislators ────────────────────────────────────────────────────────
# Freshmen members of the 119th Congress (elected November 2024) serving on
# the three key committees: Energy & Commerce, Armed Services, Science/Space/Tech.
#
# Bioguide IDs verified via Congress.gov API (April 2025).
# FEC candidate_id will be looked up dynamically via the FEC /candidates/search/ endpoint.

TARGET_LEGISLATORS = [
    # ── Energy & Commerce Committee (Fossil Fuels / Green Energy) ──────────
    {"name": "Gabe Evans",        "bioguide_id": "E000300", "party": "R", "state": "CO",
     "committees": ["Energy and Commerce"]},
    {"name": "Julie Fedorchak",   "bioguide_id": "F000482", "party": "R", "state": "ND",
     "committees": ["Energy and Commerce"]},
    {"name": "Craig Goldman",     "bioguide_id": "G000599", "party": "R", "state": "TX",
     "committees": ["Energy and Commerce"]},

    # ── Armed Services Committee (Defense / Iran) ──────────────────────────
    {"name": "Jeff Crank",        "bioguide_id": "C001137", "party": "R", "state": "CO",
     "committees": ["Armed Services"]},
    {"name": "Abraham Hamadeh",   "bioguide_id": "H001098", "party": "R", "state": "AZ",
     "committees": ["Armed Services"]},
    {"name": "Pat Harrigan",      "bioguide_id": "H001101", "party": "R", "state": "NC",
     "committees": ["Armed Services"]},
    {"name": "Mark Messmer",      "bioguide_id": "M001233", "party": "R", "state": "IN",
     "committees": ["Armed Services"]},
    {"name": "Derek Schmidt",     "bioguide_id": "S001228", "party": "R", "state": "KS",
     "committees": ["Armed Services"]},
    {"name": "Wesley Bell",       "bioguide_id": "B001324", "party": "D", "state": "MO",
     "committees": ["Armed Services"]},
    {"name": "Herb Conaway",      "bioguide_id": "C001136", "party": "D", "state": "NJ",
     "committees": ["Armed Services"]},
    {"name": "Sarah Elfreth",     "bioguide_id": "E000301", "party": "D", "state": "MD",
     "committees": ["Armed Services"]},
    {"name": "Maggie Goodlander", "bioguide_id": "G000604", "party": "D", "state": "NH",
     "committees": ["Armed Services"]},
    {"name": "Derek Tran",        "bioguide_id": "T000491", "party": "D", "state": "CA",
     "committees": ["Armed Services"]},
    {"name": "Eugene Vindman",    "bioguide_id": "V000138", "party": "D", "state": "VA",
     "committees": ["Armed Services"]},
    {"name": "George Whitesides", "bioguide_id": "W000830", "party": "D", "state": "CA",
     "committees": ["Armed Services", "Science, Space, and Technology"]},

    # ── Science, Space & Technology Committee (Data Centers / Tech) ────────
    # Source: official science.house.gov/members roster (March 2026)
    {"name": "Sheri Biggs",          "bioguide_id": "B001325", "party": "R", "state": "SC",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Mike Haridopolos",     "bioguide_id": "H001099", "party": "R", "state": "FL",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Jeff Hurd",            "bioguide_id": "H001100", "party": "R", "state": "CO",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Mike Kennedy",         "bioguide_id": "K000403", "party": "R", "state": "UT",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Nick Begich",          "bioguide_id": "B001323", "party": "R", "state": "AK",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Matt Van Epps",        "bioguide_id": "V000139", "party": "R", "state": "TN",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Suhas Subramanyam",    "bioguide_id": "S001230", "party": "D", "state": "VA",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Luz Rivas",            "bioguide_id": "R000620", "party": "D", "state": "CA",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Sarah McBride",        "bioguide_id": "M001238", "party": "D", "state": "DE",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Laura Gillen",         "bioguide_id": "G000602", "party": "D", "state": "NY",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Laura Friedman",       "bioguide_id": "F000483", "party": "D", "state": "CA",
     "committees": ["Science, Space, and Technology"]},
    {"name": "April McClain-Delaney","bioguide_id": "M001232", "party": "D", "state": "MD",
     "committees": ["Science, Space, and Technology"]},
    {"name": "Josh Riley",           "bioguide_id": "R000622", "party": "D", "state": "NY",
     "committees": ["Science, Space, and Technology"]},
]
