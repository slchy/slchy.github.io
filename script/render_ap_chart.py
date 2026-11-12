#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "gamedata.json"
STATS_PATH = ROOT / "data" / "stats_difference.json"
SVG_PATH = ROOT / "image" / "ingress_data.svg"
CHART_TIMEZONE = timezone(timedelta(hours=8))
STATS_FIELDS = [
    ("xm collected", "xm_collected"),
    ("glyph points", "glyph_points"),
    ("portals visited", "portals_visited"),
    ("unique portals captured", "unique_portals_captured"),
    ("links destroyed", "links_destroyed"),
    ("fields destroyed", "fields_destroyed"),
    ("resonators deployed", "resonators_deployed"),
]


def load_points(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError("gamedata.json must be a non-empty array")

    points = []
    for item in data:
        if not isinstance(item, dict):
            continue
        stats = item.get("stats") or {}
        ap = stats.get("ap")
        ts = item.get("timestamp")
        if isinstance(ap, (int, float)) and isinstance(ts, (int, float)):
            points.append((ts, float(ap)))

    points.sort(key=lambda p: p[0])
    if len(points) < 1:
        raise ValueError("No usable ap points found in gamedata.json")
    return points


def format_date(ts):
    return datetime.fromtimestamp(ts, tz=CHART_TIMEZONE).strftime("%m-%d")


def format_ap(value):
    return f"{value / 1_000_000:.2f}M"


def load_stats_difference(path: Path):
    fallback = {key: 0 for _, key in STATS_FIELDS}
    try:
        if not path.exists():
            return fallback
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        stats = payload.get("stats_difference")
        if not isinstance(stats, dict):
            return fallback
        result = dict(fallback)
        for _, key in STATS_FIELDS:
            value = stats.get(key, 0)
            if isinstance(value, bool):
                value = int(value)
            elif isinstance(value, (int, float)):
                value = int(round(value))
            else:
                try:
                    value = int(float(value))
                except Exception:
                    value = 0
            result[key] = value
        return result
    except Exception:
        return fallback


def format_int(value):
    return f"{int(value):,}"


def build_chart(points, width=136, height=141):
    if not points:
        return "\n".join([
            '      <text class="axis-label" x="68" y="72" text-anchor="middle">NO DATA</text>',
            '      <text class="axis-label" x="68" y="80" text-anchor="middle">Waiting for gamedata.json</text>',
        ])

    dense = len(points) > 7
    left = 20
    right = 8
    top = 16
    bottom = 24

    xs = width - left - right
    ys = height - top - bottom

    values = [value for _, value in points]
    min_v = min(values)
    max_v = max(values)
    span = max(max_v - min_v, 1.0)
    pad = max(span * 0.08, 1.0)
    min_v -= pad
    max_v += pad
    span = max(max_v - min_v, 1.0)

    count = len(points)
    day_counts = {}
    for ts, _value in points:
        day = format_date(ts)
        day_counts[day] = day_counts.get(day, 0) + 1

    def map_x(index):
        if count == 1:
            return left + xs / 2
        return left + xs * index / (count - 1)

    def map_y(value):
        return top + (max_v - value) * ys / span

    coords = [(map_x(i), map_y(value)) for i, (_, value) in enumerate(points)]
    y_ticks = []
    for ratio in (0, 1 / 3, 2 / 3, 1):
        value = min_v + span * ratio
        y = top + ys * (1 - ratio)
        y_ticks.append((y, value))

    def fmt(n):
        return f"{n:.2f}".rstrip("0").rstrip(".")

    path_cmds = [f"M {fmt(coords[0][0])} {fmt(coords[0][1])}"]
    for x, y in coords[1:]:
        path_cmds.append(f"L {fmt(x)} {fmt(y)}")

    lines = []
    axis_font_size = "2.7px" if dense else "3.2px"
    date_font_size = "2.5px" if dense else "3.2px"
    axis_x = 18.5
    axis_y = 117
    lines.append(f'      <line class="axis-line" x1="{fmt(axis_x)}" y1="{top}" x2="{fmt(axis_x)}" y2="{axis_y}" />')
    lines.append(f'      <line class="axis-line" x1="{fmt(axis_x)}" y1="{axis_y}" x2="{fmt(width - 7.5)}" y2="{axis_y}" />')
    for y, value in y_ticks:
        lines.append(f'      <line class="axis-tick" x1="{fmt(axis_x)}" y1="{fmt(y)}" x2="{fmt(width - 7.5)}" y2="{fmt(y)}" />')
        lines.append(
            f'      <text class="axis-label" x="15.8" y="{fmt(y + 1.2)}" text-anchor="end" '
            f'font-size="{axis_font_size}">{format_ap(value)}</text>'
        )

    lines.append(
        '      <path d="' + " ".join(path_cmds)
        + '" fill="none" stroke="url(#accent-grad)" stroke-width="1.8" '
        + 'stroke-linecap="round" stroke-linejoin="round" opacity="0.95" clip-path="url(#clip-chart)"/>'
    )

    for i, (x, y) in enumerate(coords):
        cls = "trend-point-end" if i == count - 1 else "trend-point"
        radius = "2.2" if i in (0, count - 1) else "2"
        lines.append(f'      <circle cx="{fmt(x)}" cy="{fmt(y)}" r="{radius}" class="{cls}"/>')

    for (x, _y), (ts, _value) in zip(coords, points):
        date_label = format_date(ts)
        time_label = datetime.fromtimestamp(ts, tz=CHART_TIMEZONE).strftime("%H:%M")
        if day_counts[date_label] > 1:
            lines.append(
                f'      <text class="axis-label" x="{fmt(x)}" y="131" text-anchor="middle">'
                f'<tspan x="{fmt(x)}" dy="0" font-size="{date_font_size}">{date_label}</tspan>'
                f'<tspan x="{fmt(x)}" dy="3.8" font-size="{date_font_size}">{time_label}</tspan>'
                f'</text>'
            )
        else:
            lines.append(
                f'      <text class="axis-label" x="{fmt(x)}" y="133" text-anchor="middle" '
                f'font-size="{date_font_size}">{date_label}</text>'
            )

    return "\n".join(lines)


def build_stats_panel(stats, panel_width=112):
    lines = []
    lines.append('      <g transform="translate(6, 97)">')
    lines.append(f'        <rect width="{panel_width}" height="74" rx="1.2" fill="#c6bccb" />')
    lines.append(f'        <rect width="{panel_width}" height="10" rx="1.2" fill="#24265d" />')
    lines.append('        <text class="font-base" x="4" y="6.8" fill="#f0f6fd" font-size="4px" font-weight="900">DESCRIPTION</text>')

    row_y = 16.8
    row_step = 8
    value_x = panel_width - 4
    for i, (label, key) in enumerate(STATS_FIELDS):
        y = row_y + i * row_step
        lines.append(
            f'        <text class="panel-label" x="4" y="{y}" font-size="5.1px">{label}:</text>'
        )
        lines.append(
            f'        <text class="panel-value" x="{value_x}" y="{y}" text-anchor="end" font-size="5.1px">'
            f'{format_int(stats.get(key, 0))}</text>'
        )

    lines.append('      </g>')
    return "\n".join(lines)


def render_svg(svg_path: Path, chart_markup: str):
    svg = svg_path.read_text(encoding="utf-8")
    chart_pattern = re.compile(r"(?s)(<!-- AP_CHART_START -->).*?(<!-- AP_CHART_END -->)")
    panel_pattern = re.compile(r"(?s)(<!-- STATS_PANEL_START -->).*?(<!-- STATS_PANEL_END -->)")
    if not chart_pattern.search(svg):
        raise ValueError("AP chart markers not found in SVG")
    if not panel_pattern.search(svg):
        raise ValueError("Stats panel markers not found in SVG")
    stats_markup = build_stats_panel(load_stats_difference(STATS_PATH))
    svg = chart_pattern.sub(lambda m: f"{m.group(1)}\n{chart_markup}\n      {m.group(2)}", svg, count=1)
    svg = panel_pattern.sub(lambda m: f"{m.group(1)}\n{stats_markup}\n    {m.group(2)}", svg, count=1)
    svg_path.write_text(svg, encoding="utf-8", newline="\n")


def main():
    try:
        points = load_points(DATA_PATH)
        chart_markup = build_chart(points)
        render_svg(SVG_PATH, chart_markup)
        print(f"Updated SVG chart with {len(points)} points and stats panel")
        return 0
    except Exception as exc:
        print(f"render_ap_chart.py failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
