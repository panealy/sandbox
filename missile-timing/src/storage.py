"""SQLite storage layer for missile alert data."""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'alerts.db')


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS alerts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id        TEXT    UNIQUE,
                timestamp_utc   TEXT    NOT NULL,
                timestamp_israel TEXT   NOT NULL,
                hour_of_day     INTEGER NOT NULL,
                day_of_week     INTEGER NOT NULL,
                city            TEXT    NOT NULL,
                threat_type     TEXT,
                raw_data        TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_alerts_city
                ON alerts (city);
            CREATE INDEX IF NOT EXISTS idx_alerts_hour
                ON alerts (hour_of_day);
            CREATE INDEX IF NOT EXISTS idx_alerts_ts
                ON alerts (timestamp_utc);

            CREATE TABLE IF NOT EXISTS locations (
                city        TEXT PRIMARY KEY,
                area        TEXT,
                lat         REAL,
                lng         REAL
            );

            CREATE TABLE IF NOT EXISTS meta (
                key     TEXT PRIMARY KEY,
                value   TEXT
            );
        """)


def insert_alert(
    alert_id: str,
    timestamp_utc: datetime,
    timestamp_israel: datetime,
    city: str,
    threat_type: str = None,
    raw_data: dict = None,
) -> bool:
    """Insert an alert record. Returns True if inserted, False if duplicate."""
    hour = timestamp_israel.hour
    dow = timestamp_israel.weekday()  # 0=Monday, 6=Sunday
    with get_db() as conn:
        try:
            conn.execute(
                """
                INSERT INTO alerts
                    (alert_id, timestamp_utc, timestamp_israel,
                     hour_of_day, day_of_week, city, threat_type, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert_id,
                    timestamp_utc.isoformat(),
                    timestamp_israel.isoformat(),
                    hour,
                    dow,
                    city,
                    threat_type,
                    json.dumps(raw_data) if raw_data else None,
                ),
            )
            return True
        except sqlite3.IntegrityError:
            return False  # duplicate


def upsert_location(city: str, area: str = None, lat: float = None, lng: float = None):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO locations (city, area, lat, lng)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(city) DO UPDATE SET
                area = COALESCE(excluded.area, area),
                lat  = COALESCE(excluded.lat,  lat),
                lng  = COALESCE(excluded.lng,  lng)
            """,
            (city, area, lat, lng),
        )


def get_meta(key: str) -> str | None:
    with get_db() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_meta(key: str, value: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_alert_count() -> int:
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]


def get_all_cities() -> list[str]:
    with get_db() as conn:
        rows = conn.execute("SELECT DISTINCT city FROM alerts ORDER BY city").fetchall()
        return [r["city"] for r in rows]


def get_alerts_for_analysis() -> list[dict]:
    """Return all alerts as dicts for analysis."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT city, hour_of_day, day_of_week, timestamp_utc, threat_type FROM alerts ORDER BY timestamp_utc"
        ).fetchall()
        return [dict(r) for r in rows]


def get_date_range() -> tuple[str | None, str | None]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT MIN(timestamp_utc) AS min_ts, MAX(timestamp_utc) AS max_ts FROM alerts"
        ).fetchone()
        return row["min_ts"], row["max_ts"]
