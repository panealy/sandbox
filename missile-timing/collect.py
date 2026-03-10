#!/usr/bin/env python3
"""
collect.py — Fetch missile alert data (historical + real-time polling).

Usage:
    python collect.py                     # historical backfill + start polling
    python collect.py --historical-only   # fetch historical data and exit
    python collect.py --realtime-only     # start polling without historical fetch
    python collect.py --from 2023-10-07 --to 2024-12-31  # custom date range
    python collect.py --interval 10       # poll every 10 seconds (default: 5)
"""

import argparse
import logging
import threading

from src import storage
from src import collector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(description="Collect missile alert data")
    parser.add_argument("--historical-only", action="store_true",
                        help="Only fetch historical data, then exit")
    parser.add_argument("--realtime-only", action="store_true",
                        help="Only poll in real-time, skip historical fetch")
    parser.add_argument("--from", dest="from_date", default=None,
                        metavar="YYYY-MM-DD", help="Start date for historical fetch")
    parser.add_argument("--to", dest="to_date", default=None,
                        metavar="YYYY-MM-DD", help="End date for historical fetch")
    parser.add_argument("--interval", type=int, default=5,
                        help="Real-time polling interval in seconds (default: 5)")
    args = parser.parse_args()

    storage.init_db()

    if not args.realtime_only:
        print("Fetching city/location metadata…")
        collector.fetch_locations()
        print(f"Fetching historical alerts ({args.from_date or '2023-10-07'} → {args.to_date or 'today'})…")
        inserted = collector.fetch_history(
            from_date=args.from_date,
            to_date=args.to_date,
        )
        print(f"Done. {inserted} new alerts inserted. Total in DB: {storage.get_alert_count()}")

    if args.historical_only:
        return

    print(f"\nStarting real-time polling every {args.interval}s. Press Ctrl+C to stop.")
    try:
        collector.poll_realtime(interval_seconds=args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
