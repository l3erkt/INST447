"""
analysis.py — Statistical analysis of merged donation + legislation data.

Tests the Investment Hypothesis: Do legislators who receive more PAC money
from a specific industry sponsor more bills related to that industry?

Methods:
  1. Pearson correlation (industry_donation_total vs total_relevant_bills)
  2. Summary statistics by party, industry, committee membership
  3. Point-biserial correlation for committee membership effects

Output: output/analysis_report.txt
"""

import os
import pandas as pd
from scipy.stats import pearsonr, spearmanr, pointbiserialr

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MERGED_CSV = os.path.join(DATA_DIR, "merged.csv")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.txt")


def run_analysis() -> str:
    """Run full statistical analysis and return the report as a string."""
    df = pd.read_csv(MERGED_CSV)
    lines = []

    def section(title):
        lines.append(f"\n{'═' * 70}")
        lines.append(f"  {title}")
        lines.append(f"{'═' * 70}")

    # ── 1. Dataset Overview ───────────────────────────────────────────────
    section("1. DATASET OVERVIEW")
    lines.append(f"Total records (legislator × industry):  {len(df)}")
    lines.append(f"Unique legislators:                     {df['bioguide_id'].nunique()}")
    lines.append(f"Industries tracked:                     {df['industry'].nunique()}")
    lines.append(f"Records with non-zero donations:        {(df['industry_donation_total'] > 0).sum()}")
    lines.append(f"Records with relevant bills sponsored:  {(df['bills_sponsored_relevant'] > 0).sum()}")

    # ── 2. Summary Statistics by Industry ─────────────────────────────────
    section("2. SUMMARY STATISTICS BY INDUSTRY")
    for industry in df["industry"].unique():
        sub = df[df["industry"] == industry]
        lines.append(f"\n── {industry} ──")
        lines.append(f"  Legislators:            {len(sub)}")
        lines.append(f"  Mean donation:          ${sub['industry_donation_total'].mean():,.2f}")
        lines.append(f"  Median donation:        ${sub['industry_donation_total'].median():,.2f}")
        lines.append(f"  Max donation:           ${sub['industry_donation_total'].max():,.2f}")
        lines.append(f"  Total donated:          ${sub['industry_donation_total'].sum():,.2f}")
        lines.append(f"  Mean relevant bills:    {sub['total_relevant_bills'].mean():.1f}")
        lines.append(f"  Median relevant bills:  {sub['total_relevant_bills'].median():.1f}")
        lines.append(f"  Max relevant bills:     {sub['total_relevant_bills'].max()}")

    # ── 3. Summary Statistics by Party ────────────────────────────────────
    section("3. SUMMARY STATISTICS BY PARTY")
    for party in df["party"].dropna().unique():
        sub = df[df["party"] == party]
        party_label = "Democrat" if party == "D" else "Republican"
        lines.append(f"\n── {party_label} ({party}) ──")
        lines.append(f"  Legislators:            {sub['bioguide_id'].nunique()}")
        lines.append(f"  Mean industry donation: ${sub['industry_donation_total'].mean():,.2f}")
        lines.append(f"  Mean relevant bills:    {sub['total_relevant_bills'].mean():.1f}")
        lines.append(f"  Mean total sponsored:   {sub['total_bills_sponsored'].mean():.1f}")

    # ── 4. Pearson Correlation ────────────────────────────────────────────
    section("4. PEARSON CORRELATION: Donations vs Relevant Bills")
    lines.append(
        "  H₀: There is no linear correlation between industry PAC donations\n"
        "      and the number of industry-relevant bills a legislator sponsors."
    )

    # Overall
    x = df["industry_donation_total"]
    y = df["total_relevant_bills"]
    mask = x.notna() & y.notna()
    if mask.sum() >= 3:
        r, p = pearsonr(x[mask], y[mask])
        lines.append(f"\n  Overall:  r = {r:.4f},  p = {p:.4f}  {'*' if p < 0.05 else '(not significant)'}")

    # Per industry
    for industry in df["industry"].unique():
        sub = df[df["industry"] == industry]
        x_i = sub["industry_donation_total"]
        y_i = sub["total_relevant_bills"]
        mask_i = x_i.notna() & y_i.notna()
        if mask_i.sum() >= 3:
            r, p = pearsonr(x_i[mask_i], y_i[mask_i])
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "(n.s.)"
            lines.append(f"  {industry:25s}  r = {r:.4f},  p = {p:.4f}  {sig}")

    # ── 5. Spearman Rank Correlation ──────────────────────────────────────
    section("5. SPEARMAN RANK CORRELATION (non-parametric)")
    if mask.sum() >= 3:
        rho, p = spearmanr(x[mask], y[mask])
        lines.append(f"\n  Overall:  ρ = {rho:.4f},  p = {p:.4f}  {'*' if p < 0.05 else '(n.s.)'}")

    for industry in df["industry"].unique():
        sub = df[df["industry"] == industry]
        x_i = sub["industry_donation_total"]
        y_i = sub["total_relevant_bills"]
        mask_i = x_i.notna() & y_i.notna()
        if mask_i.sum() >= 3:
            rho, p = spearmanr(x_i[mask_i], y_i[mask_i])
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "(n.s.)"
            lines.append(f"  {industry:25s}  ρ = {rho:.4f},  p = {p:.4f}  {sig}")

    # ── 6. Committee Membership Effect ────────────────────────────────────
    section("6. COMMITTEE MEMBERSHIP EFFECT")
    lines.append(
        "  Do legislators on relevant committees receive more donations AND\n"
        "  sponsor more relevant bills?"
    )
    if "on_relevant_committee" in df.columns:
        for industry in df["industry"].unique():
            sub = df[df["industry"] == industry].copy()
            sub["on_relevant_committee"] = sub["on_relevant_committee"].astype(bool)
            on = sub[sub["on_relevant_committee"]]
            off = sub[~sub["on_relevant_committee"]]

            lines.append(f"\n  ── {industry} ──")
            lines.append(f"    On relevant committee ({len(on)}):")
            lines.append(f"      Mean donation:       ${on['industry_donation_total'].mean():,.2f}")
            lines.append(f"      Mean relevant bills:  {on['total_relevant_bills'].mean():.1f}")
            lines.append(f"    NOT on relevant committee ({len(off)}):")
            lines.append(f"      Mean donation:       ${off['industry_donation_total'].mean():,.2f}")
            lines.append(f"      Mean relevant bills:  {off['total_relevant_bills'].mean():.1f}")

            # Point-biserial correlation
            if len(on) >= 2 and len(off) >= 2:
                r_don, p_don = pointbiserialr(
                    sub["on_relevant_committee"].astype(int),
                    sub["industry_donation_total"],
                )
                r_bill, p_bill = pointbiserialr(
                    sub["on_relevant_committee"].astype(int),
                    sub["total_relevant_bills"],
                )
                lines.append(f"    Point-biserial (committee → donations):  r = {r_don:.4f}, p = {p_don:.4f}")
                lines.append(f"    Point-biserial (committee → bills):      r = {r_bill:.4f}, p = {p_bill:.4f}")

    # ── 7. Top Recipients ─────────────────────────────────────────────────
    section("7. TOP RECIPIENTS BY INDUSTRY DONATION")
    for industry in df["industry"].unique():
        sub = df[df["industry"] == industry].nlargest(5, "industry_donation_total")
        lines.append(f"\n  ── {industry} ──")
        for _, row in sub.iterrows():
            lines.append(
                f"    {row['legislator_name']:30s} ({row['party']}-{row['state']})  "
                f"${row['industry_donation_total']:>10,.2f}  |  "
                f"{int(row['total_relevant_bills']):>3d} relevant bills"
            )

    # ── Write report ──────────────────────────────────────────────────────
    report = "\n".join(lines)

    header = (
        "╔══════════════════════════════════════════════════════════════════════╗\n"
        "║          THE LOBBYING SUBSIDY TRACKER — ANALYSIS REPORT            ║\n"
        "║                                                                    ║\n"
        "║  Hypothesis: PAC donations predict industry-relevant legislation   ║\n"
        "╚══════════════════════════════════════════════════════════════════════╝\n"
    )

    full_report = header + report

    with open(REPORT_PATH, "w") as f:
        f.write(full_report)

    print(full_report)
    print(f"\n✓ Report saved to {REPORT_PATH}")
    return full_report


if __name__ == "__main__":
    run_analysis()
