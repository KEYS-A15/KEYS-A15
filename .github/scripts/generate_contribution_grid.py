#!/usr/bin/env python3
"""Generate a wide animated SVG from a GitHub contribution calendar."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import date, datetime
from zoneinfo import ZoneInfo
from html import escape
from pathlib import Path

API_URL = "https://api.github.com/graphql"

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

    body = json.dumps(
        {
            "query": query,
            "variables": {"login": username},
        }
    ).encode()

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

    # The scan begins here and takes this long to cross the calendar.
    scan_start = 0.35
    scan_duration = 3.15

    scan_end_x = grid_x + max(len(weeks) - 1, 0) * step + cell
    scan_distance = max(scan_end_x - grid_x, 1)
    scan_finish = scan_start + scan_duration

    all_days = sorted(
        (
            day
            for week in weeks
            for day in week["contributionDays"]
        ),
        key=lambda day: day["date"],
    )

    counts = [
        int(day["contributionCount"])
        for day in all_days
    ]

    last_7 = sum(counts[-7:])
    previous_7 = sum(counts[-14:-7])
    last_30 = sum(counts[-30:])

    # Current streak. A contribution-free current day does not
    # immediately terminate yesterday's completed streak.
    current_streak = 0
    streak_counts = counts

    if all_days:
        latest_day = date.fromisoformat(all_days[-1]["date"])
        phoenix_today = datetime.now(
            ZoneInfo("America/Phoenix")
        ).date()

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
            longest_streak = max(
                longest_streak,
                running_streak,
            )
        else:
            running_streak = 0

    # Compare this seven-day period with the preceding seven days.
    if previous_7 == 0:
        signal = "NEW" if last_7 else "FLAT"
    else:
        signal_change = round(
            ((last_7 - previous_7) / previous_7) * 100
        )

        if signal_change > 0:
            signal = f"UP {signal_change}%"
        elif signal_change < 0:
            signal = f"DOWN {abs(signal_change)}%"
        else:
            signal = "FLAT"

    sync_date = datetime.now(
        ZoneInfo("America/Phoenix")
    ).strftime("%Y-%m-%d")

    telemetry = (
        f"365D {total}  //  "
        f"30D {last_30}  //  "
        f"7D {last_7}  //  "
        f"STREAK {current_streak}D  //  "
        f"MAX {longest_streak}D  //  "
        f"SIGNAL {signal}  //  "
        f"SYNC {sync_date}"
    )

    current_week_x = (
        grid_x
        + max(len(weeks) - 1, 0) * step
    )

    cells: list[str] = []
    labels: list[str] = []

    previous_month: int | None = None

    for week_index, week in enumerate(weeks):
        days = week["contributionDays"]

        if days:
            first = date.fromisoformat(days[0]["date"])

            if first.month != previous_month:
                labels.append(
                    f'<text x="{grid_x + week_index * step}" '
                    f'y="42" class="month">'
                    f"{MONTHS[first.month - 1]}"
                    "</text>"
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

            # Synchronize each cell with the exact position of the scan front.
            reveal_time = (
                scan_start
                + ((x - grid_x) / scan_distance) * scan_duration
            )

            cells.append(
                f'<rect x="{x}" y="{y}" '
                f'width="{cell}" height="{cell}" '
                f'rx="1" fill="{color}" class="cell">'
                f"<title>"
                f'{escape(day["date"])}: {count} {day_label}'
                f"</title>"
                f'<animate attributeName="opacity" '
                f'values="0.16;1;1" '
                f'keyTimes="0;0.38;1" '
                f'begin="{reveal_time:.3f}s" '
                f'dur="0.18s" '
                f'fill="freeze"/>'
                f'<animate attributeName="fill" '
                f'values="#07130d;#b6ffd0;{color}" '
                f'keyTimes="0;0.38;1" '
                f'begin="{reveal_time:.3f}s" '
                f'dur="0.22s" '
                f'fill="freeze"/>'
                "</rect>"
            )

    legend_x = width - 190

    legend = [
        (
            f'<text x="{legend_x - 36}" y="174" '
            f'class="legend-label">less</text>'
        ),
        *[
            (
                f'<rect x="{legend_x + index * 16}" '
                f'y="164" width="11" height="11" '
                f'rx="1" fill="{color}"/>'
            )
            for index, color in enumerate(PALETTE.values())
        ],
        (
            f'<text x="{legend_x + 86}" y="174" '
            f'class="legend-label">more</text>'
        ),
    ]

    calendar_panel_width = scan_end_x - 62 + 8

    return f'''<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{width}"
  height="{height}"
  viewBox="0 0 {width} {height}"
  role="img"
  aria-labelledby="title desc"
>
  <title id="title">{escape(username)} GitHub contributions</title>

  <desc id="desc">
    {total} contributions during the last year,
    revealed from left to right
  </desc>

  <defs>
    <linearGradient
      id="phosphorTrail"
      x1="0"
      y1="0"
      x2="1"
      y2="0"
    >
      <stop
        offset="0"
        stop-color="#39ff88"
        stop-opacity="0"
      />

      <stop
        offset="0.72"
        stop-color="#39ff88"
        stop-opacity="0.05"
      />

      <stop
        offset="1"
        stop-color="#9dffbd"
        stop-opacity="0.20"
      />
    </linearGradient>

    <pattern
      id="crtLines"
      width="1"
      height="4"
      patternUnits="userSpaceOnUse"
    >
      <rect
        width="1"
        height="1"
        fill="#39ff88"
        opacity="0.035"
      />
    </pattern>

    <filter
      id="pixelGlow"
      x="-80%"
      y="-20%"
      width="260%"
      height="140%"
    >
      <feGaussianBlur
        stdDeviation="1.8"
        result="blur"
      />

      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <style>
      text {{
        font-family:
          ui-monospace,
          SFMono-Regular,
          Menlo,
          Consolas,
          monospace;
      }}

      .title {{
        fill: #b7ffd0;
        font-size: 14px;
        font-weight: 600;
      }}

      .status {{
        fill: #39ff88;
        font-size: 10px;
        letter-spacing: 1.4px;
      }}

      .month,
      .day,
      .legend-label {{
        fill: #3f8058;
        font-size: 10px;
      }}

      .cell {{
        opacity: 0.16;
      }}
      
      .telemetry {{
        fill: #56b978;
        font-size: 8px;
        letter-spacing: 0.35px;
      }}

      .boot {{
        fill: #39ff88;
        font-size: 10px;
        letter-spacing: 1.2px;
      }}
    </style>
  </defs>

  <!-- Green-black terminal background -->
  <rect
    width="960"
    height="180"
    rx="10"
    fill="#020906"
  />

  <!-- Terminal border -->
  <rect
    x="0.5"
    y="0.5"
    width="959"
    height="179"
    rx="9.5"
    fill="none"
    stroke="#174d2e"
  />

  <!-- Retro terminal corner markers -->
  <path
    d="
      M1 18V1h17
      M942 1h17v17
      M1 162v17h17
      M942 179h17v-17
    "
    fill="none"
    stroke="#2ca85a"
    opacity="0.45"
  />

  <text
    x="20"
    y="25"
    class="title"
  >
    {total} contributions · last 12 months
  </text>

  <g text-anchor="end" class="boot">
    <text
      x="940"
      y="25"
      opacity="1"
    >
      INITIALIZING...

      <animate
        attributeName="opacity"
        values="1;1;0"
        keyTimes="0;.82;1"
        begin="0s"
        dur=".7s"
        fill="freeze"
      />
    </text>

    <text
      x="940"
      y="25"
      opacity="0"
    >
      INDEXING 365 DAYS...

      <animate
        attributeName="opacity"
        values="0;1;1;0"
        keyTimes="0;.08;.9;1"
        begin=".58s"
        dur="{scan_finish - .58:.2f}s"
        fill="freeze"
      />
    </text>

    <text
      x="940"
      y="25"
      opacity="0"
    >
      ● CALENDAR ONLINE

      <animate
        attributeName="opacity"
        from="0"
        to="1"
        begin="{scan_finish:.2f}s"
        dur=".18s"
        fill="freeze"
      />
    </text>

    <rect
      x="944"
      y="17"
      width="5"
      height="9"
      fill="#39ff88"
      opacity="0"
    >
      <animate
        attributeName="opacity"
        values="0;1;0"
        begin="{scan_finish + .2:.2f}s"
        dur="1s"
        repeatCount="indefinite"
      />
    </rect>
  </g>

  {''.join(labels)}

  <text x="42" y="80" class="day">Mon</text>
  <text x="42" y="112" class="day">Wed</text>
  <text x="42" y="144" class="day">Fri</text>

  <!-- Dark-green contribution-grid panel -->
  <rect
    x="62"
    y="47"
    width="{calendar_panel_width}"
    height="116"
    rx="3"
    fill="#04120b"
    stroke="#123d26"
    opacity="0.72"
  />

  <!-- Contribution cells -->
  <g>
    {''.join(cells)}
  </g>
  
  <rect
    x="{current_week_x - 3}"
    y="51"
    width="{cell + 6}"
    height="111"
    rx="2"
    fill="none"
    stroke="#70ff9b"
    stroke-width="1"
    opacity="0"
  >
    <animate
      attributeName="opacity"
      values=".22;.9;.22"
      begin="{scan_finish:.2f}s"
      dur="2.4s"
      repeatCount="indefinite"
    />
  </rect>

  <!-- Jagged pixel scan front -->
  <g opacity="0">
    <!-- Narrow trailing phosphor -->
    <rect
      x="-28"
      y="48"
      width="28"
      height="114"
      fill="url(#phosphorTrail)"
    />

    <!-- Distorted vertical line of terminal pixels -->
    <g
      filter="url(#pixelGlow)"
      fill="#39ff88"
    >
      <rect x="-2" y="49" width="2" height="3"/>
      <rect x="2" y="53" width="3" height="2"/>

      <rect x="0" y="57" width="2" height="4"/>
      <rect x="-4" y="63" width="3" height="2"/>

      <rect x="1" y="68" width="2" height="3"/>
      <rect x="4" y="73" width="2" height="2"/>

      <rect x="-1" y="77" width="3" height="4"/>
      <rect x="2" y="84" width="2" height="3"/>

      <rect x="-5" y="89" width="4" height="2"/>
      <rect x="0" y="94" width="2" height="4"/>

      <rect x="3" y="100" width="3" height="2"/>
      <rect x="-2" y="105" width="2" height="3"/>

      <rect x="1" y="110" width="3" height="4"/>
      <rect x="-4" y="116" width="3" height="2"/>

      <rect x="3" y="121" width="2" height="3"/>
      <rect x="-1" y="126" width="3" height="2"/>

      <rect x="1" y="131" width="2" height="4"/>
      <rect x="5" y="137" width="2" height="2"/>

      <rect x="-3" y="142" width="4" height="3"/>
      <rect x="1" y="148" width="3" height="2"/>

      <rect x="-1" y="153" width="2" height="4"/>
      <rect x="3" y="159" width="2" height="2"/>
    </g>

    <animate
      attributeName="opacity"
      values="0;1;1;0"
      keyTimes="0;.04;.94;1"
      begin="{scan_start}s"
      dur="{scan_duration}s"
      fill="freeze"
    />

    <animateTransform
      attributeName="transform"
      type="translate"
      from="{grid_x} 0"
      to="{scan_end_x} 0"
      begin="{scan_start}s"
      dur="{scan_duration}s"
      fill="freeze"
    />
  </g>

  <!-- CRT horizontal scanlines -->
  <rect
    width="960"
    height="180"
    rx="10"
    fill="url(#crtLines)"
    pointer-events="none"
  />

  <text
    x="20"
    y="174"
    class="telemetry"
  >
    {escape(telemetry)}
  </text>

  {''.join(legend)}
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--username",
        default="KEYS-A15",
    )

    parser.add_argument(
        "--output",
        default="assets/contribution-grid.svg",
    )

    parser.add_argument(
        "--input",
        help="Optional saved GraphQL calendar JSON",
    )

    args = parser.parse_args()

    if args.input:
        calendar = json.loads(
            Path(args.input).read_text(encoding="utf-8")
        )
    else:
        token = os.environ.get("METRICS_TOKEN")

        if not token:
            raise SystemExit("METRICS_TOKEN is required")

        calendar = fetch_calendar(
            args.username,
            token,
        )

    output = Path(args.output)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        render_svg(calendar, args.username),
        encoding="utf-8",
    )

    print(
        f"Generated {output} with "
        f"{calendar['totalContributions']} contributions"
    )


if __name__ == "__main__":
    main()
