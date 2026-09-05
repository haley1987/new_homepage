#!/usr/bin/env python3
"""Build a compact, canonical, non-overlapping weekly Clarity report."""

from datetime import date
from pathlib import Path

from clarity_metrics import aggregate_pages, collected_at, load_snapshot

ROOT = Path("clarity-data/daily")
OUT = Path("clarity-data/reports")
OUT.mkdir(parents=True, exist_ok=True)

MIN_SESSIONS = 30
METRICS = (
    ("quick_back", "Quick-backs"),
    ("dead_click", "Dead clicks"),
    ("script_error", "Script errors"),
    ("rage_click", "Rage clicks"),
)


def snapshot_label(path, snapshot):
    return f"{path.stem} ({int(snapshot.get('window_days', 3))}-day window)"


files = sorted(ROOT.glob("*.json"))
if not files:
    raise SystemExit("No Clarity snapshots found")

latest_path = files[-1]
latest = load_snapshot(latest_path)
latest_stamp = collected_at(latest, latest_path)
window_days = int(latest.get("window_days", 3))

prior_pair = None
for candidate_path in reversed(files[:-1]):
    candidate = load_snapshot(candidate_path)
    delta_days = (latest_stamp - collected_at(candidate, candidate_path)).total_seconds() / 86400
    if delta_days >= window_days:
        prior_pair = (candidate_path, candidate)
        break

lines = [
    f"# Haywood Clarity CRO Audit — {date.today().isoformat()}",
    "",
    f"Recent: `{snapshot_label(latest_path, latest)}`. URLs are grouped by canonical pathname; query parameters are discarded.",
    "",
    "The report uses one 72-hour window per period so rolling daily exports are not double-counted. Rates use each metric's eligible-session denominator.",
    "",
]
if latest.get("data_quality", {}).get("page_metrics_may_be_incomplete"):
    capped = ", ".join(latest["data_quality"].get("capped_metrics", []))
    lines += [
        f"Data-quality note: the source API returned its apparent 1,000-row ceiling for: {capped}. "
        "Canonical page values are therefore lower bounds when parameter variants displaced rows.",
        "",
    ]

if not prior_pair:
    lines += ["## Baseline building", "", "A non-overlapping prior window is not available yet."]
else:
    prior_path, prior = prior_pair
    current = aggregate_pages([latest])
    baseline = aggregate_pages([prior])
    lines += [f"Prior comparison: `{snapshot_label(prior_path, prior)}`.", ""]

    candidates = []
    for (page_path, device), row in current.items():
        if row["sessions"] < MIN_SESSIONS:
            continue
        for metric, label in METRICS:
            behavior = row["behaviors"].get(metric, {})
            rate = behavior.get("rate_pct", 0.0)
            affected = behavior.get("affected_sessions_est", 0.0)
            old = baseline.get((page_path, device), {}).get("behaviors", {}).get(metric, {})
            old_rate = old.get("rate_pct", 0.0)
            delta = rate - old_rate
            if rate <= 0:
                continue
            score = affected + max(delta, 0) * 0.5
            candidates.append((score, page_path, device, label, rate, old_rate, affected, row["sessions"]))

    candidates.sort(reverse=True)
    lines += [
        "## Highest current friction",
        "",
        "| Page | Device | Signal | Sessions | Affected (est.) | Recent | Prior | Change |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    shown = 0
    for _, page_path, device, label, rate, old_rate, affected, sessions in candidates:
        if page_path == "/cart" and label == "Dead clicks":
            continue
        lines.append(
            f"| `{page_path.replace('|', '%7C')}` | {device} | {label} | {sessions} | {affected:.1f} | "
            f"{rate:.1f}% | {old_rate:.1f}% | {rate - old_rate:+.1f} pp |"
        )
        shown += 1
        if shown == 15:
            break
    if shown == 0:
        lines.append("| No page cleared the traffic threshold |  |  |  |  |  |  |  |")

    lines += [
        "",
        "## Interpretation guardrails",
        "",
        "- `/cart` dead clicks are excluded because the mandatory checkout-confirmation checkbox intentionally blocks unconfirmed clicks.",
        "- A Clarity signal identifies where to inspect recordings/heatmaps; it does not by itself prove a storefront defect.",
        "- Change production code only after the affected control or script error is identified reproducibly.",
    ]

report = "\n".join(lines) + "\n"
path = OUT / f"{date.today().isoformat()}.md"
path.write_text(report)
print(report)
