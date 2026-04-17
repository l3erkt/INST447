"""
main.py — Orchestrator for The Lobbying Subsidy Tracker pipeline.

Runs the full data pipeline:
  1. Fetch FEC donation data     → data/donations.csv
  2. Fetch Congress.gov data     → data/legislation.csv
  3. Merge datasets              → data/merged.csv
  4. Run statistical analysis    → output/analysis_report.txt
  5. Generate visualizations     → output/*.png

Usage:
  python main.py                     # Run full pipeline
  python main.py --skip-fetch        # Use cached data, just re-analyze
  python main.py --fetch-only        # Only fetch data, don't analyze
  python main.py --analyze-only      # Only run analysis + charts (data must exist)
"""

import argparse
import os
import sys
import time


def main():
    parser = argparse.ArgumentParser(
        description="The Lobbying Subsidy Tracker — Correlating PAC donations with legislation",
    )
    parser.add_argument(
        "--skip-fetch", action="store_true",
        help="Skip API fetching, use cached CSVs in data/",
    )
    parser.add_argument(
        "--fetch-only", action="store_true",
        help="Only fetch data from APIs, don't run analysis",
    )
    parser.add_argument(
        "--analyze-only", action="store_true",
        help="Only run analysis + visualization (data must exist)",
    )
    args = parser.parse_args()

    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║              THE LOBBYING SUBSIDY TRACKER                          ║
║                                                                    ║
║  Correlating PAC Donations with Legislative Decisions              ║
║  2024 Election Cycle — 119th Congress                              ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

    start_time = time.time()

    # ── Step 1: Fetch FEC Data ────────────────────────────────────────────
    if not args.skip_fetch and not args.analyze_only:
        sep = '═' * 60
        print(f"\n{sep}")
        print("  STEP 1: Fetching FEC Donation Data")
        print(f"{sep}\n")
        from fetch_fec import fetch_all_donations
        donations = fetch_all_donations()
        print(f"\n  Donation records: {len(donations)}")
        print(f"  Non-zero donations: {(donations['amount'] > 0).sum()}")
    else:
        print("\n⏩ Skipping FEC fetch (using cached data)")

    # ── Step 2: Fetch Congress Data ───────────────────────────────────────
    if not args.skip_fetch and not args.analyze_only:
        sep = '═' * 60
        print(f"\n{sep}")
        print("  STEP 2: Fetching Congress.gov Legislative Data")
        print(f"{sep}\n")
        from fetch_congress import fetch_all_legislation
        legislation = fetch_all_legislation()
        print(f"\n  Legislation records: {len(legislation)}")
    # ── Step 2.5: Fetch Roll-Call Votes ─────────────────────────────────────
    if not args.skip_fetch and not args.analyze_only:
        sep = '═' * 60
        print(f"\n{sep}")
        print("  STEP 2.5: Fetching Roll-Call Vote Records")
        print(f"{sep}\n")
        from fetch_votes import fetch_all_votes
        votes = fetch_all_votes()
        print(f"\n  Vote records: {len(votes)}")
    else:
        print("⏩ Skipping vote fetch (using cached data)")

    if args.fetch_only:
        elapsed = time.time() - start_time
        print(f"\n✓ Data fetching complete in {elapsed:.1f}s")
        return

    # ── Step 3: Merge Datasets ────────────────────────────────────────────
    sep = '═' * 60
    print(f"\n{sep}")
    print("  STEP 3: Merging Datasets")
    print(f"{sep}\n")
    from merge_data import merge_datasets
    merged = merge_datasets()
    print(f"\n  Merged records: {len(merged)}")

    # ── Step 4: Statistical Analysis ──────────────────────────────────────
    sep = '═' * 60
    print(f"\n{sep}")
    print("  STEP 4: Statistical Analysis")
    print(f"{sep}\n")
    from analysis import run_analysis
    run_analysis()

    # ── Step 5: Visualizations ────────────────────────────────────────────
    sep = '═' * 60
    print(f"\n{sep}")
    print("  STEP 5: Generating Visualizations")
    print(f"{sep}\n")
    from visualize import generate_all_charts
    generate_all_charts()

    sep = '═' * 60
    print(f"\n{sep}")
    print("  STEP 5b: Generating Network Graphs")
    print(f"{sep}\n")
    from visualize_network import generate_all_networks
    generate_all_networks()

    # ── Done ──────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  ✓ PIPELINE COMPLETE                                               ║
║                                                                    ║
║  Data:     data/donations.csv, legislation.csv, merged.csv         ║
║  Report:   output/analysis_report.txt                              ║
║  Charts:   output/*.png                                            ║
║                                                                    ║
║  Time elapsed: {elapsed:.1f}s{' ' * (53 - len(f'{elapsed:.1f}'))}║
╚══════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
