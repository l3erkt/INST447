"""
visualize_network.py — Build NetworkX donor–legislator network graphs.

Produces one graph per policy topic, as described in the project proposal:
  - Legislator nodes: Red (R) or Blue (D) by party
  - Donor/PAC nodes: Colored by industry
  - Edges: PAC → Legislator, weighted by donation amount
  - Layout: Legislators grouped left (pro-industry vote) vs right (anti-industry)
            based on their roll-call vote alignment
  - Node size: Proportional to total donations received (legislators)
               or total amount donated (PACs)

Output: output/network_<topic>.png  (one per industry)
"""

import os
import math
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MERGED_CSV = os.path.join(DATA_DIR, "merged.csv")
VOTES_CSV  = os.path.join(DATA_DIR, "votes.csv")

# ── Styling ───────────────────────────────────────────────────────────────────
BG_COLOR   = "#0d0d1a"
NODE_TEXT  = "#e8e8f0"

PARTY_COLOR = {"D": "#4a90d9", "R": "#e74c3c", "?": "#888888"}

INDUSTRY_COLOR = {
    "Fossil Fuels":       "#ff6b35",
    "Data Centers / Tech": "#00d4aa",
    "Defense / Iran":     "#6c5ce7",
}

PAC_NODE_COLOR = {
    "Fossil Fuels":        "#ff9055",
    "Data Centers / Tech": "#00ffcc",
    "Defense / Iran":      "#9b8af0",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _scale(values, min_size: float, max_size: float) -> list[float]:
    """Min-max scale a series of values into a node-size range."""
    lo, hi = values.min(), values.max()
    if hi == lo:
        return [min_size] * len(values)
    return [min_size + (v - lo) / (hi - lo) * (max_size - min_size) for v in values]


# ── Main graph builder ────────────────────────────────────────────────────────

def build_network_for_topic(
    topic: str,
    merged_df: pd.DataFrame,
    votes_df: pd.DataFrame | None,
) -> None:
    """
    Build and save the donor–legislator network graph for one policy topic.
    """
    topic_donations = merged_df[merged_df["industry"] == topic].copy()
    if topic_donations.empty:
        print(f"  ⚠ No donation data for {topic}, skipping.")
        return

    # ── Build vote alignment lookup ────────────────────────────────────────
    # alignment: True = voted with industry, False = against, None = no vote
    alignment: dict[str, bool | None] = {}
    if votes_df is not None and not votes_df.empty:
        topic_votes = votes_df[votes_df["topic"] == topic]
        for bio, grp in topic_votes.groupby("bioguide_id"):
            aligned_vals = grp["aligned_with_industry"].dropna()
            if len(aligned_vals) == 0:
                alignment[bio] = None
            else:
                # Majority alignment across bills
                alignment[bio] = aligned_vals.mean() >= 0.5
    for bio in topic_donations["bioguide_id"].unique():
        alignment.setdefault(bio, None)

    # ── Build graph ────────────────────────────────────────────────────────
    G = nx.Graph()

    # Add legislator nodes
    for _, row in topic_donations.iterrows():
        bio  = row["bioguide_id"]
        name = row["legislator_name"]
        if bio not in G:
            G.add_node(
                bio,
                label=name.split()[-1],   # last name only
                full_name=name,
                node_type="legislator",
                party=row.get("party", "?"),
                donation=row.get("industry_donation_total", 0),
                aligned=alignment.get(bio),
            )

    # Add PAC nodes and edges (only PACs that donated to at least one legislator)
    # We'll reconstruct from raw donations.csv if available, else use merged totals.
    donations_csv = os.path.join(DATA_DIR, "donations.csv")
    if os.path.exists(donations_csv):
        raw = pd.read_csv(donations_csv)
        topic_raw = raw[(raw["industry"] == topic) & (raw["amount"] > 0)]
        for pac_name, pac_grp in topic_raw.groupby("pac_name"):
            pac_id = f"pac::{pac_name}"
            if pac_id not in G:
                G.add_node(
                    pac_id,
                    label=pac_name.replace(" PAC", "").replace(" Employees", ""),
                    node_type="pac",
                    total_donated=pac_grp["amount"].sum(),
                )
            for _, edge_row in pac_grp.iterrows():
                bio = edge_row["bioguide_id"]
                if bio in G:
                    existing = G.get_edge_data(pac_id, bio, default={}).get("weight", 0)
                    G.add_edge(pac_id, bio, weight=existing + edge_row["amount"])

    if len(G.nodes) == 0:
        print(f"  ⚠ Empty graph for {topic}, skipping.")
        return

    # ── Layout ────────────────────────────────────────────────────────────
    # Separate nodes by type and vote alignment for spatial grouping
    leg_nodes  = [n for n, d in G.nodes(data=True) if d.get("node_type") == "legislator"]
    pac_nodes  = [n for n, d in G.nodes(data=True) if d.get("node_type") == "pac"]

    pro_leg    = [n for n in leg_nodes if G.nodes[n]["aligned"] is True]
    anti_leg   = [n for n in leg_nodes if G.nodes[n]["aligned"] is False]
    neutral_leg= [n for n in leg_nodes if G.nodes[n]["aligned"] is None]

    pos = {}
    # Pro-industry legislators: left column
    for i, n in enumerate(pro_leg):
        pos[n] = (-2.5, -i * 1.2)
    # Anti-industry: right column
    for i, n in enumerate(anti_leg):
        pos[n] = (2.5, -i * 1.2)
    # No vote: center column
    for i, n in enumerate(neutral_leg):
        pos[n] = (0, -i * 1.2)
    # PAC nodes: scattered at top
    angle_step = 2 * math.pi / max(len(pac_nodes), 1)
    for i, n in enumerate(pac_nodes):
        angle = i * angle_step
        pos[n] = (4.5 * math.cos(angle), 4.5 * math.sin(angle) + 4)

    # Spring fallback for any unpositioned nodes
    unpositioned = [n for n in G.nodes if n not in pos]
    if unpositioned:
        spring = nx.spring_layout(G.subgraph(unpositioned), seed=42)
        pos.update(spring)

    # ── Draw ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(18, 14), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.axis("off")

    ind_color = INDUSTRY_COLOR.get(topic, "#888888")
    pac_color = PAC_NODE_COLOR.get(topic, "#aaaaaa")

    # Draw edges, weight → linewidth
    if G.edges:
        weights = [G[u][v].get("weight", 1) for u, v in G.edges()]
        max_w   = max(weights) if weights else 1
        for (u, v), w in zip(G.edges(), weights):
            nx.draw_networkx_edges(
                G, pos, edgelist=[(u, v)],
                width=0.5 + 3.0 * w / max_w,
                alpha=0.35,
                edge_color=ind_color,
                ax=ax,
            )

    # Draw legislator nodes (colored by party)
    for n in leg_nodes:
        party  = G.nodes[n].get("party", "?")
        col    = PARTY_COLOR.get(party, "#888888")
        donate = G.nodes[n].get("donation", 0)
        # Node size proportional to donation received
        size   = 300 + donate / 200
        nx.draw_networkx_nodes(
            G, pos, nodelist=[n],
            node_color=col, node_size=min(size, 2000),
            alpha=0.9, ax=ax,
        )

    # Draw PAC nodes
    if pac_nodes:
        pac_sizes = [300 + G.nodes[n].get("total_donated", 0) / 500 for n in pac_nodes]
        pac_sizes = [min(s, 2500) for s in pac_sizes]
        nx.draw_networkx_nodes(
            G, pos, nodelist=pac_nodes,
            node_color=pac_color, node_size=pac_sizes,
            node_shape="D", alpha=0.85, ax=ax,
        )

    # Labels
    labels = {n: G.nodes[n].get("label", n) for n in G.nodes()}
    nx.draw_networkx_labels(
        G, pos, labels=labels,
        font_size=8, font_color=NODE_TEXT, ax=ax,
    )

    # ── Legend ────────────────────────────────────────────────────────────
    legend_elements = [
        mpatches.Patch(facecolor=PARTY_COLOR["D"], label="Democrat"),
        mpatches.Patch(facecolor=PARTY_COLOR["R"], label="Republican"),
        mpatches.Patch(facecolor=pac_color,        label="PAC / Donor (♦)"),
        Line2D([0], [0], color=ind_color, linewidth=2, label="Donation edge (weight = $)"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=9,
              facecolor="#1a1a2e", labelcolor=NODE_TEXT, edgecolor="#333355")

    # Column labels
    if pro_leg or anti_leg or neutral_leg:
        col_y = ax.get_ylim()[1] * 0.95
        if pro_leg:
            ax.text(-2.5, col_y, "✓ Pro-Industry\n  Votes", ha="center",
                    fontsize=10, color="#00ff99", fontweight="bold")
        if anti_leg:
            ax.text(2.5, col_y, "✗ Anti-Industry\n  Votes", ha="center",
                    fontsize=10, color="#ff6688", fontweight="bold")
        if neutral_leg:
            ax.text(0, col_y, "— No Vote\n  Recorded", ha="center",
                    fontsize=10, color="#aaaaaa", fontweight="bold")

    fig.suptitle(
        f"Donor–Legislator Network: {topic}\n"
        f"119th Congress (2025) — Edge weight ∝ PAC Donation Amount",
        fontsize=15, fontweight="bold", color=NODE_TEXT, y=0.98,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    slug = topic.lower().replace(" / ", "_").replace(" ", "_")
    path = os.path.join(OUTPUT_DIR, f"network_{slug}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  ✓ {path}")


# ── Generate All Networks ─────────────────────────────────────────────────────

def generate_all_networks() -> None:
    """Generate network graphs for all three policy topics."""
    print("\n═══ Generating Network Graphs ═══\n")

    merged_df = pd.read_csv(MERGED_CSV) if os.path.exists(MERGED_CSV) else pd.DataFrame()
    votes_df  = pd.read_csv(VOTES_CSV)  if os.path.exists(VOTES_CSV)  else None

    for topic in ["Fossil Fuels", "Defense / Iran", "Data Centers / Tech"]:
        print(f"\n── {topic} ──")
        build_network_for_topic(topic, merged_df, votes_df)

    print(f"\n✓ All network graphs saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    generate_all_networks()
