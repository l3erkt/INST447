# INST414 — Final Project: The Lobbying Subsidy Tracker

## Hypothesis

**Investment Hypothesis:** Do legislators who receive higher contributions from a specific industry's PACs sponsor more bills related to that industry?

We test this across three policy domains:

| Focus Area | PACs Tracked | Policy Areas |
|---|---|---|
| **Fossil Fuels** | ExxonMobil, Chevron, Koch Industries, ConocoPhillips, Marathon Petroleum, etc. | Energy, Environmental Protection |

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

## Methodology

1. **Network Graphs** were the most effective way to see how politicans voted on chosen topics, and what industries contributed to their campaign and success. 
2. **Colors** were used to make our network graphs more understandable. Red nodes represent republicans, blue nodes represent democrats, yellow nodes represent contributors in the fossil fuels industry, and green nodes represent contributors in the green-energy industry. Lastly, the graphs with a yellow background indicate that the congress members voted more in line with fossil fuels (saying YEAS/AYES during voting), and a blue background indicate that the congress members voted more in line with green energy (saying NAYS/NOES during voting).
3. **Income** was also analyzed but it didn't end up having a large impact on the results. We suspected that representatives who earned less were more likely to vote in accordance with their funders, but that wasn't exactly the case.  

## Target Legislators

12 members of the 119th Congress (2025–2026) selected from:
- **House Energy & Commerce Committee** (Fossil Fuels focus)

## Selected Bill
### Green Energy
As of late April 2026, the legislative status and voting records for these three bills in the House of Representatives are as follows. Of the three, only H.R. 4758 has reached a full floor vote.

1. H.R. 4758 – Homeowner Energy Freedom Act

This bill sought to repeal key electrification rebates and energy efficiency grants established by the Inflation Reduction Act (IRA).

    House Floor Vote Date: February 25, 2026

    Result: Passed (210–199, 1 Present)

    Roll Call No.: 78

    Procedural Vote: A Democratic motion to recommit (a final attempt to send the bill back to committee for changes) failed 198–208 (Roll Call No. 77).

    Current Status: Received in the Senate and referred to the Committee on Energy and Natural Resources.