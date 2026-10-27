#!/usr/bin/env python3
"""
Time zone scanner and adjuster.

1. Scans countries-time-zones.md and extracts every UTC offset for every country.
2. You type a time. That time becomes the reference clock, and EVERY time zone of
   EVERY country is adjusted to follow it.

The typed time is read as the clock time in a reference place (default: Uganda,
UTC+3). Use --from to name another country, or --offset for a raw UTC offset.

Usage:
    python timezone_converter.py                          # interactive, repeats until you quit
    python timezone_converter.py 20:00                    # 20:00 in Uganda; all zones follow
    python timezone_converter.py 09:00 --from Japan       # 09:00 in Japan
    python timezone_converter.py 14:30 --offset -5        # 14:30 in UTC-5
    python timezone_converter.py 20:00 --live             # clock keeps ticking from 20:00
    python timezone_converter.py 20:00 --country Brazil Japan --output result.md
"""

import argparse
import re
import sys
import time as time_module
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_FILE = "countries-time-zones.md"
DEFAULT_REFERENCE_COUNTRY = "Uganda"

# Matches "UTC+5:30", "UTC−3" (the file uses the Unicode minus sign), "UTC+0"
OFFSET_RE = re.compile(r"UTC\s*([+\-−])\s*(\d{1,2})(?::(\d{2}))?")

# The file only gives end points for some multi-zone countries, and hourly
# expansion is wrong for these, so their real standard offsets are set here.
OVERRIDES = {
    "Canada": ["-8", "-7", "-6", "-5", "-4", "-3:30"],
    "Australia": ["+8", "+9:30", "+10"],
    "United States": ["-10", "-9", "-8", "-7", "-6", "-5"],
    "Mexico": ["-8", "-7", "-6"],
    "Morocco": ["+1"],  # the Ramadan UTC+0 shift is seasonal, not a separate zone
}


# ---------------------------------------------------------------------------
# Offset helpers
# ---------------------------------------------------------------------------

def offset_to_minutes(sign: str, hours: str, minutes: str | None) -> int:
    total = int(hours) * 60 + int(minutes or 0)
    return -total if sign in ("-", "−") else total


def parse_offset_text(text: str) -> int:
    """Parse '+3', '-3:30', 'UTC+5:45' or '0' into minutes from UTC."""
    cleaned = text.strip().upper().replace("UTC", "").replace("−", "-").replace(" ", "")
    match = re.fullmatch(r"([+\-]?)(\d{1,2})(?::(\d{2}))?", cleaned)
    if not match:
        raise ValueError(f"Cannot read '{text}' as a UTC offset. Try +3, -5, +5:30.")
    sign, hours, minutes = match.groups()
    value = offset_to_minutes(sign or "+", hours, minutes)
    if not -12 * 60 <= value <= 14 * 60:
        raise ValueError("UTC offsets must be between -12:00 and +14:00.")
    return value


def format_offset(minutes: int) -> str:
    sign = "-" if minutes < 0 else "+"
    hours, mins = divmod(abs(minutes), 60)
    return f"UTC{sign}{hours}" + (f":{mins:02d}" if mins else "")


def extract_offsets(country: str, zone_text: str) -> list[int]:
    """Return every distinct UTC offset (in minutes) mentioned for one country."""
    if country in OVERRIDES:
        return sorted(parse_offset_text(o) for o in OVERRIDES[country])

    found = [offset_to_minutes(*m.groups()) for m in OFFSET_RE.finditer(zone_text)]

    # "UTC+2 to UTC+12" style ranges: fill in the whole-hour zones between.
    if re.search(r"\bto\b", zone_text) and len(found) >= 2:
        step, high = min(found), max(found)
        while step <= high:
            found.append(step)
            step += 60

    return sorted(set(found))


# ---------------------------------------------------------------------------
# Step 1: scan the document
# ---------------------------------------------------------------------------

def scan_time_zones(path: str = DEFAULT_FILE) -> dict[str, dict]:
    """Return { country: {"region": str, "zones": [minutes, ...], "raw": text} }."""
    file = Path(path)
    if not file.exists():
        sys.exit(f"File not found: {path}")

    countries: dict[str, dict] = {}
    region = "Unknown"

    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if line.startswith("## "):
            region = re.sub(r"\s*\(\d+\)\s*$", "", line[3:]).strip()
            continue
        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        country, zone_text = cells
        if country.lower() == "country" or set(country) <= {"-", " "}:
            continue  # header or divider row

        zones = extract_offsets(country, zone_text)
        if zones:
            countries[country] = {"region": region, "zones": zones, "raw": zone_text}

    return countries


def find_country(countries: dict[str, dict], name: str) -> str:
    """Case-insensitive lookup; also accepts a unique partial name."""
    lowered = name.strip().lower()
    for country in countries:
        if country.lower() == lowered:
            return country
    partial = [c for c in countries if lowered in c.lower()]
    if len(partial) == 1:
        return partial[0]
    if partial:
        raise ValueError(f"'{name}' matches several countries: {', '.join(partial)}")
    raise ValueError(f"'{name}' is not in the file.")


def reference_offset_for(countries: dict[str, dict], name: str) -> int:
    """UTC offset of a single-zone country, used as the reference for the typed time."""
    country = find_country(countries, name)
    zones = countries[country]["zones"]
    if len(zones) != 1:
        raise ValueError(
            f"{country} has {len(zones)} time zones. Use --offset to say which one your time is in."
        )
    return zones[0]


# ---------------------------------------------------------------------------
# Step 2: adjust every time zone to follow the typed time
# ---------------------------------------------------------------------------

def parse_user_time(text: str) -> datetime:
    """Accept 14:30, 2:30pm, 2:30 PM, 1430, or a full 'YYYY-MM-DD HH:MM'."""
    text = text.strip()
    formats = (
        "%H:%M:%S", "%H:%M", "%I:%M%p", "%I:%M %p", "%I%p", "%I %p", "%H%M",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p",
    )
    for fmt in formats:
        try:
            parsed = datetime.strptime(text.upper(), fmt)
        except ValueError:
            continue
        if "%Y" not in fmt:  # no date typed: use today's date
            today = datetime.now()
            parsed = parsed.replace(year=today.year, month=today.month, day=today.day)
        return parsed
    raise ValueError(f"Cannot read '{text}' as a time. Try 20:00, 8:00 PM or 2026-10-27 20:00.")


def adjust_all_timezones(
    countries: dict[str, dict],
    user_time: datetime,
    reference_offset: int,
    only: list[str] | None = None,
) -> dict[str, list[dict]]:
    """
    Make every time zone follow the time the user typed.

    user_time         the clock time typed (a naive datetime)
    reference_offset  UTC offset (minutes) that clock time is in

    The typed time pins down one real moment. Every zone is then set to the clock
    reading that belongs to that same moment, so all zones agree with the input.

    Returns { country: [ {"offset": "UTC+3", "minutes": 180,
                          "local_time": datetime, "day_shift": int}, ... ] }
    """
    utc_moment = user_time - timedelta(minutes=reference_offset)
    wanted = {name.lower() for name in only} if only else None

    results: dict[str, list[dict]] = {}
    for country, info in countries.items():
        if wanted and country.lower() not in wanted:
            continue
        results[country] = [
            {
                "offset": format_offset(minutes),
                "minutes": minutes,
                "local_time": (local := utc_moment + timedelta(minutes=minutes)),
                "day_shift": (local.date() - user_time.date()).days,
            }
            for minutes in info["zones"]
        ]
    return results


# Kept so older code that imported the first version still works.
generate_new_timezones = adjust_all_timezones


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def describe_row(row: dict, with_seconds: bool = False) -> str:
    shift = row["day_shift"]
    note = {0: "", 1: " (next day)", -1: " (previous day)"}.get(shift, f" ({shift:+d} days)")
    clock = row["local_time"].strftime("%H:%M:%S" if with_seconds else "%H:%M")
    return f"{clock} on {row['local_time'].strftime('%a %d %b')}{note}"


def print_results(results: dict[str, list[dict]], with_seconds: bool = False) -> None:
    width = max((len(c) for c in results), default=10)
    for country, rows in results.items():
        summary = "; ".join(f"{r['offset']} -> {describe_row(r, with_seconds)}" for r in rows)
        print(f"{country:<{width}}  {summary}")


def save_markdown(results, countries, user_time, reference_label, path) -> None:
    lines = [
        "# Local Times Across Countries",
        "",
        f"Input: **{user_time.strftime('%Y-%m-%d %H:%M')}** in **{reference_label}**. "
        "Every zone below follows that time.",
        "",
        "| Region | Country | Time zone | Local time |",
        "|---|---|---|---|",
    ]
    for country, rows in results.items():
        for row in rows:
            lines.append(
                f"| {countries[country]['region']} | {country} | {row['offset']} | {describe_row(row)} |"
            )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved to {path}")


def run_live(countries, user_time, reference_offset, only, ticks=None) -> None:
    """
    Simulated clock: starts at the typed time and keeps ticking once a second,
    with every time zone of every country following it. Press Ctrl+C to stop.
    """
    started = time_module.monotonic()
    shown = 0
    try:
        while ticks is None or shown < ticks:
            elapsed = timedelta(seconds=int(time_module.monotonic() - started))
            current = user_time + elapsed
            results = adjust_all_timezones(countries, current, reference_offset, only)
            if sys.stdout.isatty():
                print("\033[2J\033[H", end="")  # clear screen, cursor to top
            print(f"Live clock from {user_time.strftime('%H:%M:%S')}  (Ctrl+C to stop)\n")
            print_results(results, with_seconds=True)
            shown += 1
            time_module.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def resolve_reference(countries, args) -> tuple[int, str]:
    if args.offset is not None:
        minutes = parse_offset_text(args.offset)
        return minutes, format_offset(minutes)
    name = args.from_country or DEFAULT_REFERENCE_COUNTRY
    country = find_country(countries, name)
    minutes = reference_offset_for(countries, country)
    return minutes, f"{country} ({format_offset(minutes)})"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Type a time and every time zone of every country follows it."
    )
    parser.add_argument("time", nargs="?", help="Time to apply, e.g. 20:00 or '8:00 PM'")
    parser.add_argument("--from", dest="from_country",
                        help=f"Country the typed time is in (default: {DEFAULT_REFERENCE_COUNTRY})")
    parser.add_argument("--offset", help="UTC offset the typed time is in, e.g. +3 or -5:30 (overrides --from)")
    parser.add_argument("--file", default=DEFAULT_FILE, help="Markdown file with the time zones")
    parser.add_argument("--country", nargs="+", help="Only show these countries")
    parser.add_argument("--output", help="Also save the results to this .md file")
    parser.add_argument("--live", action="store_true", help="Keep the clock running from the typed time")
    parser.add_argument("--ticks", type=int, help=argparse.SUPPRESS)  # for testing --live
    args = parser.parse_args()

    countries = scan_time_zones(args.file)
    zone_count = len({z for info in countries.values() for z in info["zones"]})
    print(f"Scanned {len(countries)} countries and found {zone_count} distinct UTC offsets.")

    try:
        reference_offset, reference_label = resolve_reference(countries, args)
    except ValueError as err:
        sys.exit(f"Error: {err}")
    print(f"Your time will be read as {reference_label}.\n")

    interactive = args.time is None
    while True:
        time_text = args.time or input("Enter a time (e.g. 20:00 or 8:00 PM; blank to quit): ").strip()
        if not time_text:
            break
        try:
            user_time = parse_user_time(time_text)
        except ValueError as err:
            if not interactive:
                sys.exit(f"Error: {err}")
            print(f"Error: {err}\n")
            continue

        if args.live:
            run_live(countries, user_time, reference_offset, args.country, args.ticks)
            break

        results = adjust_all_timezones(countries, user_time, reference_offset, args.country)
        if not results:
            sys.exit("No matching countries found. Check the spelling against the file.")

        print(f"\nIt is {user_time.strftime('%H:%M')} in {reference_label}. All time zones follow:\n")
        print_results(results)

        if args.output:
            save_markdown(results, countries, user_time, reference_label, args.output)

        if not interactive:
            break
        print()


if __name__ == "__main__":
    main()
