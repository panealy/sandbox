#!/usr/bin/env python3
"""
dashboard.py — Start the web dashboard.

Usage:
    python dashboard.py                    # http://127.0.0.1:5001/
    python dashboard.py --port 8080
    python dashboard.py --host 0.0.0.0    # expose on all interfaces
    python dashboard.py --refresh          # re-run analysis before serving
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
    parser = argparse.ArgumentParser(description="Launch the missile alert timing dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--refresh", action="store_true",
                        help="Re-run analysis and update probabilities.json before starting")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    storage.init_db()

    if args.refresh:
        count = storage.get_alert_count()
        if count > 0:
            print(f"Refreshing analysis for {count} alerts…")
            result = analyzer.analyze()
            analyzer.save_report(result)
        else:
            print("No data in DB yet. Run collect.py first.")

    from src.dashboard.server import run
    print(f"\nDashboard: http://{args.host}:{args.port}/")
    print("Press Ctrl+C to stop.\n")
    run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
