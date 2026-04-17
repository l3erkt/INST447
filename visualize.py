"""
visualize.py — Generate publication-quality charts for the analysis.

Charts:
  1. Scatter plot: Donations vs Relevant Bills (per industry, with regression)
  2. Horizontal bar: Top 15 recipients by industry donation
  3. Heatmap: Correlation matrix of key numeric variables
  4. Box plot: Donations by party (per industry)
  5. Grouped bar: Relevant vs total bills (per legislator, one per industry)
  6. Stacked bar: PAC breakdown for top recipients

Output: output/*.png
"""

import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MERGED_CSV = os.path.join(DATA_DIR, "merged.csv")

# ── Styling ───────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f0f1a",
    "axes.facecolor": "#1a1a2e",
    "savefig.facecolor": "#0f0f1a",
    "text.color": "#e0e0e0",
    "axes.labelcolor": "#e0e0e0",
    "xtick.color": "#b0b0b0",
    "ytick.color": "#b0b0b0",
    "axes.edgecolor": "#333355",
    "grid.color": "#2a2a44",
    "grid.alpha": 0.5,
    "font.family": "sans-serif",
    "font.size": 11,
})

INDUSTRY_COLORS = {
    "Fossil Fuels": "#ff6b35",
    "Data Centers / Tech": "#00d4aa",
    "Defense / Iran": "#6c5ce7",
}

PARTY_COLORS = {"D": "#4a90d9", "R": "#e74c3c"}


def dollar_fmt(x, _):
    """Format axis ticks as dollars."""
    if x >= 1_000_000:
        return f"${x / 1e6:.1f}M"
    elif x >= 1_000:
        return f"${x / 1e3:.0f}K"
    return f"${x:.0f}"


# ── Chart 1: Scatter with Regression ──────────────────────────────────────────

def plot_scatter_regression(df: pd.DataFrame):
    """Donations vs relevant bills, colored by industry with regression lines."""
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=True)
    fig.suptitle(
        "PAC Industry Donations vs. Relevant Bills Sponsored",
        fontsize=16, fontweight="bold", color="white", y=1.02,
    )

    for ax, (industry, color) in zip(axes, INDUSTRY_COLORS.items()):
        sub = df[df["industry"] == industry].copy()
        sns.regplot(
            data=sub,
            x="industry_donation_total",
            y="total_relevant_bills",
            ax=ax,
            color=color,
            scatter_kws={"alpha": 0.7, "s": 60, "edgecolor": "white", "linewidths": 0.5},
            line_kws={"linewidth": 2, "alpha": 0.8},
        )

        # Label top outliers
        top = sub.nlargest(3, "industry_donation_total")
        for _, row in top.iterrows():
            ax.annotate(
                row["legislator_name"].split()[-1],
                (row["industry_donation_total"], row["total_relevant_bills"]),
                textcoords="offset points", xytext=(5, 5),
                fontsize=8, color=color, alpha=0.9,
            )

        ax.set_title(industry, fontsize=13, fontweight="bold", color=color)
        ax.set_xlabel("Total Industry PAC Donations ($)")
        ax.xaxis.set_major_formatter(FuncFormatter(dollar_fmt))
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Relevant Bills Sponsored + Co-sponsored")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "01_scatter_regression.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {path}")


# ── Chart 2: Top Recipients Bar Chart ────────────────────────────────────────

def plot_top_recipients(df: pd.DataFrame):
    """Horizontal bar chart of top 15 recipients across all industries."""
    top = df.nlargest(15, "industry_donation_total").sort_values("industry_donation_total")

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = [INDUSTRY_COLORS.get(row["industry"], "#888") for _, row in top.iterrows()]
    party_markers = [PARTY_COLORS.get(row["party"], "#888") for _, row in top.iterrows()]

    bars = ax.barh(
        range(len(top)),
        top["industry_donation_total"],
        color=colors,
        edgecolor="white",
        linewidth=0.5,
        alpha=0.85,
    )

    labels = [
        f"{row['legislator_name']} ({row['party']}-{row['state']}) — {row['industry']}"
        for _, row in top.iterrows()
    ]
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=9)

    # Party color indicator dots
    for i, (_, row) in enumerate(top.iterrows()):
        ax.plot(
            -top["industry_donation_total"].max() * 0.02, i,
            "o", color=PARTY_COLORS.get(row["party"], "#888"),
            markersize=8, clip_on=False,
        )

    ax.set_xlabel("Total Industry PAC Donations ($)")
    ax.xaxis.set_major_formatter(FuncFormatter(dollar_fmt))
    ax.set_title(
        "Top 15 Recipients of Industry PAC Donations (2022 Cycle)",
        fontsize=14, fontweight="bold", color="white",
    )
    ax.grid(True, axis="x", alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=c, label=ind) for ind, c in INDUSTRY_COLORS.items()
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "02_top_recipients.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {path}")


# ── Chart 3: Correlation Heatmap ─────────────────────────────────────────────

def plot_correlation_heatmap(df: pd.DataFrame):
    """Heatmap of correlations among key numeric variables."""
    cols = [
        "industry_donation_total",
        "total_relevant_bills",
        "bills_sponsored_relevant",
        "bills_cosponsored_relevant",
        "total_bills_sponsored",
        "total_pac_contributions",
        "sponsorship_rate",
    ]
    available = [c for c in cols if c in df.columns]
    corr = df[available].corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=1,
        linecolor="#333355",
        cbar_kws={"shrink": 0.8},
        ax=ax,
        annot_kws={"fontsize": 9},
    )
    ax.set_title(
        "Correlation Matrix: Donations & Legislative Activity",
        fontsize=14, fontweight="bold", color="white", pad=15,
    )
    # Clean up tick labels
    short = {
        "industry_donation_total": "Industry Donations",
        "total_relevant_bills": "Relevant Bills",
        "bills_sponsored_relevant": "Sponsored (Relevant)",
        "bills_cosponsored_relevant": "Cosponsored (Relevant)",
        "total_bills_sponsored": "Total Sponsored",
        "total_pac_contributions": "Total PAC $",
        "sponsorship_rate": "Sponsorship Rate",
    }
    ax.set_xticklabels([short.get(c, c) for c in available], rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels([short.get(c, c) for c in available], rotation=0, fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "03_correlation_heatmap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {path}")


# ── Chart 4: Box Plot by Party ───────────────────────────────────────────────

def plot_donations_by_party(df: pd.DataFrame):
    """Box plot of industry donation totals separated by party."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    fig.suptitle(
        "Industry PAC Donations by Party",
        fontsize=16, fontweight="bold", color="white", y=1.02,
    )

    for ax, (industry, color) in zip(axes, INDUSTRY_COLORS.items()):
        sub = df[df["industry"] == industry]
        sns.boxplot(
            data=sub,
            x="party",
            y="industry_donation_total",
            ax=ax,
            palette=PARTY_COLORS,
            width=0.5,
            flierprops={"marker": "o", "markerfacecolor": color, "alpha": 0.5},
        )
        sns.stripplot(
            data=sub,
            x="party",
            y="industry_donation_total",
            ax=ax,
            color=color,
            alpha=0.4,
            size=5,
            jitter=True,
        )
        ax.set_title(industry, fontsize=13, fontweight="bold", color=color)
        ax.set_xlabel("Party")
        ax.set_ylabel("Industry PAC Donations ($)")
        ax.yaxis.set_major_formatter(FuncFormatter(dollar_fmt))
        ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "04_donations_by_party.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {path}")


# ── Chart 5: Committee Membership Comparison ─────────────────────────────────

def plot_committee_effect(df: pd.DataFrame):
    """Compare donations and bills for on-committee vs off-committee members."""
    if "on_relevant_committee" not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "Effect of Relevant Committee Membership",
        fontsize=16, fontweight="bold", color="white", y=1.02,
    )

    # Donations comparison
    sns.barplot(
        data=df,
        x="industry",
        y="industry_donation_total",
        hue="on_relevant_committee",
        ax=axes[0],
        palette={True: "#00d4aa", False: "#555570"},
        alpha=0.85,
    )
    axes[0].set_title("Mean Industry Donations", fontsize=13, color="white")
    axes[0].set_ylabel("Mean PAC Donations ($)")
    axes[0].yaxis.set_major_formatter(FuncFormatter(dollar_fmt))
    axes[0].legend(title="On Relevant Committee", fontsize=9)
    axes[0].tick_params(axis="x", rotation=15)
    axes[0].grid(True, axis="y", alpha=0.3)

    # Bills comparison
    sns.barplot(
        data=df,
        x="industry",
        y="total_relevant_bills",
        hue="on_relevant_committee",
        ax=axes[1],
        palette={True: "#6c5ce7", False: "#555570"},
        alpha=0.85,
    )
    axes[1].set_title("Mean Relevant Bills", fontsize=13, color="white")
    axes[1].set_ylabel("Mean Relevant Bills (Sponsored + Co-sponsored)")
    axes[1].legend(title="On Relevant Committee", fontsize=9)
    axes[1].tick_params(axis="x", rotation=15)
    axes[1].grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "05_committee_effect.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {path}")


# ── Chart 6: Donation vs Bills Dual-Axis per Industry ────────────────────────

def plot_dual_axis_per_industry(df: pd.DataFrame):
    """
    For each industry, show legislator names with donation bars and bill
    count bars side-by-side, sorted by donation amount.
    """
    for industry, color in INDUSTRY_COLORS.items():
        sub = (
            df[df["industry"] == industry]
            .sort_values("industry_donation_total", ascending=True)
            .tail(15)  # top 15
        )
        if sub.empty:
            continue

        fig, ax1 = plt.subplots(figsize=(12, 8))
        y = range(len(sub))

        # Donations bars
        ax1.barh(
            [yi - 0.15 for yi in y],
            sub["industry_donation_total"],
            height=0.3,
            color=color,
            alpha=0.8,
            label="PAC Donations ($)",
        )
        ax1.set_xlabel("PAC Donations ($)", color=color)
        ax1.xaxis.set_major_formatter(FuncFormatter(dollar_fmt))
        ax1.tick_params(axis="x", colors=color)

        # Bills bars on secondary axis
        ax2 = ax1.twiny()
        ax2.barh(
            [yi + 0.15 for yi in y],
            sub["total_relevant_bills"],
            height=0.3,
            color="#ffffff",
            alpha=0.5,
            label="Relevant Bills",
        )
        ax2.set_xlabel("Relevant Bills", color="#cccccc")
        ax2.tick_params(axis="x", colors="#cccccc")

        labels = [
            f"{row['legislator_name']} ({row['party']})"
            for _, row in sub.iterrows()
        ]
        ax1.set_yticks(list(y))
        ax1.set_yticklabels(labels, fontsize=9)
        ax1.set_title(
            f"{industry}: Donations vs Relevant Bills",
            fontsize=14, fontweight="bold", color=color, pad=30,
        )
        ax1.grid(True, axis="x", alpha=0.2)

        # Combined legend
        from matplotlib.patches import Patch
        ax1.legend(
            handles=[
                Patch(facecolor=color, alpha=0.8, label="PAC Donations ($)"),
                Patch(facecolor="#ffffff", alpha=0.5, label="Relevant Bills"),
            ],
            loc="lower right", fontsize=9,
        )

        plt.tight_layout()
        slug = industry.lower().replace(" / ", "_").replace(" ", "_")
        path = os.path.join(OUTPUT_DIR, f"06_dual_{slug}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  ✓ {path}")


# ── Generate All Charts ──────────────────────────────────────────────────────

def generate_all_charts():
    """Generate all visualization charts."""
    print("\n═══ Generating Visualizations ═══\n")
    df = pd.read_csv(MERGED_CSV)

    plot_scatter_regression(df)
    plot_top_recipients(df)
    plot_correlation_heatmap(df)
    plot_donations_by_party(df)
    plot_committee_effect(df)
    plot_dual_axis_per_industry(df)

    # Network graphs (primary visualization per proposal)
    from visualize_network import generate_all_networks
    generate_all_networks()

    print(f"\n✓ All charts saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    generate_all_charts()
