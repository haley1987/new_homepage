#!/usr/bin/env python3
import json, pathlib, statistics
from collections import defaultdict
from datetime import date

ROOT = pathlib.Path("clarity-data/daily")
OUT = pathlib.Path("clarity-data/reports")
OUT.mkdir(parents=True, exist_ok=True)
FILES = sorted(ROOT.glob("*.json"))

BAD_KEYS = ("rage", "dead", "quick", "excessive", "error")
MIN_CURRENT = 5
PCT_ALERT = 0.30


def rows(obj):
    if isinstance(obj, list):
        for x in obj:
            if isinstance(x, dict): yield x
    elif isinstance(obj, dict):
        for key in ("data", "result", "results"):
            if key in obj:
                yield from rows(obj[key])


def flatten(dayfile):
    doc=json.loads(dayfile.read_text())
    out=[]
    for seg in doc.get("segments",{}).values():
        for r in rows(seg.get("data")):
            out.append(r)
    return out


def numeric(d):
    out={}
    for k,v in d.items():
        try: out[k]=float(v)
        except (TypeError,ValueError): pass
    return out

recent=FILES[-7:]
prior=FILES[-14:-7]
lines=[f"# Haywood Clarity CRO Audit — {date.today().isoformat()}", ""]
if len(recent)<7 or len(prior)<7:
    lines += ["## Baseline building", "", f"Only {len(FILES)} daily snapshot(s) exist. The watchdog needs 14 days before week-over-week anomaly alerts are reliable."]
else:
    def aggregate(files):
        vals=defaultdict(list)
        for f in files:
            for r in flatten(f):
                label = str(r.get("URL") or r.get("url") or r.get("Page") or "sitewide")
                for k,v in numeric(r).items():
                    if any(b in k.lower() for b in BAD_KEYS): vals[(label,k)].append(v)
        return {k:sum(v) for k,v in vals.items()}
    cur,old=aggregate(recent),aggregate(prior)
    alerts=[]
    for key,c in cur.items():
        o=old.get(key,0)
        if c < MIN_CURRENT: continue
        change=(c-o)/max(o,1)
        if change >= PCT_ALERT: alerts.append((change,key,c,o))
    alerts.sort(reverse=True)
    if not alerts:
        lines += ["## No material friction spikes detected", "", "No tracked negative-behavior metric cleared the current alert thresholds this week."]
    else:
        lines += ["## Actionable friction spikes", ""]
        for change,(url,metric),c,o in alerts[:15]:
            lines.append(f"- **{metric}** on `{url}`: {c:.0f} vs {o:.0f} prior week (**{change:+.0%}**).")
        lines += ["", "## Triage", "", "Review the highest-volume/highest-change pages first. Confirm the behavior in Clarity recordings/heatmaps before changing production code."]

report="\n".join(lines)+"\n"
path=OUT/f"{date.today().isoformat()}.md"
path.write_text(report)
print(report)
