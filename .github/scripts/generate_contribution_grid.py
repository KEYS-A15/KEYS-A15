#!/usr/bin/env python3
"""Generate a wide animated SVG from a GitHub contribution calendar."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import date
from html import escape
from pathlib import Path

API_URL = "https://api.github.com/graphql"
PALETTE = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353",
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
            delay = week_index * 0.045
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                f'rx="2" fill="{color}" class="cell" '
                f'style="animation-delay:{delay:.3f}s">'
                f'<title>{escape(day["date"])}: {count} {day_label}</title>'
                "</rect>"
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
  <title id="title">{escape(username)} GitHub contributions</title>
  <desc id="desc">{total} contributions during the last year, revealed from left to right</desc>
  <defs>
    <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#39d353" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#7ee787" stop-opacity="0.22"/>
      <stop offset="1" stop-color="#39d353" stop-opacity="0"/>
    </linearGradient>
    <style>
      text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
      .title {{ fill:#e6edf3; font-size:14px; font-weight:600; }}
      .status {{ fill:#39d353; font-size:10px; letter-spacing:1.4px; }}
      .month,.day,.legend-label {{ fill:#7d8590; font-size:10px; }}
      .cell {{
        transform-box:fill-box;
        transform-origin:center;
        animation:cell-in .32s cubic-bezier(.2,.8,.2,1) both;
      }}
      .sweep {{ animation:sweep-across 3s ease-out both; }}
      @keyframes cell-in {{
        from {{ opacity:.08; transform:scale(.45); }}
        to {{ opacity:1; transform:scale(1); }}
      }}
      @keyframes sweep-across {{
        0% {{ opacity:0; transform:translateX(-160px); }}
        8% {{ opacity:1; }}
        88% {{ opacity:.7; }}
        100% {{ opacity:0; transform:translateX(960px); }}
      }}
    </style>
  </defs>
  <rect width="960" height="180" rx="10" fill="#0d1117"/>
  <rect x="0.5" y="0.5" width="959" height="179" rx="9.5" fill="none" stroke="#30363d"/>
  <text x="20" y="25" class="title">{total} contributions · last 12 months</text>
  <text x="940" y="25" text-anchor="end" class="status">● LIVE CALENDAR</text>
  {''.join(labels)}
  <text x="42" y="80" class="day">Mon</text>
  <text x="42" y="112" class="day">Wed</text>
  <text x="42" y="144" class="day">Fri</text>
  <g>{''.join(cells)}</g>
  <rect x="-160" y="47" width="150" height="114" fill="url(#sweep)" class="sweep"/>
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
