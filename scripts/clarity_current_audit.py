#!/usr/bin/env python3
"""Build a page diagnostic from the latest raw or compact snapshot."""

from datetime import date
from pathlib import Path

from clarity_metrics import aggregate_pages, load_snapshot

ROOT = Path("clarity-data/daily")
OUT = Path("clarity-data/reports")
OUT.mkdir(parents=True, exist_ok=True)

files = sorted(ROOT.glob("*.json"))
if not files:
    raise SystemExit("No Clarity snapshots found")

latest = files[-1]
pages = aggregate_pages([load_snapshot(latest)])


def ranked(metric, device, min_sessions=20, limit=15):
    result = []
    for (path, row_device), values in pages.items():
        if row_device != device or values["sessions"] < min_sessions:
            continue
        behavior = values["behaviors"].get(metric, {})
        rate = behavior.get("rate_pct", 0.0)
        if rate:
            result.append(
                (
                    rate,
                    behavior.get("affected_sessions_est", 0.0),
                    behavior.get("occurrences", 0),
                    values["sessions"],
                    path,
                )
            )
    result.sort(reverse=True)
    return result[:limit]


sections = [
    ("Mobile script errors", "script_error", "Mobile"),
    ("Desktop dead clicks", "dead_click", "PC"),
    ("Mobile quick-backs", "quick_back", "Mobile"),
    ("Desktop quick-backs", "quick_back", "PC"),
    ("Mobile rage clicks", "rage_click", "Mobile"),
    ("Desktop rage clicks", "rage_click", "PC"),
]

lines = [
    f"# Haywood Clarity Page Diagnostic — {date.today().isoformat()}",
    "",
    f"Source snapshot: `{latest.name}`. URLs are grouped by canonical pathname; query parameters are discarded.",
    "",
]

for title, metric, device in sections:
    lines += [
        f"## {title}",
        "",
        "| Page | Sessions | Affected sessions (est.) | Rate | Occurrences |",
        "|---|---:|---:|---:|---:|",
    ]
    rows = ranked(metric, device)
    if not rows:
        lines.append("| No page cleared the minimum traffic threshold |  |  |  |  |")
    else:
        for rate, affected, occurrences, sessions, path in rows:
            lines.append(
                f"| `{path.replace('|', '%7C')}` | {sessions} | {affected:.1f} | {rate:.1f}% | {occurrences} |"
            )
    lines.append("")

report = "\n".join(lines) + "\n"
path = OUT / f"current-page-diagnostic-{date.today().isoformat()}.md"
path.write_text(report)
print(report)
