"""
Timing analysis and probability calculator for missile alert data.

Computes, for each tracked location:
  - P(alert | hour h) = days with ≥1 alert in hour h / total tracked days
  - Alert count per hour (absolute frequency)
  - Most dangerous hours
  - Day-of-week breakdown

Also computes global (all-Israel) statistics.
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from . import storage

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
HOURS = list(range(24))
DOW_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _date_range_days(min_ts: str, max_ts: str) -> int:
    """Return number of calendar days between two ISO timestamps."""
    try:
        d1 = datetime.fromisoformat(min_ts).date()
        d2 = datetime.fromisoformat(max_ts).date()
        return max(1, (d2 - d1).days + 1)
    except Exception:
        return 1


def analyze() -> dict:
    """
    Run the full analysis and return a structured result dict.

    Structure:
    {
        "generated_at": "...",
        "date_range": {"from": "...", "to": "..."},
        "total_days_tracked": 123,
        "total_alerts": 456,
        "global": {
            "hourly_counts": [0..23 counts],
            "hourly_probabilities": [0..23 probs],
            "peak_hour": 14,
            "dow_counts": [Mon..Sun counts]
        },
        "cities": {
            "Tel Aviv": {
                "total_alerts": 12,
                "hourly_counts": [...],
                "hourly_probabilities": [...],
                "peak_hour": 10,
                "dow_counts": [...]
            },
            ...
        }
    }
    """
    alerts = storage.get_alerts_for_analysis()
    if not alerts:
        logger.warning("No alerts in database. Run the collector first.")
        return {}

    min_ts, max_ts = storage.get_date_range()
    total_days = _date_range_days(min_ts, max_ts)

    # ── Global counters ──────────────────────────────────────────────────────
    global_hourly_counts = [0] * 24
    global_dow_counts = [0] * 7
    # Track which (date, hour) combinations had alerts to compute daily probs
    global_day_hour_set: set[tuple] = set()

    # ── Per-city counters ────────────────────────────────────────────────────
    city_hourly_counts: dict[str, list[int]] = defaultdict(lambda: [0] * 24)
    city_dow_counts: dict[str, list[int]] = defaultdict(lambda: [0] * 7)
    city_day_hour_set: dict[str, set] = defaultdict(set)
    city_first_last: dict[str, list] = {}  # [min_ts, max_ts]

    for alert in alerts:
        city = alert["city"]
        hour = alert["hour_of_day"]
        dow = alert["day_of_week"]
        ts_str = alert["timestamp_utc"]

        try:
            ts = datetime.fromisoformat(ts_str)
            date_key = ts.date()
        except Exception:
            date_key = None

        # Global
        global_hourly_counts[hour] += 1
        global_dow_counts[dow] += 1
        if date_key:
            global_day_hour_set.add((date_key, hour))

        # Per city
        city_hourly_counts[city][hour] += 1
        city_dow_counts[city][dow] += 1
        if date_key:
            city_day_hour_set[city].add((date_key, hour))

        if city not in city_first_last:
            city_first_last[city] = [ts_str, ts_str]
        else:
            if ts_str < city_first_last[city][0]:
                city_first_last[city][0] = ts_str
            if ts_str > city_first_last[city][1]:
                city_first_last[city][1] = ts_str

    # ── Global probabilities ─────────────────────────────────────────────────
    global_hourly_probs = []
    for h in HOURS:
        days_with_alert = sum(1 for (d, hour) in global_day_hour_set if hour == h)
        global_hourly_probs.append(round(days_with_alert / total_days, 6))

    # ── Per-city probabilities ───────────────────────────────────────────────
    cities_result = {}
    for city in sorted(city_hourly_counts.keys()):
        city_days = _date_range_days(
            city_first_last[city][0], city_first_last[city][1]
        )
        hourly_probs = []
        dh_set = city_day_hour_set[city]
        for h in HOURS:
            days_with_alert = sum(1 for (d, hour) in dh_set if hour == h)
            hourly_probs.append(round(days_with_alert / city_days, 6))

        counts = city_hourly_counts[city]
        peak = counts.index(max(counts))
        cities_result[city] = {
            "total_alerts": sum(counts),
            "days_tracked": city_days,
            "hourly_counts": counts,
            "hourly_probabilities": hourly_probs,
            "peak_hour": peak,
            "dow_counts": city_dow_counts[city],
        }

    global_peak = global_hourly_counts.index(max(global_hourly_counts))

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_range": {"from": min_ts, "to": max_ts},
        "total_days_tracked": total_days,
        "total_alerts": len(alerts),
        "global": {
            "hourly_counts": global_hourly_counts,
            "hourly_probabilities": global_hourly_probs,
            "peak_hour": global_peak,
            "dow_counts": global_dow_counts,
        },
        "cities": cities_result,
    }

    return result


def save_report(result: dict) -> str:
    """Save analysis result to JSON file. Returns file path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, "probabilities.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("Saved report to %s", path)
    return path


def print_summary(result: dict):
    """Print a human-readable summary to stdout."""
    if not result:
        print("No data available.")
        return

    print("\n" + "=" * 60)
    print("MISSILE ALERT TIMING ANALYSIS")
    print("=" * 60)
    print(f"Generated:     {result['generated_at']}")
    print(f"Date range:    {result['date_range']['from']} → {result['date_range']['to']}")
    print(f"Days tracked:  {result['total_days_tracked']}")
    print(f"Total alerts:  {result['total_alerts']}")
    print(f"Cities:        {len(result['cities'])}")

    g = result["global"]
    peak_h = g["peak_hour"]
    print(f"\nGLOBAL PEAK HOUR (Israel time): {peak_h:02d}:00 — {peak_h+1:02d}:00")

    print("\nHourly probability of alert anywhere in Israel:")
    print("  Hour  Probability  Bar")
    for h, prob in enumerate(g["hourly_probabilities"]):
        bar = "█" * int(prob * 40)
        print(f"  {h:02d}:00  {prob:.4f}       {bar}")

    print("\nDay-of-week alert counts:")
    for i, name in enumerate(DOW_NAMES):
        print(f"  {name:<12} {g['dow_counts'][i]}")

    print("\nTop 10 most-alerted cities:")
    top_cities = sorted(
        result["cities"].items(), key=lambda x: x[1]["total_alerts"], reverse=True
    )[:10]
    for city, data in top_cities:
        print(f"  {city:<30} {data['total_alerts']:>5} alerts  peak={data['peak_hour']:02d}:00")

    print()
