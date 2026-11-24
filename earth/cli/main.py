"""CLI backed exclusively by the shared EARTH engine."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from earth.core.conversion import compare_locations, convert_local_datetime
from earth.core.timezone import TimeZoneError, get_timezone, get_timezone_info
from earth.locations.resolver import resolve_location, search_locations

def _zone(value: str) -> str:
    return resolve_location(value).timezone

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="earth", description="Global Temporal Intelligence")
    sub = parser.add_subparsers(dest="command", required=True)
    clock = sub.add_parser("clock", help="Show current time in a location")
    clock.add_argument("--location", default="Africa/Kampala")
    convert = sub.add_parser("convert", help="Convert a local date/time")
    convert.add_argument("--from", dest="source", required=True)
    convert.add_argument("--to", dest="target", required=True)
    convert.add_argument("--datetime", required=True, help="YYYY-MM-DDTHH:MM[:SS]")
    convert.add_argument("--fold", type=int, choices=(0, 1))
    compare = sub.add_parser("compare", help="Compare an instant across locations")
    compare.add_argument("timezones", nargs="+")
    compare.add_argument("--at", help="ISO-8601 instant including UTC offset; defaults to now")
    location = sub.add_parser("location", help="Search locations")
    location.add_argument("action", choices=("search",))
    location.add_argument("query")
    location.add_argument("--limit", type=int, default=10)
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "clock":
            zone = _zone(args.location)
            now = datetime.now(timezone.utc).astimezone(get_timezone(zone))
            info = get_timezone_info(zone, now)
            result = {"location": args.location, "timezone": zone, "local_datetime": now.isoformat(), "utc_offset": info.utc_offset, "is_dst": info.is_dst}
        elif args.command == "convert":
            result = convert_local_datetime(datetime.fromisoformat(args.datetime), _zone(args.source), _zone(args.target), fold=args.fold).to_dict()
        elif args.command == "compare":
            instant = datetime.fromisoformat(args.at) if args.at else datetime.now(timezone.utc)
            result = compare_locations(instant, [_zone(item) for item in args.timezones])
        else:
            result = [item.__dict__ for item in search_locations(args.query, args.limit)]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, TimeZoneError) as exc:
        print(f"earth: error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
