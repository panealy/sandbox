"""
Data collector for Israeli missile/rocket alerts.

Sources:
  - Historical: oref.org.il AlertsHistory endpoint (requires Israeli IP or proxy)
  - Real-time polling: oref.org.il alerts.json (every 5 seconds)
  - Real-time WebSocket: tzevaadom.co.il WebSocket (works globally)
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone, timedelta

import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python < 3.9

from . import storage

logger = logging.getLogger(__name__)

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")

# Pikud Haoref API endpoints
OREF_BASE = "https://www.oref.org.il"
ALERTS_JSON = f"{OREF_BASE}/WarningMessages/alert/alerts.json"
HISTORY_JSON = f"{OREF_BASE}/WarningMessages/History/AlertsHistory.json"
LOCATIONS_JSON = f"{OREF_BASE}/Shared/Ajax/GetCitiesMix.aspx"

# Required headers to avoid 403s from oref.org.il
OREF_HEADERS = {
    "Referer": "https://www.oref.org.il/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (compatible; missile-timing-tracker/1.0)",
}

THREAT_TYPES = {
    "1":  "missiles_rockets",
    "2":  "UAV_drone",
    "3":  "earthquake",
    "4":  "tsunami",
    "5":  "hostile_aircraft",
    "6":  "dangerous_material",
    "7":  "nuclear",
    "8":  "gunfire",
    "13": "missiles_rockets",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_israel(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ISRAEL_TZ)


def _parse_oref_ts(date_str: str, time_str: str) -> datetime:
    """Parse oref date/time strings into UTC datetime."""
    # date_str: "17.05.2021"  time_str: "13:31"
    try:
        dt_israel = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
        dt_israel = dt_israel.replace(tzinfo=ISRAEL_TZ)
        return dt_israel.astimezone(timezone.utc)
    except ValueError:
        logger.warning("Could not parse date/time: %s %s", date_str, time_str)
        return _utc_now()


def _make_alert_id(city: str, ts_utc: datetime, threat: str = "") -> str:
    raw = f"{city}|{ts_utc.isoformat()}|{threat}"
    return hashlib.sha1(raw.encode()).hexdigest()


def fetch_locations():
    """Fetch the city/area mapping from oref.org.il and cache in DB."""
    try:
        resp = requests.get(LOCATIONS_JSON, headers=OREF_HEADERS, timeout=15)
        resp.raise_for_status()
        cities = resp.json()
        count = 0
        for city in cities:
            name = city.get("label_he") or city.get("label")
            area = city.get("areaname_he") or city.get("areaname")
            lat = city.get("lat")
            lng = city.get("lng")
            if name:
                storage.upsert_location(name, area=area, lat=lat, lng=lng)
                count += 1
        logger.info("Cached %d locations from oref.org.il", count)
    except Exception as exc:
        logger.warning("Could not fetch locations: %s", exc)


def fetch_history(from_date: str = None, to_date: str = None) -> int:
    """
    Fetch historical alerts from the oref.org.il AlertsHistory endpoint.

    Args:
        from_date: "YYYY-MM-DD" (defaults to 2023-01-01)
        to_date:   "YYYY-MM-DD" (defaults to today)

    Returns:
        Number of new alerts inserted.
    """
    if from_date is None:
        from_date = "2023-10-07"  # Beginning of major escalation
    if to_date is None:
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    params = {"fromDate": from_date, "toDate": to_date, "mode": 0}
    logger.info("Fetching historical alerts %s → %s", from_date, to_date)

    try:
        resp = requests.get(
            HISTORY_JSON, params=params, headers=OREF_HEADERS, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError as exc:
        logger.error(
            "Connection error fetching history (are you on an Israeli IP?): %s", exc
        )
        return 0
    except Exception as exc:
        logger.error("Error fetching history: %s", exc)
        return 0

    if not isinstance(data, list):
        data = data.get("alerts", data.get("data", []))

    inserted = 0
    for record in data:
        city = record.get("data", "")
        if not city:
            continue
        date_str = record.get("date", "")
        time_str = record.get("time", "")
        threat = str(record.get("category", record.get("alertType", "")))

        ts_utc = _parse_oref_ts(date_str, time_str)
        ts_israel = _to_israel(ts_utc)
        alert_id = _make_alert_id(city, ts_utc, threat)

        if storage.insert_alert(
            alert_id=alert_id,
            timestamp_utc=ts_utc,
            timestamp_israel=ts_israel,
            city=city,
            threat_type=THREAT_TYPES.get(threat, threat or None),
            raw_data=record,
        ):
            inserted += 1
            storage.upsert_location(city)

    logger.info("Inserted %d new historical alerts (out of %d fetched)", inserted, len(data))
    return inserted


def fetch_current_alerts() -> list[dict]:
    """Poll the real-time alerts.json endpoint. Returns list of active alert dicts."""
    try:
        resp = requests.get(ALERTS_JSON, headers=OREF_HEADERS, timeout=10)
        if resp.status_code == 204 or not resp.text.strip():
            return []  # No active alerts
        resp.raise_for_status()
        data = resp.json()
        cities = data.get("data", [])
        if not isinstance(cities, list):
            return []
        ts_utc = _utc_now()
        ts_israel = _to_israel(ts_utc)
        threat = str(data.get("cat", data.get("category", "1")))
        alerts = []
        for city in cities:
            if not city:
                continue
            alert_id = _make_alert_id(city, ts_utc, threat)
            alerts.append(
                {
                    "alert_id": alert_id,
                    "timestamp_utc": ts_utc,
                    "timestamp_israel": ts_israel,
                    "city": city,
                    "threat_type": THREAT_TYPES.get(threat, threat),
                    "raw_data": data,
                }
            )
        return alerts
    except requests.exceptions.ConnectionError as exc:
        logger.debug("Connection error polling alerts (Israeli IP needed?): %s", exc)
        return []
    except Exception as exc:
        logger.warning("Error polling current alerts: %s", exc)
        return []


def poll_realtime(interval_seconds: int = 5, stop_event=None):
    """
    Continuously poll the real-time alerts endpoint and save new alerts.

    Args:
        interval_seconds: Polling interval (default 5s).
        stop_event: Optional threading.Event to stop the loop.
    """
    logger.info("Starting real-time polling (interval=%ds)", interval_seconds)
    last_ids: set[str] = set()

    while True:
        if stop_event and stop_event.is_set():
            break

        alerts = fetch_current_alerts()
        current_ids = {a["alert_id"] for a in alerts}
        new_alerts = [a for a in alerts if a["alert_id"] not in last_ids]

        for alert in new_alerts:
            inserted = storage.insert_alert(**{k: alert[k] for k in alert})
            if inserted:
                logger.info(
                    "NEW ALERT: %s — %s (%s)",
                    alert["city"],
                    alert["threat_type"],
                    alert["timestamp_israel"].strftime("%H:%M:%S"),
                )
                storage.upsert_location(alert["city"])

        last_ids = current_ids
        time.sleep(interval_seconds)
