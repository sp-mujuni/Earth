# EARTH Temporal Model

## Principles
1. A time-zone identifier is an IANA identifier, not a manually maintained UTC offset.
2. A local wall-clock time is not always a unique instant. DST rollbacks can make it ambiguous; DST advances can make it nonexistent.
3. Convert between locations by identifying the source instant and rendering that instant in the destination zone.
4. Use aware datetimes for instants. Use naive datetimes only for user-entered wall-clock values before localization.
5. Never silently use the machine's local time zone as a reference.

## Ambiguous and nonexistent local times
The engine detects both cases by round-tripping candidate folds through UTC. Ambiguous values require fold=0 (earlier occurrence) or fold=1 (later occurrence). Nonexistent values raise NonexistentTimeError and are never silently shifted.

## Data coverage
The engine uses the IANA Time Zone Database through Python zoneinfo. On Windows, tzdata is installed as a fallback. Deployments should keep tzdata current because governments can change civil-time rules.

The initial location resolver is a curated starter city index plus direct IANA identifier validation. It is not yet a global geocoder or exhaustive city database.
