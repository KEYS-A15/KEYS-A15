#!/usr/bin/env python3
"""Generate a wide animated SVG from a GitHub contribution calendar."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import date, datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

API_URL = "https://api.github.com/graphql"
REVEAL_VERSION = "pixel-cascade-v6"
REVEAL_START = 0.18
COL_DELAY = 0.023
ROW_DELAY = 0.050
CELL_DURATION = 0.44
PALETTE = {
    "NONE": "#07130d",
    "FIRST_QUARTILE": "#0d3b22",
    "SECOND_QUARTILE": "#126b35",
    "THIRD_QUARTILE": "#18a64b",
    "FOURTH_QUARTILE": "#39ff88",
}
MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def fetch_calendar(username: str, token: str) -> dict:
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                contributionLevel
                date
                weekday
              }
            }
          }
        }
      }
    }
    """
    body = json.dumps({"query": query, "variables": {"login": username}}).encode()
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "KEYS-A15-profile-grid",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    user = payload.get("data", {}).get("user")
    if user is None:
        raise RuntimeError(f"GitHub user {username!r} was not found")
    return user["contributionsCollection"]["contributionCalendar"]


def render_svg(calendar: dict, username: str) -> str:
    width = 960
    height = 180
    grid_x = 72
    grid_y = 55
    step = 16
    cell = 11
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    scan_end_x = grid_x + max(len(weeks) - 1, 0) * step + cell
    pixel_sweep_duration = max(max(len(weeks) - 1, 0) * COL_DELAY, 0.01)
    last_cell_delay = (
        REVEAL_START
        + max(len(weeks) - 1, 0) * COL_DELAY
        + 6 * ROW_DELAY
    )
    reveal_finish = last_cell_delay + CELL_DURATION
    settle_finish = reveal_finish + 0.12

    all_days = sorted(
        (
            day
            for week in weeks
            for day in week["contributionDays"]
        ),
        key=lambda day: day["date"],
    )
    counts = [int(day["contributionCount"]) for day in all_days]
    last_7 = sum(counts[-7:])
    previous_7 = sum(counts[-14:-7])
    last_30 = sum(counts[-30:])

    current_streak = 0
    streak_counts = counts
    if all_days:
        latest_day = date.fromisoformat(all_days[-1]["date"])
        phoenix_today = datetime.now(ZoneInfo("America/Phoenix")).date()
        if latest_day == phoenix_today and counts[-1] == 0:
            streak_counts = counts[:-1]
    for count in reversed(streak_counts):
        if count == 0:
            break
        current_streak += 1

    longest_streak = 0
    running_streak = 0
    for count in counts:
        if count > 0:
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        else:
            running_streak = 0

    if previous_7 == 0:
        signal = "NEW" if last_7 else "FLAT"
    else:
        signal_change = round(((last_7 - previous_7) / previous_7) * 100)
        if signal_change > 0:
            signal = f"UP {signal_change}%"
        elif signal_change < 0:
            signal = f"DOWN {abs(signal_change)}%"
        else:
            signal = "FLAT"

    sync_date = datetime.now(ZoneInfo("America/Phoenix")).strftime("%Y-%m-%d")
    telemetry = (
        f"365D {total}  //  30D {last_30}  //  7D {last_7}  //  "
        f"STREAK {current_streak}D  //  MAX {longest_streak}D  //  "
        f"SIGNAL {signal}  //  SYNC {sync_date}"
    )
    current_week_x = grid_x + max(len(weeks) - 1, 0) * step

    cells: list[str] = []
    labels: list[str] = []
    previous_month: int | None = None

    for week_index, week in enumerate(weeks):
        days = week["contributionDays"]
        if days:
            first = date.fromisoformat(days[0]["date"])
            if first.month != previous_month:
                labels.append(
                    f'<text x="{grid_x + week_index * step}" y="42" '
                    f'class="month">{MONTHS[first.month - 1]}</text>'
                )
                previous_month = first.month

        for day in days:
            weekday = int(day["weekday"])
            x = grid_x + week_index * step
            y = grid_y + weekday * step
            level = day["contributionLevel"]
            color = PALETTE.get(level, PALETTE["NONE"])
            count = int(day["contributionCount"])
            day_label = "contribution" if count == 1 else "contributions"
            delay = REVEAL_START + week_index * COL_DELAY + weekday * ROW_DELAY
            cells.append(
                f'<rect class="contribution-cell" x="{x}" y="{y}" '
                f'width="{cell}" height="{cell}" rx="1" fill="{color}" '
                f'style="animation-delay:{delay:.3f}s">'
                f'<title>{escape(day["date"])}: {count} {day_label}</title>'
                f'<animate attributeName="fill" '
                f'values="#effff4;#8dffb1;{color}" keyTimes="0;0.18;1" '
                f'begin="{delay:.3f}s" dur="0.22s" fill="freeze"/>'
                "</rect>"
            )

    # The seven staggered heads and tapered wakes are adapted from the
    # original pixel-front design. Each row now moves on the same timing as
    # its cell cascade, so the pixels appear to trigger the reveal rather
    # than forming an unrelated overlay.
    head_offsets = (0, 4, 8, 3, 9, 5, 1)
    wake_opacities = (0.96, 0.34, 0.15, 0.06)
    scan_rows: list[str] = []
    for row, head_offset in enumerate(head_offsets):
        y = grid_y + row * step
        row_start = REVEAL_START + row * ROW_DELAY
        wake = "".join(
            f'<rect x="{head_offset - depth * 8}" y="{y}" '
            f'width="{5 if depth == 0 else 6}" height="{cell}" rx="1" '
            f'fill="{"#e9fff0" if depth == 0 else "#39ff88"}" '
            f'opacity="{opacity}"/>'
            for depth, opacity in enumerate(wake_opacities)
        )
        fragments = "".join(
            (
                f'<rect x="{head_offset + dx}" y="{y + dy}" width="{size}" '
                f'height="{size}" rx=".5" fill="#39ff88" opacity="{opacity}"/>'
            )
            for dx, dy, size, opacity in (
                (-18, 2, 3, 0.20),
                (-28, 7, 2, 0.12),
                (-13, -3, 2, 0.17),
            )
        )
        # Offset the group's travel by the head's local x position. This
        # keeps the bright pixel aligned with each contribution column even
        # though the seven rows use different head shapes.
        sweep_start_x = grid_x - head_offset
        sweep_end_x = grid_x + max(len(weeks) - 1, 0) * step - head_offset
        scan_rows.append(
            f'<g opacity="0">'
            f'<g filter="url(#pixelGlow)">{wake}</g>{fragments}'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;.025;.94;1" begin="{row_start:.3f}s" '
            f'dur="{pixel_sweep_duration:.3f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="{sweep_start_x} 0" to="{sweep_end_x} 0" '
            f'begin="{row_start:.3f}s" dur="{pixel_sweep_duration:.3f}s" '
            f'fill="freeze"/>'
            f'</g>'
        )

    legend_x = width - 190
    legend = [
        f'<text x="{legend_x - 36}" y="174" class="legend-label">less</text>',
        *[
            f'<rect x="{legend_x + index * 16}" y="164" width="11" height="11" '
            f'rx="2" fill="{color}"/>'
            for index, color in enumerate(PALETTE.values())
        ],
        f'<text x="{legend_x + 86}" y="174" class="legend-label">more</text>',
    ]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <!-- reveal-version: {REVEAL_VERSION} -->
  <title id="title">{escape(username)} GitHub contributions</title>
  <desc id="desc">{total} contributions during the last year, revealed from left to right</desc>
  <defs>
    <pattern id="crtLines" width="1" height="4" patternUnits="userSpaceOnUse">
      <rect width="1" height="1" fill="#39ff88" opacity="0.022"/>
    </pattern>
    <filter id="pixelGlow" x="-100%" y="-30%" width="300%" height="160%">
      <feGaussianBlur stdDeviation="1.15" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      @keyframes contribution-reveal {{
        0% {{ opacity:0; transform:translateY(-6px); }}
        4% {{ opacity:1; transform:translateY(-3px); }}
        100% {{ opacity:1; transform:translateY(0); }}
      }}
      text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
      .contribution-cell {{
        opacity:0;
        animation:contribution-reveal {CELL_DURATION:.2f}s cubic-bezier(.2,.8,.2,1) both;
      }}
      .title {{ fill:#b7ffd0; font-size:14px; font-weight:600; }}
      .status {{ fill:#39ff88; font-size:10px; letter-spacing:1.4px; }}
      .month,.day,.legend-label {{ fill:#3f8058; font-size:10px; }}
      .telemetry {{ fill:#56b978; font-size:8px; letter-spacing:.35px; }}
      .boot {{ fill:#39ff88; font-size:10px; letter-spacing:1.2px; }}
    </style>
  </defs>
  <rect width="960" height="180" rx="10" fill="#020906"/>
  <rect x="0.5" y="0.5" width="959" height="179" rx="9.5" fill="none" stroke="#174d2e"/>
  <path d="M1 18V1h17 M942 1h17v17 M1 162v17h17 M942 179h17v-17" fill="none" stroke="#2ca85a" opacity=".45"/>
  <text x="20" y="25" class="title">{total} contributions · last 12 months</text>
  <g text-anchor="end" class="boot">
    <text x="940" y="25" opacity="0">RECONSTRUCTING GIT HISTORY...
      <animate attributeName="opacity" values="1;1;0" keyTimes="0;.94;1" begin="0s" dur="{reveal_finish:.2f}s" fill="freeze"/>
    </text>
    <text x="940" y="25" opacity="1">● 365D CHECKSUM VERIFIED
      <set attributeName="opacity" to="0" begin="0s" dur="{settle_finish:.2f}s"/>
      <animate attributeName="opacity" from="0" to="1" begin="{settle_finish:.2f}s" dur=".16s" fill="freeze"/>
    </text>
  </g>
  {''.join(labels)}
  <text x="42" y="80" class="day">Mon</text>
  <text x="42" y="112" class="day">Wed</text>
  <text x="42" y="144" class="day">Fri</text>
  <rect x="62" y="47" width="{scan_end_x - 62 + 8}" height="116" rx="3" fill="#04120b" stroke="#123d26" opacity=".72"/>
  <g>{''.join(cells)}</g>
  <g>{''.join(scan_rows)}</g>
  <rect x="{current_week_x - 3}" y="51" width="{cell + 6}" height="111" rx="2" fill="none" stroke="#70ff9b" stroke-width="1" opacity=".42">
    <set attributeName="opacity" to="0" begin="0s" dur="{settle_finish:.2f}s"/>
    <animate attributeName="opacity" from="0" to=".42" begin="{settle_finish:.2f}s" dur=".16s" fill="freeze"/>
  </rect>
  <rect width="960" height="180" rx="10" fill="url(#crtLines)" pointer-events="none"/>
  <text x="20" y="174" class="telemetry">{escape(telemetry)}</text>
  {''.join(legend)}
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="KEYS-A15")
    parser.add_argument("--output", default="assets/contribution-grid.svg")
    parser.add_argument("--input", help="Optional saved GraphQL calendar JSON")
    args = parser.parse_args()

    if args.input:
        calendar = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        token = os.environ.get("METRICS_TOKEN")
        if not token:
            raise SystemExit("METRICS_TOKEN is required")
        calendar = fetch_calendar(args.username, token)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_svg(calendar, args.username), encoding="utf-8")
    print(f"Generated {output} with {calendar['totalContributions']} contributions")


if __name__ == "__main__":
    main()
