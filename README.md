# Earth Time Zone Converter

`timezone_converter.py` is a small, dependency-free Python command-line tool
for comparing the local time in countries around the world. Enter a time in a
reference location and the tool calculates the corresponding time for every
standard time zone listed in [`countries-time-zones.md`](./countries-time-zones.md).

The default reference location is Uganda (`UTC+3`), but you can use another
single-zone country or provide a raw UTC offset.

## Requirements

- Python 3.10 or later

The script uses only Python's standard library. No package installation is
required.

## Quick start

Run the tool without a time to use interactive mode:

```text
python timezone_converter.py
```

Enter a time such as `20:00` or `8:00 PM`. Press Enter on a blank prompt to
quit.

To run it non-interactively:

```text
python timezone_converter.py 20:00
```

The command reports the time for each country and marks dates that fall on the
previous or next day.

## Usage

```text
python timezone_converter.py [TIME] [OPTIONS]
```

### Examples

Interpret `09:00` as the time in Japan:

```text
python timezone_converter.py 09:00 --from Japan
```

Interpret `14:30` as a time in UTC-5:

```text
python timezone_converter.py 14:30 --offset -5
```

Show only selected countries:

```text
python timezone_converter.py 20:00 --country Brazil Japan Australia
```

Keep the clock running from the entered time:

```text
python timezone_converter.py 20:00 --live
```

Save the calculated times as a Markdown table:

```text
python timezone_converter.py 20:00 --output result.md
```

Use a different time-zone data file:

```text
python timezone_converter.py 20:00 --file path/to/time-zones.md
```

### Options

| Option | Description |
|---|---|
| `TIME` | Optional time to apply. Interactive mode starts when omitted. |
| `--from COUNTRY` | Treat the entered time as the time in a single-zone country. Defaults to Uganda. |
| `--offset OFFSET` | Treat the entered time as a raw UTC offset, such as `+3`, `-5:30`, or `UTC+5:30`. Overrides `--from`. |
| `--country COUNTRY [...]` | Limit output to the named countries. |
| `--output FILE` | Write the results to a Markdown file as well as printing them. |
| `--live` | Update the displayed times every second. Stop with `Ctrl+C`. |
| `--file FILE` | Read country and offset data from another Markdown file. |

Country names are matched case-insensitively. A unique partial name is also
accepted. A country with multiple time zones cannot be used with `--from`;
use `--offset` when the reference country spans several zones.

## Accepted time formats

The converter accepts:

- `14:30`
- `14:30:00`
- `1430`
- `2:30 PM`
- `2 PM`
- `2026-10-28 14:30`
- `2026-10-28 14:30:00`

Times without a date use the current local date. UTC offsets may include
30-minute or 45-minute components, for example `+5:30` or `+5:45`.

## Data and assumptions

[`countries-time-zones.md`](./countries-time-zones.md) contains 195 countries:
the 193 UN member states and two UN observer states. It describes standard
UTC offsets rather than daylight-saving-time rules.

The converter calculates one shared UTC moment:

1. The entered clock time is interpreted in the selected reference offset.
2. That time is converted to UTC.
3. Each country's listed offset is applied to produce its local time.

Some countries have multiple zones. The script includes explicit standard-zone
overrides for Canada, Australia, the United States, Mexico, and Morocco because
their source-table ranges or seasonal notes need special handling. This is a
standard-offset comparison tool, not a daylight-saving-aware replacement for
the IANA time-zone database.

## Project files

| File | Purpose |
|---|---|
| [`timezone_converter.py`](./timezone_converter.py) | CLI, parsing, time calculations, live display, and Markdown export |
| [`countries-time-zones.md`](./countries-time-zones.md) | Country-to-standard-UTC-offset input data |
| [`countries (1).md`](./countries%20%281%29.md) | Country list reference |
| [`release_1.txt`](./release_1.txt) | Example interactive output |

## License

No license file is currently included in this project.