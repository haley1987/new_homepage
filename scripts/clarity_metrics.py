#!/usr/bin/env python3
"""Canonical, compact Clarity snapshot helpers.

The Clarity export API groups URL metrics by the complete URL. Marketing and
recommendation parameters therefore create thousands of rows for one page.
This module collapses those rows to pathname + device and provides one reader
for both the original raw snapshots (schema 1) and compact snapshots (schema 2).
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urlsplit

BEHAVIOR_METRICS = {
    "DeadClickCount": "dead_click",
    "ErrorClickCount": "error_click",
    "ExcessiveScroll": "excessive_scroll",
    "QuickbackClick": "quick_back",
    "RageClickCount": "rage_click",
    "ScriptErrorCount": "script_error",
}


def number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def canonical_path(raw_url):
    """Return a stable pathname; all query parameters and fragments are dropped."""
    if not raw_url:
        return "(unknown)"
    value = str(raw_url).strip()
    try:
        parsed = urlsplit(value)
        path = parsed.path if parsed.scheme or parsed.netloc else value.split("?", 1)[0].split("#", 1)[0]
        path = unquote(path or "/")
        path = re.sub(r"/{2,}", "/", path)
        if not path.startswith("/"):
            path = "/" + path
        return path.rstrip("/") or "/"
    except (TypeError, ValueError):
        return value.split("?", 1)[0].split("#", 1)[0] or "/"


def _metric_blocks(segment):
    data = segment.get("data", []) if isinstance(segment, dict) else []
    return data if isinstance(data, list) else []


def _weighted_average(total, weight):
    return round(total / weight, 2) if weight else 0.0


def compact_raw_snapshot(raw):
    """Convert a legacy raw API payload to schema 2 without retaining raw URLs."""
    segments = raw.get("segments", {})
    site_rows = {}

    for block in _metric_blocks(segments.get("device", {})):
        metric = block.get("metricName")
        for row in block.get("information", []):
            device = str(row.get("Device") or "(unknown)")
            item = site_rows.setdefault(device, {"device": device, "behaviors": {}})
            if metric == "Traffic":
                item["sessions"] = int(number(row.get("totalSessionCount")))
                item["bot_sessions"] = int(number(row.get("totalBotSessionCount")))
                item["pages_per_session"] = round(number(row.get("pagesPerSessionPercentage")), 2)
            elif metric == "EngagementTime":
                item["active_seconds"] = round(number(row.get("activeTime")), 2)
                item["total_seconds"] = round(number(row.get("totalTime")), 2)
            elif metric == "ScrollDepth":
                item["scroll_depth_pct"] = round(number(row.get("averageScrollDepth")), 2)
            elif metric in BEHAVIOR_METRICS:
                key = BEHAVIOR_METRICS[metric]
                item["behaviors"][key] = {
                    "eligible_sessions": int(number(row.get("sessionsCount"))),
                    "affected_sessions_est": round(
                        number(row.get("sessionsCount"))
                        * number(row.get("sessionsWithMetricPercentage"))
                        / 100.0,
                        2,
                    ),
                    "rate_pct": round(number(row.get("sessionsWithMetricPercentage")), 2),
                    "occurrences": int(number(row.get("subTotal"))),
                }

    page_rows = defaultdict(
        lambda: {
            "sessions": 0.0,
            "landing_sessions": 0.0,
            "bot_sessions": 0.0,
            "pages_per_session_total": 0.0,
            "pages_per_session_weight": 0.0,
            "active_total": 0.0,
            "active_weight": 0.0,
            "total_time_total": 0.0,
            "total_time_weight": 0.0,
            "scroll_total": 0.0,
            "scroll_weight": 0.0,
            "behaviors": defaultdict(lambda: {"eligible": 0.0, "affected": 0.0, "occurrences": 0.0}),
        }
    )
    page_sessions_by_raw = defaultdict(float)

    blocks = _metric_blocks(segments.get("url_device", {}))
    source_row_counts = {
        str(block.get("metricName") or "(unknown)"): len(block.get("information", [])) for block in blocks
    }
    capped_metrics = sorted(name for name, count in source_row_counts.items() if count >= 1000)
    for block in blocks:
        if block.get("metricName") not in BEHAVIOR_METRICS:
            continue
        for row in block.get("information", []):
            raw_url = row.get("Url") or row.get("URL")
            device = str(row.get("Device") or "(unknown)")
            key = (str(raw_url), device)
            page_sessions_by_raw[key] = max(page_sessions_by_raw[key], number(row.get("sessionsCount")))

    for (raw_url, device), sessions in page_sessions_by_raw.items():
        page_rows[(canonical_path(raw_url), device)]["sessions"] += sessions

    for block in blocks:
        if block.get("metricName") != "Traffic":
            continue
        for row in block.get("information", []):
            raw_url = row.get("Url") or row.get("URL")
            device = str(row.get("Device") or "(unknown)")
            key = (canonical_path(raw_url), device)
            sessions = number(row.get("totalSessionCount"))
            item = page_rows[key]
            item["landing_sessions"] += sessions
            item["bot_sessions"] += number(row.get("totalBotSessionCount"))
            if sessions:
                item["pages_per_session_total"] += number(row.get("pagesPerSessionPercentage")) * sessions
                item["pages_per_session_weight"] += sessions

    for block in blocks:
        metric = block.get("metricName")
        if metric == "Traffic":
            continue
        for row in block.get("information", []):
            raw_url = row.get("Url") or row.get("URL")
            device = str(row.get("Device") or "(unknown)")
            item = page_rows[(canonical_path(raw_url), device)]
            weight = page_sessions_by_raw.get((str(raw_url), device), 0.0)
            if metric == "EngagementTime" and weight:
                item["active_total"] += number(row.get("activeTime")) * weight
                item["active_weight"] += weight
                item["total_time_total"] += number(row.get("totalTime")) * weight
                item["total_time_weight"] += weight
            elif metric == "ScrollDepth" and weight:
                item["scroll_total"] += number(row.get("averageScrollDepth")) * weight
                item["scroll_weight"] += weight
            elif metric in BEHAVIOR_METRICS:
                behavior = item["behaviors"][BEHAVIOR_METRICS[metric]]
                eligible = number(row.get("sessionsCount"))
                behavior["eligible"] += eligible
                behavior["affected"] += eligible * number(row.get("sessionsWithMetricPercentage")) / 100.0
                behavior["occurrences"] += number(row.get("subTotal"))

    compact_pages = []
    for (path, device), item in sorted(page_rows.items()):
        if not item["sessions"] and not item["landing_sessions"]:
            continue
        behaviors = {}
        for name, values in sorted(item["behaviors"].items()):
            eligible = values["eligible"]
            behaviors[name] = {
                "eligible_sessions": int(eligible),
                "affected_sessions_est": round(values["affected"], 2),
                "rate_pct": round(values["affected"] / eligible * 100.0, 2) if eligible else 0.0,
                "occurrences": int(values["occurrences"]),
            }
        compact_pages.append(
            {
                "path": path,
                "device": device,
                "sessions": int(item["sessions"]),
                "landing_sessions": int(item["landing_sessions"]),
                "bot_sessions": int(item["bot_sessions"]),
                "pages_per_session": _weighted_average(
                    item["pages_per_session_total"], item["pages_per_session_weight"]
                ),
                "active_seconds": _weighted_average(item["active_total"], item["active_weight"]),
                "total_seconds": _weighted_average(item["total_time_total"], item["total_time_weight"]),
                "scroll_depth_pct": _weighted_average(item["scroll_total"], item["scroll_weight"]),
                "behaviors": behaviors,
            }
        )

    validation_sessions = int(
        number(raw.get("validation", {}).get("traffic_sessions"))
        or sum(row.get("sessions", 0) for row in site_rows.values())
    )
    return {
        "schema_version": 2,
        "collected_at": raw.get("collected_at"),
        "window_days": int(number(raw.get("window_days"), 3)),
        "canonicalization": "pathname_only",
        "data_quality": {
            "source_url_device_rows": source_row_counts,
            "suspected_row_cap": 1000,
            "capped_metrics": capped_metrics,
            "page_metrics_may_be_incomplete": bool(capped_metrics),
        },
        "site_device": sorted(site_rows.values(), key=lambda row: row["device"]),
        "page_device": compact_pages,
        "validation": {
            "traffic_sessions": validation_sessions,
            "passed": validation_sessions > 0,
        },
    }


def load_snapshot(path):
    doc = json.loads(Path(path).read_text())
    if doc.get("schema_version") == 2:
        return doc
    return compact_raw_snapshot(doc)


def collected_at(snapshot, fallback_path=None):
    value = snapshot.get("collected_at")
    if value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    if fallback_path:
        return datetime.fromisoformat(Path(fallback_path).stem + "T00:00:00+00:00")
    raise ValueError("Snapshot is missing collected_at")


def non_overlapping_snapshots(paths, newest_first=False):
    """Select rolling windows whose collection timestamps are at least one window apart."""
    loaded = [(Path(path), load_snapshot(path)) for path in paths]
    loaded.sort(key=lambda pair: collected_at(pair[1], pair[0]), reverse=newest_first)
    selected = []
    for path, snapshot in loaded:
        stamp = collected_at(snapshot, path)
        window = timedelta(days=int(snapshot.get("window_days", 3)))
        if not selected:
            selected.append((path, snapshot))
            continue
        prior_stamp = collected_at(selected[-1][1], selected[-1][0])
        if abs(stamp - prior_stamp) >= window:
            selected.append((path, snapshot))
    if newest_first:
        selected.reverse()
    return selected


def aggregate_pages(snapshots):
    """Aggregate compact page rows, weighting averages by page sessions."""
    out = defaultdict(
        lambda: {
            "sessions": 0.0,
            "landing_sessions": 0.0,
            "bot_sessions": 0.0,
            "pages_per_session_total": 0.0,
            "active_total": 0.0,
            "total_time_total": 0.0,
            "scroll_total": 0.0,
            "session_weight": 0.0,
            "landing_weight": 0.0,
            "behaviors": defaultdict(lambda: {"eligible": 0.0, "affected": 0.0, "occurrences": 0.0}),
        }
    )
    for snapshot in snapshots:
        for row in snapshot.get("page_device", []):
            key = (row["path"], row["device"])
            item = out[key]
            sessions = number(row.get("sessions"))
            landing_sessions = number(row.get("landing_sessions"))
            item["sessions"] += sessions
            item["landing_sessions"] += landing_sessions
            item["bot_sessions"] += number(row.get("bot_sessions"))
            item["pages_per_session_total"] += number(row.get("pages_per_session")) * landing_sessions
            item["active_total"] += number(row.get("active_seconds")) * sessions
            item["total_time_total"] += number(row.get("total_seconds")) * sessions
            item["scroll_total"] += number(row.get("scroll_depth_pct")) * sessions
            item["session_weight"] += sessions
            item["landing_weight"] += landing_sessions
            for name, behavior in row.get("behaviors", {}).items():
                target = item["behaviors"][name]
                target["eligible"] += number(behavior.get("eligible_sessions"))
                target["affected"] += number(behavior.get("affected_sessions_est"))
                target["occurrences"] += number(behavior.get("occurrences"))

    result = {}
    for key, item in out.items():
        session_weight = item["session_weight"]
        landing_weight = item["landing_weight"]
        behaviors = {}
        for name, values in item["behaviors"].items():
            eligible = values["eligible"]
            behaviors[name] = {
                "eligible_sessions": int(eligible),
                "affected_sessions_est": round(values["affected"], 2),
                "rate_pct": round(values["affected"] / eligible * 100.0, 2) if eligible else 0.0,
                "occurrences": int(values["occurrences"]),
            }
        result[key] = {
            "sessions": int(item["sessions"]),
            "landing_sessions": int(item["landing_sessions"]),
            "bot_sessions": int(item["bot_sessions"]),
            "pages_per_session": _weighted_average(item["pages_per_session_total"], landing_weight),
            "active_seconds": _weighted_average(item["active_total"], session_weight),
            "total_seconds": _weighted_average(item["total_time_total"], session_weight),
            "scroll_depth_pct": _weighted_average(item["scroll_total"], session_weight),
            "behaviors": behaviors,
        }
    return result
