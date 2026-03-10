#!/usr/bin/env python3
"""
analyze.py — Run timing analysis and output results.

Usage:
    python analyze.py                 # analyze + print summary + save JSON
    python analyze.py --json-only     # save JSON without printing
    python analyze.py --no-save       # print summary without saving JSON
"""

import argparse
import logging

from src import storage
from src import analyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(description="Analyze missile alert timing data")
    parser.add_argument("--json-only", action="store_true",
                        help="Save JSON report without printing summary")
    parser.add_argument("--no-save", action="store_true",
                        help="Print summary without saving JSON")
    args = parser.parse_args()

    storage.init_db()

    count = storage.get_alert_count()
    if count == 0:
        print("No data in database. Run: python collect.py --historical-only")
        return

    print(f"Analyzing {count} alerts…")
    result = analyzer.analyze()

    if not args.json_only:
        analyzer.print_summary(result)

    if not args.no_save:
        path = analyzer.save_report(result)
        print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()
