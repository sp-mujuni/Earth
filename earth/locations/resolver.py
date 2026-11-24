"""Curated starter city resolver plus direct IANA identifier support."""
from __future__ import annotations
from dataclasses import dataclass
from zoneinfo import available_timezones
from earth.core.timezone import TimeZoneError, get_timezone

class LocationNotFoundError(ValueError):
    """Location could not be resolved."""
@dataclass(frozen=True)
class Location:
    name: str
    country: str
    timezone: str
    latitude: float | None = None
    longitude: float | None = None

CITY_INDEX = {
    "kampala": Location("Kampala", "Uganda", "Africa/Kampala", .3476, 32.5825),
    "entebbe": Location("Entebbe", "Uganda", "Africa/Kampala", .0512, 32.4637),
    "nairobi": Location("Nairobi", "Kenya", "Africa/Nairobi", -1.2921, 36.8219),
    "lagos": Location("Lagos", "Nigeria", "Africa/Lagos", 6.5244, 3.3792),
    "cairo": Location("Cairo", "Egypt", "Africa/Cairo", 30.0444, 31.2357),
    "johannesburg": Location("Johannesburg", "South Africa", "Africa/Johannesburg", -26.2041, 28.0473),
    "london": Location("London", "United Kingdom", "Europe/London", 51.5072, -.1276),
    "paris": Location("Paris", "France", "Europe/Paris", 48.8566, 2.3522),
    "berlin": Location("Berlin", "Germany", "Europe/Berlin", 52.52, 13.405),
    "new york": Location("New York", "United States", "America/New_York", 40.7128, -74.006),
    "los angeles": Location("Los Angeles", "United States", "America/Los_Angeles", 34.0522, -118.2437),
    "chicago": Location("Chicago", "United States", "America/Chicago", 41.8781, -87.6298),
    "toronto": Location("Toronto", "Canada", "America/Toronto", 43.6532, -79.3832),
    "mexico city": Location("Mexico City", "Mexico", "America/Mexico_City", 19.4326, -99.1332),
    "sao paulo": Location("São Paulo", "Brazil", "America/Sao_Paulo", -23.5505, -46.6333),
    "tokyo": Location("Tokyo", "Japan", "Asia/Tokyo", 35.6762, 139.6503),
    "singapore": Location("Singapore", "Singapore", "Asia/Singapore", 1.3521, 103.8198),
    "kolkata": Location("Kolkata", "India", "Asia/Kolkata", 22.5726, 88.3639),
    "kathmandu": Location("Kathmandu", "Nepal", "Asia/Kathmandu", 27.7172, 85.324),
    "sydney": Location("Sydney", "Australia", "Australia/Sydney", -33.8688, 151.2093),
    "auckland": Location("Auckland", "New Zealand", "Pacific/Auckland", -36.8509, 174.7645),
    "chatham islands": Location("Chatham Islands", "New Zealand", "Pacific/Chatham", -43.9535, -176.5597),
    "honolulu": Location("Honolulu", "United States", "Pacific/Honolulu", 21.3099, -157.8581),
}
def resolve_location(query: str) -> Location:
    key = query.strip().casefold()
    if key in CITY_INDEX:
        return CITY_INDEX[key]
    try:
        get_timezone(query)
    except TimeZoneError as exc:
        raise LocationNotFoundError(f"Could not resolve '{query}'. Try an indexed city or an IANA identifier.") from exc
    return Location(query, "Unknown", query)

def search_locations(query: str, limit: int = 10) -> list[Location]:
    if limit < 1:
        raise ValueError("limit must be at least 1.")
    key = query.strip().casefold()
    if not key:
        raise ValueError("Search query cannot be empty.")
    cities = [loc for name, loc in CITY_INDEX.items() if key in name]
    zones = [Location(zone, "Unknown", zone) for zone in sorted(available_timezones()) if key in zone.casefold()]
    seen = {loc.timezone for loc in cities}
    return (cities + [loc for loc in zones if loc.timezone not in seen])[:limit]
