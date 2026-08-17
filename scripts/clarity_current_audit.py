#!/usr/bin/env python3
import json
import pathlib
from collections import defaultdict
from datetime import date
from urllib.parse import urlsplit

ROOT = pathlib.Path('clarity-data/daily')
OUT = pathlib.Path('clarity-data/reports')
OUT.mkdir(parents=True, exist_ok=True)

files = sorted(ROOT.glob('*.json'))
if not files:
    raise SystemExit('No Clarity snapshots found')

latest = files[-1]
doc = json.loads(latest.read_text())
seg = doc.get('segments', {}).get('url_device', {})
metrics = seg.get('data', [])


def canonical(raw):
    if not raw:
        return '(unknown)'
    try:
        p = urlsplit(str(raw))
        path = p.path or '/'
        return path.rstrip('/') or '/'
    except Exception:
        return str(raw)


def fnum(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

# key=(metric,path,device) -> denominator sessions + estimated affected sessions + occurrences
agg = defaultdict(lambda: {'sessions': 0.0, 'affected': 0.0, 'occurrences': 0.0})
traffic = defaultdict(float)

for block in metrics:
    name = block.get('metricName', '')
    for row in block.get('information', []):
        path = canonical(row.get('Url') or row.get('URL'))
        device = row.get('Device') or '(unknown)'
        if name == 'Traffic':
            sessions = fnum(row.get('totalSessionCount'))
            traffic[(path, device)] += sessions
            continue
        sessions = fnum(row.get('sessionsCount'))
        pct = fnum(row.get('sessionsWithMetricPercentage'))
        subtotal = fnum(row.get('subTotal'))
        key = (name, path, device)
        agg[key]['sessions'] += sessions
        agg[key]['affected'] += sessions * pct / 100.0
        agg[key]['occurrences'] += subtotal


def ranked(metric, device, min_sessions=20, limit=15):
    rows = []
    for (m, path, d), vals in agg.items():
        if m != metric or d != device:
            continue
        denom = vals['sessions'] or traffic.get((path, device), 0)
        if denom < min_sessions:
            continue
        rate = (vals['affected'] / denom * 100.0) if denom else 0
        rows.append((rate, vals['affected'], vals['occurrences'], denom, path))
    rows.sort(reverse=True)
    return rows[:limit]

sections = [
    ('Mobile script errors', 'ScriptErrorCount', 'Mobile', 20),
    ('Desktop dead clicks', 'DeadClickCount', 'PC', 20),
    ('Mobile quick backs', 'QuickbackClick', 'Mobile', 20),
    ('Desktop quick backs', 'QuickbackClick', 'PC', 20),
]

lines = [
    f'# Haywood Clarity Page Diagnostic — {date.today().isoformat()}',
    '',
    f'Source snapshot: `{latest.name}`. URLs are canonicalized so ad/UTM parameters do not split one page into many rows.',
    ''
]

for title, metric, device, minimum in sections:
    lines += [f'## {title}', '', '| Page | Sessions | Affected sessions (est.) | Rate | Occurrences |', '|---|---:|---:|---:|---:|']
    rows = ranked(metric, device, minimum)
    if not rows:
        lines.append('| No page cleared the minimum traffic threshold |  |  |  |  |')
    else:
        for rate, affected, occurrences, sessions, path in rows:
            safe = path.replace('|', '%7C')
            lines.append(f'| `{safe}` | {sessions:.0f} | {affected:.1f} | {rate:.1f}% | {occurrences:.0f} |')
    lines.append('')

report = '\n'.join(lines) + '\n'
path = OUT / f'current-page-diagnostic-{date.today().isoformat()}.md'
path.write_text(report)
print(report)
