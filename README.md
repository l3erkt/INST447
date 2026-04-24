# INST414 — Final Project: The Lobbying Subsidy Tracker

## Hypothesis

**Investment Hypothesis:** Do legislators who receive higher contributions from a specific industry's PACs sponsor more bills related to that industry?

We test this across three policy domains:

| Focus Area | PACs Tracked | Policy Areas |
|---|---|---|
| **Fossil Fuels** | ExxonMobil, Chevron, Koch Industries, ConocoPhillips, Marathon Petroleum | Energy, Environmental Protection |
| **Data Centers / Tech** | Google, Meta, Amazon, Microsoft | Science/Technology/Communications, Energy |
| **Defense / Iran** | Lockheed Martin, Northrop Grumman, RTX (Raytheon), General Dynamics, Boeing, L3Harris | Armed Forces & National Security, International Affairs |

## Data Sources

- **OpenFEC API** — PAC disbursements (Schedule B) to candidate campaigns, 2022 cycle
- **Congress.gov API** — Sponsored & co-sponsored legislation by policy area, 117th Congress

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key (from api.data.gov) to .env
echo "API_KEY=your_key_here" > .env

# 3. Run the full pipeline
python main.py

# Or use flags:
python main.py --skip-fetch       # Re-analyze with cached data
python main.py --fetch-only       # Only download data
python main.py --analyze-only     # Only run analysis + charts
```

## Project Structure

```
├── config.py          # API keys, PAC mappings, legislator targets
├── fetch_fec.py       # FEC API client (PAC → candidate donations)
├── fetch_congress.py  # Congress.gov client (bills by policy area)
├── merge_data.py      # Joins donation & legislation datasets
├── analysis.py        # Pearson/Spearman correlations, committee effects
├── visualize.py       # Seaborn/Matplotlib charts (dark theme)
├── main.py            # Pipeline orchestrator
├── data/              # Cached CSVs (gitignored)
└── output/            # Charts & analysis report (gitignored)
```

## Methodology

1. **Resolve** FEC candidate IDs for 30 legislators on Energy & Commerce, Armed Services, and Science/Tech committees
2. **Fetch** Schedule B disbursements from each industry PAC to each legislator
3. **Fetch** sponsored + co-sponsored legislation, filtered by policy area
4. **Merge** datasets on (legislator, industry)
5. **Analyze** with Pearson correlation, Spearman rank, point-biserial (committee effect)
6. **Visualize** scatter regressions, bar charts, heatmaps, party comparisons

## Target Legislators

30 members of the 117th Congress (2021–2022) selected from:
- **House Energy & Commerce Committee** (Fossil Fuels focus)
- **House Armed Services Committee** (Defense/Iran focus)
- **House Science, Space & Technology Committee** (Data Centers/Tech focus)

## Possible Bills to look into
### Green Energy
As of late April 2026, the legislative status and voting records for these three bills in the House of Representatives are as follows. Of the three, only H.R. 4758 has reached a full floor vote.

1. H.R. 4758 – Homeowner Energy Freedom Act

This bill sought to repeal key electrification rebates and energy efficiency grants established by the Inflation Reduction Act (IRA).

    House Floor Vote Date: February 25, 2026

    Result: Passed (210–199, 1 Present)

    Roll Call No.: 78

    Procedural Vote: A Democratic motion to recommit (a final attempt to send the bill back to committee for changes) failed 198–208 (Roll Call No. 77).

    Current Status: Received in the Senate and referred to the Committee on Energy and Natural Resources.