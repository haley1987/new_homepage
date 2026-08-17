#!/usr/bin/env python3
import json, os, pathlib, urllib.parse, urllib.request
from datetime import datetime, timezone

TOKEN = os.environ["CLARITY_API_TOKEN"]
BASE = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
OUT = pathlib.Path("clarity-data/daily")
OUT.mkdir(parents=True, exist_ok=True)

# Pull several useful segmentations while staying below Clarity's daily request limit.
queries = {
    "url_device": ["URL", "Device"],
    "url_country": ["URL", "Country/Region"],
    "url_source": ["URL", "Source"],
}

def fetch(dimensions):
    params = urllib.parse.urlencode({"numOfDays": 1, "dimensions": ",".join(dimensions)})
    req = urllib.request.Request(f"{BASE}?{params}", headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
payload = {"collected_at": datetime.now(timezone.utc).isoformat(), "window_days": 1, "segments": {}}
for name, dims in queries.items():
    payload["segments"][name] = {"dimensions": dims, "data": fetch(dims)}

path = OUT / f"{stamp}.json"
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(path)
