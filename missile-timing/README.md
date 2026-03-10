# Missile Alert Timing Analysis

Tracks historical and real-time missile/rocket alert data from the Israeli Pikud Ha'Oref (Home Front Command) system and computes time-of-day probability distributions for each location.

## Quick Start

```bash
cd missile-timing
pip install -r requirements.txt

# 1. Fetch historical data (requires Israeli IP or proxy)
python collect.py --historical-only

# 2. Analyze and generate report
python analyze.py

# 3. View dashboard
python dashboard.py
# → open http://127.0.0.1:5001/
```

## Data Sources

- **Historical**: `oref.org.il/WarningMessages/History/AlertsHistory.json` — requires Israeli IP
- **Real-time polling**: `oref.org.il/WarningMessages/alert/alerts.json` — also requires Israeli IP
- Both sources are from the official Pikud Ha'Oref (Home Front Command) system

> **Note**: If you're outside Israel, you'll need a VPN or proxy with an Israeli exit node to fetch data from oref.org.il.

## Usage

### Collect data

```bash
# Historical backfill + ongoing real-time polling
python collect.py

# Historical only (exit after fetching)
python collect.py --historical-only

# Custom date range
python collect.py --from 2023-10-07 --to 2024-12-31 --historical-only

# Real-time only (no historical backfill)
python collect.py --realtime-only --interval 5
```

### Analyze

```bash
# Full analysis: print summary + save reports/probabilities.json
python analyze.py

# Save JSON only (no console output)
python analyze.py --json-only

# Print summary only (don't save)
python analyze.py --no-save
```

### Dashboard

```bash
# Start dashboard (auto-uses cached report if available)
python dashboard.py

# Re-run analysis before starting
python dashboard.py --refresh

# Custom port / expose externally
python dashboard.py --port 8080 --host 0.0.0.0
```

## Dashboard Features

- **Global statistics**: total alerts, days tracked, peak hour
- **Hourly probability chart**: P(alert | hour) for all of Israel
- **Day-of-week breakdown**
- **Per-city analysis**: select any city to see its hourly probability and DoW charts
- **Heatmap**: alert frequency by hour × day of week
- **City rankings table**: sortable by alerts, peak hour, max probability

## Project Structure

```
missile-timing/
├── collect.py          # CLI: fetch historical + real-time data
├── analyze.py          # CLI: run analysis, print + save report
├── dashboard.py        # CLI: start web dashboard
├── requirements.txt
├── data/
│   └── alerts.db       # SQLite database (auto-created)
├── reports/
│   └── probabilities.json  # Analysis output (auto-generated)
└── src/
    ├── collector.py    # Data fetching (historical + polling)
    ├── storage.py      # SQLite operations
    ├── analyzer.py     # Probability calculations
    └── dashboard/
        ├── server.py   # Flask app
        ├── templates/index.html
        └── static/app.js
```

## Probability Definition

For each location and each hour `h` (0–23, Israel time):

```
P(alert at hour h) = (number of days with ≥1 alert in hour h) / (total days tracked)
```

This gives the probability that, on any given day, the location will receive an alert during that hour.
