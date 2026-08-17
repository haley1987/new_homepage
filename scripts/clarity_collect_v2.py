#!/usr/bin/env python3
import json
import os
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ["CLARITY_API_TOKEN"]
BASE = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
OUT = pathlib.Path("clarity-data/daily")
OUT.mkdir(parents=True, exist_ok=True)

WINDOW_DAYS = 3
QUERIES = {
    "device": ["Device"],
    "url_device": ["URL", "Device"],
    "url_country": ["URL", "Country/Region"],
    "url_source": ["URL", "Source"],
}


def fetch(dimensions):
    params = {"numOfDays": str(WINDOW_DAYS)}
    for i, dimension in enumerate(dimensions, start=1):
        params[f"dimension{i}"] = dimension

    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{BASE}?{query}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def traffic_sessions(data):
    for metric in data:
        if metric.get("metricName") != "Traffic":
            continue
        total = 0
        for row in metric.get("information", []):
            try:
                total += int(row.get("totalSessionCount", 0) or 0)
            except (TypeError, ValueError):
                pass
        return total
    return 0


stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
payload = {
    "collected_at": datetime.now(timezone.utc).isoformat(),
    "window_days": WINDOW_DAYS,
    "segments": {},
}

for name, dimensions in QUERIES.items():
    data = fetch(dimensions)
    payload["segments"][name] = {
        "dimensions": dimensions,
        "data": data,
        "traffic_sessions": traffic_sessions(data),
    }

# The one-dimension Device query is our sanity check. If this is zero while the
# Clarity dashboard has traffic, do not commit a misleading snapshot.
validation_sessions = payload["segments"]["device"]["traffic_sessions"]
payload["validation"] = {
    "segment": "device",
    "traffic_sessions": validation_sessions,
    "passed": validation_sessions > 0,
}

if validation_sessions <= 0:
    raise RuntimeError(
        "Clarity API returned zero sessions for the last 72 hours. "
        "Snapshot not saved; verify the token/project and API response."
    )

path = OUT / f"{stamp}.json"
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(f"Saved {path} with {validation_sessions} sessions in the 72-hour validation query")
