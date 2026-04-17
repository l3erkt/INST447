# Project Alignment Review
**Course:** INST447 — Team 5 Final Project  
**Reviewed:** April 14, 2026  
**Documents Reviewed:** `[Revised] Team 5 Project Proposal.docx`, `Response Letter.docx`  
**Codebase:** `/Users/robtzou/Desktop/INST447/`

---

## Overview

This document evaluates how well the current Python codebase aligns with the commitments made in the revised project proposal and the responses given to reviewer feedback in the Response Letter. Each section of the outline documents is assessed against what is actually implemented.

---

## 1. Research Question

### What the Proposal + Response Letter Say
> *"How does funding bias politicians in their decisions for important policies regarding fossil fuels / green energy, defense / Iran war, and data centers / technologies?"*

The Response Letter clarified the team would focus on **10–20 congress members elected in 2024**, looking at funding and voting behavior in **2025** across three specific policy topics.

### What the Code Does
| Item | Status |
|---|---|
| Three policy topics (Fossil Fuels, Defense/Iran, Data Centers/Tech) | ✅ Implemented in `config.py` |
| Focused research question on funding vs. legislative behavior | ✅ Reflected in README hypothesis |
| 10–20 members elected in 2024 | ⚠️ **Diverges significantly** |
| Voting behavior from 2025 | ⚠️ **Not implemented** |

### Gap Identified
The code targets **40 members of the 117th Congress (2021–2022)**, not 10–20 newly elected 2024 members. The `config.py` sets `ELECTION_CYCLE = 2022` and `CONGRESS_NUMBER = 117`. The Response Letter specifically committed to members *elected in 2024* and policies from *2025*. This is a meaningful misalignment with the revised research scope.

> [!WARNING]
> The code's chosen legislators and election cycle (2022/117th Congress) directly contradict the Response Letter's commitment to focus on 2024-elected members and 2025 policy behavior.

---

## 2. Data Sources

### What the Proposal + Response Letter Say
- **fec.gov** — candidate funding data
- **congress.gov** — voting behaviors on controversial bills

### What the Code Does
| Data Source | Status |
|---|---|
| `fec.gov` data via OpenFEC API | ✅ Fully implemented in `fetch_fec.py` |
| `congress.gov` data via Congress.gov API | ✅ Fully implemented in `fetch_congress.py` |
| "Raised funds" dataset | ✅ PAC → candidate donations fetched (Schedule A) |
| House Roll Call Votes on specific bills | ⚠️ **Partially misaligned** |

### Gap Identified
The proposal references **actual roll-call votes** on specific controversial bills. The current code instead counts **bills sponsored or co-sponsored** by legislators (filtered by policy area). These are not the same: a legislator can sponsor many energy bills while still voting against a specific piece of energy legislation. The roll-call vote angle — which is what the proposal and Response Letter describe as the key metric for "voting behavior" — is not currently captured.

> [!IMPORTANT]
> The code measures *sponsorship/co-sponsorship activity* as a proxy for policy stance. The proposal and Response Letter explicitly frame the analysis around *voting behavior on controversial bills*. This is a conceptual gap that affects the validity of the research question.

---

## 3. Data Wrangling / Pipeline

### What the Proposal Says
> *"Join datasets so we have a table that shows each candidate's name and columns for controversial bills showing how each candidate voted."*

### What the Code Does
- `fetch_fec.py` → downloads PAC donation data → `data/donations.csv`
- `fetch_congress.py` → downloads legislative sponsorship data → `data/legislation.csv`
- `merge_data.py` → joins on `(bioguide_id, industry)` → `data/merged.csv`
- Derived metrics: `industry_donation_share`, `sponsorship_rate`

| Wrangling Task | Status |
|---|---|
| Join FEC + Congress data | ✅ Implemented cleanly in `merge_data.py` |
| Per-candidate view with industry columns | ✅ Produces `(legislator × industry)` rows |
| Actual votes on specific bills | ❌ Not implemented |
| Python used for wrangling | ✅ pandas used throughout |

### Gap Identified
The merge is technically sound and well-structured, but the **unit of analysis** differs from the proposal. The proposal envisions a table of "votes on bills"; the codebase produces a table of "bills sponsored per industry." The Excel/SQL tools mentioned in the proposal are absent (Python handles everything, which is fine and arguably better).

---

## 4. Data Analysis

### What the Response Letter Commits To
> *"We will analyze data joined from fec.gov and congress.gov using data aggregation and **network graphs** primarily… Red or blue nodes represent congress members, placed in regions by how they voted on bills, with edges connecting to donor nodes colored by their stance on the topic."*

### What the Code Does
| Analysis Method | Status |
|---|---|
| Pearson correlation (donations vs. bills) | ✅ Implemented (`analysis.py`) |
| Spearman rank correlation | ✅ Implemented (`analysis.py`) |
| Point-biserial (committee membership effect) | ✅ Implemented (`analysis.py`) |
| Summary statistics by party and industry | ✅ Implemented (`analysis.py`) |
| **Network graphs (NetworkX)** | ❌ **Not implemented at all** |
| Voting-region layout for nodes | ❌ Not applicable — no voting data |
| Donor nodes with stance coloring | ❌ Not implemented |

### Gap Identified — Critical
The **network graph** was explicitly called out in both the proposal and the Response Letter as the *primary* visualization. The Response Letter even gave specific design details (node color by party, regions by vote, edges to donors). The current `visualize.py` produces scatter plots, bar charts, heatmaps, and box plots — **none of which are network graphs**.

> [!CAUTION]
> The network graph using NetworkX is described as the centerpiece of the data analysis in both documents. It is entirely absent from the current codebase. This is the most significant alignment gap in the project.

---

## 5. Visualizations Produced

### Current Output Files
| File | Chart Type | Proposal Alignment |
|---|---|---|
| `01_scatter_regression.png` | Scatter + regression (donations vs. bills, per industry) | ⚠️ Supplementary; not the primary viz |
| `02_top_recipients.png` | Horizontal bar — top 15 donation recipients | ⚠️ Useful but not in the proposal |
| `03_correlation_heatmap.png` | Correlation matrix heatmap | ⚠️ Supplementary; not in the proposal |
| `04_donations_by_party.png` | Box plot — donations by party | ⚠️ Useful but not in the proposal |
| `05_committee_effect.png` | Bar chart — committee membership effect | ⚠️ Supplementary; not in the proposal |
| `06_dual_*.png` (×3) | Dual-axis bar — donations + bills per legislator | ⚠️ Useful but not in the proposal |

All 8 generated charts are statistically informative but **none match the planned network graph format** described in the outline documents.

---

## 6. Communication of Results

### What the Proposal Says
> *"We will communicate our results using a **Jupyter Notebook** and a **Quarto manuscript**."*

### What Exists
| Deliverable | Status |
|---|---|
| Jupyter Notebook | ❌ **Not present** |
| Quarto manuscript | ❌ **Not present** |
| `output/analysis_report.txt` | ✅ Exists (auto-generated text report) |
| `README.md` | ✅ Exists (technical documentation) |

> [!IMPORTANT]
> Neither the Jupyter Notebook nor the Quarto manuscript required by the proposal currently exist. The `analysis_report.txt` is machine-generated output, not a narrative research deliverable.

---

## 7. Sample Size & Member Selection

### What the Response Letter Says
> *"We are focusing on between **ten and twenty congress members** who were **elected in 2024**."*

### What the Code Has
`config.py` defines **40 legislators** from the 117th Congress (2021–2022). These include members like Bobby Rush (retired), Fred Upton (retired), and Liz Cheney (lost primary in 2022) — none of whom were elected in 2024.

> [!WARNING]
> The legislator list needs to be completely replaced with 10–20 members elected in the 2024 cycle if the codebase is to match the revised scope from the Response Letter.

---

## 8. What the Code Does Well (Strengths)

Despite the gaps, the codebase demonstrates strong technical execution:

- ✅ **Clean modular pipeline** — each phase (fetch, merge, analyze, visualize) is a separate module
- ✅ **API integration** — both FEC and Congress.gov APIs are properly called with rate limiting, pagination, and error handling
- ✅ **Statistical rigor** — Pearson, Spearman, and Point-Biserial correlations are all implemented correctly
- ✅ **Reproducibility** — CSV caching means the pipeline can be re-run without repeating API calls
- ✅ **Industry categorization** — PAC → industry mapping and policy area → industry mapping are clearly defined
- ✅ **Data quality** — proper handling of NaN values, outer joins, and derived metrics (donation share, sponsorship rate)
- ✅ **Three policy domains** — Fossil Fuels, Defense/Iran, Data Centers/Tech are all correctly represented

---

## 9. Summary of Gaps

| Proposal Requirement | Current Status | Priority |
|---|---|---|
| Network graph (NetworkX) — primary visualization | ❌ Missing | 🔴 Critical |
| Voting behavior on specific roll-call votes | ❌ Missing (sponsorship used instead) | 🔴 Critical |
| 2024-elected congress members (10–20) | ❌ Wrong cohort (2022, 40 members) | 🔴 Critical |
| Jupyter Notebook deliverable | ❌ Missing | 🟡 High |
| Quarto manuscript | ❌ Missing | 🟡 High |
| "Green energy" framing (vs. just "Fossil Fuels") | ⚠️ Partial (policy areas cover some overlap) | 🟠 Medium |
| FEC + congress.gov data pipeline | ✅ Solid | — |
| Statistical analysis (correlations) | ✅ Solid | — |
| Three policy topic focus | ✅ Aligned | — |

---

## 10. Recommended Next Steps

1. **Update the legislator list** in `config.py` to 10–20 members elected in November 2024 (`ELECTION_CYCLE = 2024`, `CONGRESS_NUMBER = 119`).
2. **Add roll-call vote fetching** — The Congress.gov API supports `/vote` endpoints. A new `fetch_votes.py` module could pull votes on specific bills (e.g., the Inflation Reduction Act amendments, NDAA, AI-related bills).
3. **Build a NetworkX visualization** — A `visualize_network.py` module that creates the donor-legislator graph described in both documents, with party-colored nodes, vote-region layout, and industry-colored donor edges.
4. **Create a Jupyter Notebook** — Convert the pipeline into an `.ipynb` with narrative markdown cells explaining methodology and findings.
5. **Draft the Quarto manuscript** — Start a `.qmd` file for the final written deliverable.