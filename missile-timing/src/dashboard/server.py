"""Flask web dashboard server."""

import json
import logging
import os

from flask import Flask, jsonify, render_template, send_from_directory

from .. import storage
from .. import analyzer as _analyzer

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analysis")
def api_analysis():
    """Return the latest analysis as JSON, computing on-the-fly if no cached report exists."""
    cached_path = os.path.join(REPORTS_DIR, "probabilities.json")
    if os.path.exists(cached_path):
        with open(cached_path, encoding="utf-8") as f:
            return app.response_class(
                response=f.read(), status=200, mimetype="application/json"
            )
    # Compute on-the-fly
    result = _analyzer.analyze()
    if not result:
        return jsonify({"error": "No data available. Run the collector first."}), 404
    return jsonify(result)


@app.route("/api/cities")
def api_cities():
    cities = storage.get_all_cities()
    return jsonify(cities)


@app.route("/api/stats")
def api_stats():
    count = storage.get_alert_count()
    min_ts, max_ts = storage.get_date_range()
    return jsonify({"total_alerts": count, "from": min_ts, "to": max_ts})


def run(host: str = "127.0.0.1", port: int = 5001, debug: bool = False):
    logger.info("Starting dashboard at http://%s:%d/", host, port)
    app.run(host=host, port=port, debug=debug)
